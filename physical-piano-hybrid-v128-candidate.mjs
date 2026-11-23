import {PianoResonanceBody} from './piano-resonance.js';
import {hybridRadiationGain} from './piano-hybrid-calibration.js';

/**
 * Stage D — original hybrid modal piano prototype (research-informed, NOT measured/calibrated).
 *
 * One shared soundboard + sympathetic-string model, per-note inharmonic modes,
 * unequal fast/slow unison decays, a velocity-dependent felt contact spectrum,
 * spatial key projection and short key/hammer noise. No samples or external code.
 * No allocation in render(): designed for AudioWorklet and deterministic Node tests.
 * The 32/48/64 figures are VOICE ALLOCATION caps, not real-time CPU certification.
 */
export const HYBRID_QUALITY = Object.freeze({
  eco: Object.freeze({voices:32,partials:12,paired:3,bodyDivisor:6}),
  balanced: Object.freeze({voices:48,partials:17,paired:4,bodyDivisor:4}),
  studio: Object.freeze({voices:64,partials:23,paired:5,bodyDivisor:4})
});
const SRATE = 48000, TWO_PI = 2*Math.PI, MAX_VOICES = 64, MAX_MODES = 32;
const MAX_BLOCK = 128, MAX_HAMMER_SAMPLES=512, T60_DB = 6.907755278982137;
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const midiHz=k=>440*2**((k-69)/12);
/**
 * Magnitude of the *normalized* raised-cosine contact pulse's discrete Fourier
 * transform. Closed-form Dirichlet sums are O(1) per mode vs O(contactSamples).
 * The pulse is a compressed half-sine squared (F ∝ compression²): a simple
 * nonlinear compression model, NOT measured felt law or Hammer F(t).
 */
function dirichletSum(n,x){
  const half=x*.5,s=Math.sin(half);
  return Math.abs(s)<1e-8?n:Math.sin(n*half)/s;
}
export function bassContactTransferMagnitude(n,w){
  if(!Number.isInteger(n)||n<16||n>MAX_HAMMER_SAMPLES||
      !Number.isFinite(w)||w<0||w>Math.PI)throw new RangeError('invalid contact spectrum');
  const d=TWO_PI/n;
  return Math.abs(dirichletSum(n,w)+.5*dirichletSum(n,w+d)+.5*dirichletSum(n,w-d))/n;
}
const CHARACTER=Object.freeze({
  // Inspired by qualitative differences, not measured Yamaha/Steinway constants.
  japanese:{tone:1.10,body:1.05,decay:1.04,detune:.9,contact:.92,noise:.84,radiation:.75},
  american:{tone:.88,body:1.08,decay:1.13,detune:.86,contact:1.10,noise:.77,radiation:1},
  felt:{tone:.41,body:.82,decay:.83,detune:.72,contact:2.0,noise:.37,radiation:.20},
  upright:{tone:.79,body:.90,decay:.75,detune:1.65,contact:1.14,noise:1.12,radiation:.52}
});

export function hybridInharmonicity(key) {
  if (!Number.isFinite(key))return .0001;
  // U-shaped empirical *approximation* across the compass, not a Steinway fit.
  const low=Math.max(0,48-key)/27,high=Math.max(0,key-58)/50;
  return clamp(.000085+.00027*low*low+.0020*high**3,5e-5,.018);
}
export function hybridContactTime(key,speed,hardness,character='american'){
  const cfg=CHARACTER[character]||CHARACTER.american;
  const normalized=clamp(speed,.04,1),hard=clamp(hardness,0,1);
  const t=(.0010+.0020*(1-hard))*normalized**(-.24)*cfg.contact;
  const maxContact=Math.min(.012,1.0/midiHz(key));
  return clamp(t,Math.min(.00011,maxContact),maxContact);
}

class Voice {
  constructor(){
    this.y1=new Float64Array(MAX_MODES);this.y2=new Float64Array(MAX_MODES);
    this.c=new Float64Array(MAX_MODES);this.r2=new Float64Array(MAX_MODES);
    // Preallocate contact force and per-mode driving coefficients (bass only).
    this.force=new Float64Array(MAX_HAMMER_SAMPLES);
    this.drive=new Float64Array(MAX_MODES);
    this.forceCount=0;this.forceIndex=0;
    this.tmp=new Float32Array(MAX_BLOCK);
    this.active=false;this.released=false;this.damped=false;
    this.id=0;this.key=60;this.age=0;this.count=0;this.silent=0;this.lastPeak=0;
    this.gl=1;this.gr=1;this.level=0;this.send=.1;this.sendTarget=.1;
    this.attack=0;this.attackStep=.02;this.noise=0;this.noiseDecay=1;this.noiseLP=0;
    this.impact=0;this.impactDecay=1;this.character='american';
    this.decayScale=1;this.brightness=.5;this.releaseTime=.4;
  }
}
export class HybridPianoEngine {
  constructor(sampleRate=SRATE,quality='eco'){
    if(!Number.isFinite(sampleRate)||sampleRate<22050)throw new RangeError('sampleRate must be >= 22050');
    this.sr=sampleRate;
    this.voices=Array.from({length:MAX_VOICES},()=>new Voice());
    this.done=[];this.seed=0x736f6e67;this.mixGain=1;this.pedal=0;
    this.keys=new Uint8Array(88);
    this.body=new PianoResonanceBody({sampleRate,divisor:4,sympathetic:.20,body:.26,mechanical:.12,bridgeLoad:.12});
    this.setQuality(quality);
  }
  setQuality(quality){
    const q=HYBRID_QUALITY[quality]||HYBRID_QUALITY.eco;
    const old=this.quality;
    this.quality=quality in HYBRID_QUALITY?quality:'eco';
    this.maxVoices=q.voices;this.maxPartials=q.partials;this.paired=q.paired;
    if(old&&old!==this.quality){
      for(let i=this.maxVoices;i<this.voices.length;i++)if(this.voices[i].active)this.kill(this.voices[i]);
    }
    // Body divisor is intentionally fixed on existing states; no live DSP reset.
  }
  random(){
    let x=this.seed;x^=x<<13;x^=x>>>17;x^=x<<5;this.seed=x;
    return (x>>>0)/2147483648-1;
  }
  find(id){for(const v of this.voices)if(v.active&&v.id===id)return v;return null}
  kill(v){
    if(!v.active)return;
    if(!v.released)this.keyUp(v.key);
    v.active=false;v.count=0;v.forceCount=0;v.forceIndex=0;this.done.push(v.id);
  }
  keyDown(key,speed){
    const idx=key-21;if(idx<0||idx>=88)return;
    if(this.keys[idx]<255)this.keys[idx]++;
    this.body.noteOn(key,clamp(Math.round(speed*127),1,127));
  }
  keyUp(key){
    const idx=key-21;if(idx<0||idx>=88)return;
    if(this.keys[idx])this.keys[idx]--;
    if(!this.keys[idx])this.body.noteOff(key);
  }
  acquire(){
    for(let i=0;i<this.maxVoices;i++)if(!this.voices[i].active)return this.voices[i];
    let chosen=this.voices[0],score=-Infinity;
    for(let i=0;i<this.maxVoices;i++){
      const v=this.voices[i],s=v.age+(v.released?100:0);
      if(s>score){score=s;chosen=v}
    }
    this.kill(chosen);return chosen;
  }
  /**
   * Finite causal contact pulse (a Hertz-inspired compressed half-sine, NOT
   * physically measured hammer force). Both peak and pulse width depend on
   * MIDI speed and felt hardness. Normalized area makes the impulse energy
   * explicit; high-frequency suppression comes from its Fourier transform.
   */
  prepareBassContact(v,seconds){
    const n=clamp(Math.round(seconds*this.sr),16,MAX_HAMMER_SAMPLES);
    // A positive raised-cosine pressure envelope, normalized to unit area.
    // Recurrence avoids one transcendental call per force sample on note-on.
    // Hardness and MIDI velocity affect duration through hybridContactTime.
    const phase=TWO_PI/n,cw=Math.cos(phase),sw=Math.sin(phase);
    let c=Math.cos(phase*.5),sn=Math.sin(phase*.5);
    for(let i=0;i<n;i++){
      v.force[i]=Math.max(0,(1-c)/n);
      const nextC=c*cw-sn*sw;sn=sn*cw+c*sw;c=nextC;
    }
    v.forceCount=n;v.forceIndex=0;
  }
  addMode(v,mode,f,t60,amp,phase){
    if(mode>=MAX_MODES)return mode;
    const w=TWO_PI*f/this.sr,r=Math.exp(-T60_DB/(Math.max(.08,t60)*this.sr));
    v.c[mode]=2*r*Math.cos(w);v.r2[mode]=r*r;
    if(v.forceCount){
      // Response of this second-order resonator to one finite force pulse.
      // Match its *post-contact modal amplitude* to the measured spectral
      // target, rather than injecting an arbitrary global noise/thump.
      // Phase is produced by propagation and the hammer-force waveform.
      const response=Math.max(.045,bassContactTransferMagnitude(v.forceCount,w));
      v.drive[mode]=amp*Math.abs(Math.sin(w))/response;
      v.y1[mode]=0;v.y2[mode]=0;
    }else{
      v.drive[mode]=0;
      v.y1[mode]=amp*Math.sin(phase);
      v.y2[mode]=amp*Math.sin(phase-w)/r;
    }
    return mode+1;
  }
  noteOn({id,key,speed=.6,hardness=.5,send=.12,character='american',
          decayScale=1,brightness=.5}={}){
    if(!Number.isFinite(id)||!Number.isFinite(key))return;
    key=clamp(Math.round(key),21,108);
    speed=clamp(Number.isFinite(speed)?speed:.6,.001,1);
    hardness=clamp(Number.isFinite(hardness)?hardness:.5,0,1);
    brightness=clamp(Number.isFinite(brightness)?brightness:.5,0,1);
    const profile=CHARACTER[character]||CHARACTER.american;
    const v=this.acquire(),f0=midiHz(key),B=hybridInharmonicity(key);
    const t=hybridContactTime(key,speed,hardness,character);
    const beta=.13-.04*(key-21)/87;
    const tone=clamp((.24+.7*brightness+.42*hardness)*profile.tone,.15,1.8);
    const baseT60=16*2**(-(key-21)/39)*profile.decay*clamp(decayScale,.35,1.7);
    // Acoustic construction: single-string lowest bass, bichord in upper bass.
    // A0..E1 remain monochord; F1 and above may use unison modes.
    // The exact crossover varies by instrument; this is a Stage B-like
    // register approximation, not measured string count per specific piano.
    const single=key<29,nyquist=this.sr*.44;
    // Only the bass gets the candidate physical contact experiment.
    // C4–C6 are guaranteed to keep the original oscillator path.
    if(key<=48)this.prepareBassContact(v,t);
    else {v.forceCount=0;v.forceIndex=0;}
    let count=0,power=0;
    // Save normalized partial weights locally in voice state; no unlicensed tables.
    for(let n=1;n<=this.maxPartials;n++){
      const f=n*f0*Math.sqrt((1+B*n*n)/(1+B));if(f>=nyquist)break;
      const omega=TWO_PI*f,ct=omega*t*.27;
      const contact=1/(1+ct*ct);
      const strike=Math.sin(Math.PI*n*beta)/Math.sin(Math.PI*beta);
      // A finite-width, causal hammer excitation + the strike position's comb.
      // Coupled unison double-decay is below, not a global chorus.
      const tilt=Math.exp(-.35*(f/3500)**1.16/tone);
      let a=strike*contact*tilt/n**1.12;
      if(n>1)a*=.65+.55*speed**.55;
      // Piano sound is not raw string displacement: bridge/body/microphones
      // radiate frequency-dependent modes. Apply a BOUNDED effective
      // excitation/radiation transfer at each note-on, before energy
      // normalization. Steinway B is the only measured acoustic anchor;
      // other characters receive weaker cross-instrument extrapolation.
      a*=hybridRadiationGain(key,speed,n)**profile.radiation;
      const phase=-2*Math.atan(ct)+.08*n;
      const decay=baseT60/(1+.052*n*n+.08*f/1000);
      if(n<=this.paired&&!single&&count+2<=MAX_MODES){
        const cents=(.25+.55*(n/this.paired)+.23*((key*7+n*3)%5)/5)*profile.detune;
        count=this.addMode(v,count,f,decay*.40,a*.63,phase);
        count=this.addMode(v,count,f*2**(cents/1200),decay*1.65,a*.37,phase+.16);
      }else count=this.addMode(v,count,f,decay,a,phase);
      power+=a*a;
    }
    const normalized=.056*speed**1.35*(.72+.45*brightness)*profile.body/
      Math.sqrt(Math.max(1e-8,power));
    for(let i=0;i<count;i++){
      v.y1[i]*=normalized;v.y2[i]*=normalized;
      // Bass drive starts from zero displacement, so normalize drive too.
      if(v.forceCount)v.drive[i]*=normalized;
    }
    v.id=id;v.key=key;v.active=true;v.released=false;v.damped=false;
    v.count=count;v.age=0;v.silent=0;v.lastPeak=0;v.send=clamp(send,0,1);v.sendTarget=v.send;
    // A bridge/soundboard does not radiate every modal component instantly.
    // Limit the candidate ONLY to bass; preserve the original higher-note
    // attack byte-for-byte. This is a bounded temporal transmission proxy,
    // not a measured hammer-to-bridge transfer function.
    v.attack=0;
    // The bass bridge build-up is register dependent: too long a delay
    // suppresses the first-cycle energy in low C2, while too short a delay
    // exaggerates the attack near C3. These are exploratory timings, not
    // instrument-measured radiation delays.
    const bassRise=.0048+.0018*clamp((key-24)/24,0,1)+.001*(1-speed);
    const attackSeconds=v.forceCount ? bassRise
      :(.0012+.0030*(1-key/120)*(1-speed*.5));
    v.attackStep=1/(this.sr*attackSeconds);
    const pan=clamp((key-64.5)/43.5,-1,1)*.30;
    v.gl=Math.sqrt(1-pan);v.gr=Math.sqrt(1+pan);
    v.noise=.037*speed**2.4*(.35+.65*hardness)*profile.noise;
    v.noiseDecay=Math.exp(-1/(this.sr*(.0028+.0018*(1-speed))));
    // Bass: the force pulse is the mechanical strike; do not add the old
    // one-sided exponential thump on top of it.
    v.noiseLP=0;v.impact=v.forceCount?0:.014*speed**2*profile.body;
    v.impactDecay=Math.exp(-1/(this.sr*.017));
    v.character=character;v.decayScale=decayScale;v.brightness=brightness;
    v.releaseTime=.38;
    this.keyDown(key,speed);
  }
  damp(v,fast=false,release=.4){
    if(v.damped)return;
    const seconds=fast?.025:clamp(release,.025,3);
    const g=Math.exp(-T60_DB/(seconds*this.sr));
    for(let i=0;i<v.count;i++){v.c[i]*=g;v.r2[i]*=g*g}
    v.damped=true;
  }
  noteOff(id,fast=false,release=.4){
    const v=this.find(id);if(!v||v.released)return;
    v.released=true;v.releaseTime=release;this.keyUp(v.key);
    if(fast||this.pedal<.5||v.key>=89)this.damp(v,fast,release);
  }
  setSustain(value){
    const prior=this.pedal;this.pedal=clamp(Number.isFinite(value)?value:0,0,127)/127;
    this.body.setSustain(value);
    if(prior>=.5&&this.pedal<.5){
      for(const v of this.voices)if(v.active&&v.released&&!v.damped)this.damp(v,false,v.releaseTime);
    }
  }
  setSend(id,x){const v=this.find(id);if(v)v.sendTarget=clamp(x,0,1)}
  updateVoice(id,{decayScale,brightness,damping,send,release}={}){
    const v=this.find(id);if(!v)return;
    if(Number.isFinite(send))v.sendTarget=clamp(send,0,1);
    if(Number.isFinite(release))v.releaseTime=clamp(release,.025,3);
    if(Number.isFinite(brightness))v.brightness=clamp(brightness,0,1);
    if(Number.isFinite(decayScale)&&!v.released){
      const next=clamp(decayScale,.35,1.7),ratio=v.decayScale/next;
      for(let i=0;i<v.count;i++){
        const old=Math.sqrt(v.r2[i]);
        const newR=old**ratio;
        if(old>0){v.c[i]*=newR/old;v.r2[i]=newR*newR}
      }
      v.decayScale=next;
    }
    if(Number.isFinite(damping)&&v.released&&this.pedal<.5)this.damp(v,false,v.releaseTime);
  }
  stopAll(){
    this.setSustain(0);
    for(const v of this.voices)if(v.active){
      if(!v.released){v.released=true;this.keyUp(v.key)}
      this.damp(v,true,.025);
    }
    this.body.allKeysUp();this.keys.fill(0);
  }
  render(L,R,S=null,n=L.length){
    if(n>MAX_BLOCK||n<0)throw new RangeError('hybrid render supports <=128 samples/block');
    L.fill(0,0,n);if(R!==L)R.fill(0,0,n);if(S)S.fill(0,0,n);
    const stereo=L!==R;
    let active=0;
    for(let k=0;k<this.maxVoices;k++)if(this.voices[k].active){
      const v=this.voices[k];active++;
      const tmp=v.tmp;tmp.fill(0,0,n);
      const driveStart=v.forceIndex;
      const driving=driveStart<v.forceCount;
      for(let m=0;m<v.count;m++){
        const c=v.c[m],r2=v.r2[m];
        let a=v.y1[m],b=v.y2[m];
        if(driving){
          const forceGain=v.drive[m],force=v.force,limit=v.forceCount;
          for(let i=0;i<n;i++){
            const d=driveStart+i<limit?force[driveStart+i]*forceGain:0;
            const next=c*a-r2*b+d; b=a;a=next;tmp[i]+=next;
          }
        }else{
          for(let i=0;i<n;i++){
            const next=c*a-r2*b; b=a;a=next;tmp[i]+=next;
          }
        }
        v.y1[m]=a;v.y2[m]=b;
      }
      if(driving)v.forceIndex=Math.min(v.forceCount,driveStart+n);
      let env=v.attack,noise=v.noise,impact=v.impact,lp=v.noiseLP,peak=0;
      let send=v.send;
      for(let i=0;i<n;i++){
        env=Math.min(1,env+v.attackStep);
        // Causal hammer attack: independent mechanical thump and broadband strike.
        lp+=.21*(this.random()-lp);
        const mechanical=lp*noise+impact;
        const x=tmp[i]*env+mechanical;
        peak=Math.max(peak,Math.abs(x));
        L[i]+=x*v.gl;
        if(stereo)R[i]+=x*v.gr;
        if(S)S[i]+=x*send;
        noise*=v.noiseDecay;impact*=v.impactDecay;
        send+=(v.sendTarget-send)*.001;
      }
      v.noise=noise;v.impact=impact;v.noiseLP=lp;v.attack=env;v.send=send;
      v.lastPeak=peak;v.age+=n/this.sr;
      if(v.released&&v.damped&&peak<.000012)v.silent++;else v.silent=0;
      if(v.silent>12||v.age>55)this.kill(v);
    }
    const target=1/Math.sqrt(Math.max(1,active/5));
    for(let i=0;i<n;i++){
      this.mixGain+=(target-this.mixGain)*(target<this.mixGain?.028:.0008);
      const dryL=L[i],dryR=stereo?R[i]:dryL;
      this.body.step(dryL*.65,dryR*.65);
      // All resonance is shared; never route through a second piano Convolver.
      const x=(dryL+this.body.wetL*.48)*this.mixGain;
      const y=(dryR+this.body.wetR*.48)*this.mixGain;
      // Gentle safety curve, not a loudness-maximizing hard limiter.
      L[i]=.96*Math.tanh(x/.96);
      if(stereo)R[i]=.96*Math.tanh(y/.96);
      if(S)S[i]*=this.mixGain*.30;
    }
  }
}

if(typeof registerProcessor==='function'){
  registerProcessor('palco-piano-hybrid',class extends AudioWorkletProcessor {
    constructor(){
      super();
      this.engine=new HybridPianoEngine(sampleRate,'eco');
      this.port.onmessage=({data:m})=>{
        if(m.type==='on')this.engine.noteOn(m);
        else if(m.type==='off')this.engine.noteOff(m.id,m.fast,m.release);
        else if(m.type==='send')this.engine.setSend(m.id,m.value);
        else if(m.type==='param')this.engine.updateVoice(m.id,m);
        else if(m.type==='quality')this.engine.setQuality(m.quality);
        else if(m.type==='pedal')this.engine.setSustain(m.value);
        else if(m.type==='stop')this.engine.stopAll();
      };
    }
    process(_inputs,outputs){
      const [dry,aux]=outputs;
      this.engine.render(dry[0],dry[1]||dry[0],aux?.[0],dry[0].length);
      if(this.engine.done.length)this.port.postMessage({type:'done',ids:this.engine.done.splice(0)});
      return true;
    }
  });
}
