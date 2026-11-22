/*
 * Stage Synth — Physical Piano Core v0.2 (original DSP, no samples).
 * Lightweight hammered-string waveguide + a shared resonant soundboard.
 * The core is platform-independent JavaScript: it can render in Node or AudioWorklet.
 * This is a perceptual/physically informed model, not a calibrated acoustic piano.
 * All ring buffers and voices are preallocated. render() performs no heap allocations.
 * Reference: J. O. Smith, Physical Audio Signal Processing (digital waveguides).
 */
export const PHYSICAL_PRESETS=Object.freeze({
  eco: {voices:8, strings:1, boardModes:3},
  balanced: {voices:16,strings:2,boardModes:5},
  studio: {voices:24,strings:2,boardModes:7}
});
const TWOPI=2*Math.PI;
const MAX_DELAY=8192; // supports A0 at 48/44.1 kHz and even extended bass notes
const SILENCE=0.000025;
const clamp=(x,lo,hi)=>Math.min(hi,Math.max(lo,x));
export const midiHz=key=>440*2**((key-69)/12);
const profiles={
  japanese:{stiff:0.30,bright:0.89,body:1.00,decay:1.00,detune:1.10,position:.135},
  american:{stiff:0.23,bright:0.77,body:1.08,decay:1.13,detune:.84,position:.122},
  felt:{stiff:0.18,bright:.30,body:.82,decay:.88,detune:.65,position:.148},
  upright:{stiff:.38,bright:.67,body:.90,decay:.84,detune:1.65,position:.153}
};
const BOARD=[[87,.18],[134,.13],[198,.11],[279,.090],[398,.078],[590,.060],[876,.045]];

class StringVoice {
  constructor(){
    this.lineA=new Float32Array(MAX_DELAY);
    this.lineB=new Float32Array(MAX_DELAY);
    this.active=false;this.id=0;this.key=60;this.write=0;
    this.age=0;this.release=false;this.energy=0;this.quiet=0;
    this.periodA=80;this.periodB=80;this.intPeriodA=80;this.intPeriodB=80;
    this.fracCoeffA=0;this.fracCoeffB=0;this.fracXA=0;this.fracYA=0;this.fracXB=0;this.fracYB=0;this.freq=440;
    this.lpA=0;this.lpB=0;this.apXA=0;this.apYA=0;this.apXB=0;this.apYB=0;
    this.apCoeff=-.22;this.lpSpeed=.72;this.loopGain=.997;this.loopTarget=.997;
    this.left=.7;this.right=.7;this.level=.1;this.levelTarget=.1;
    this.resonance=.08;this.send=.08;this.sendTarget=.08;
    this.attack=0;this.attackStep=1;this.releaseTime=.45;this.fade=0;
    this.character='japanese';this.hammerNoise=0;this.noiseState=0;
  }
}
export class PhysicalPianoEngine {
  constructor(sr=48000,quality='eco'){
    this.sr=sr;this.voices=Array.from({length:PHYSICAL_PRESETS.studio.voices},()=>new StringVoice());
    this.mode='eco';this.maxVoices=8;this.stringCount=1;this.boardModes=3;
    this.setQuality(quality);
    this.counter=0;this.done=[];this.doneCount=0;this.seed=0x18ca6c9f;
    this.boardY1=new Float64Array(BOARD.length);this.boardY2=new Float64Array(BOARD.length);
    this.boardA=new Float64Array(BOARD.length);this.boardR2=new Float64Array(BOARD.length);
    this.boardInput=new Float64Array(BOARD.length);
    for(let k=0;k<BOARD.length;k++){
      const [f,t]=BOARD[k],r=Math.exp(-1/(this.sr*t));
      this.boardA[k]=2*r*Math.cos(TWOPI*f/this.sr);
      this.boardR2[k]=r*r;
      this.boardInput[k]=(.0035/(1+k*.3))*(1-r);
    }
  }
  setQuality(mode){
    const m=PHYSICAL_PRESETS[mode]||PHYSICAL_PRESETS.eco;
    this.mode=PHYSICAL_PRESETS[mode]?mode:'eco';
    this.maxVoices=m.voices;this.stringCount=m.strings;this.boardModes=m.boardModes;
    // If lowering polyphony, release excess voices safely.
    for(let i=this.maxVoices;i<this.voices.length;i++)if(this.voices[i].active)this.kill(this.voices[i]);
  }
  random(){let x=this.seed;x^=x<<13;x^=x>>>17;x^=x<<5;this.seed=x;return (x>>>0)/2147483648-1}
  find(id){for(let i=0;i<this.voices.length;i++){const v=this.voices[i];if(v.active&&v.id===id)return v;}return null;}
  kill(v){if(v.active){v.active=false;v.lineA.fill(0);v.lineB.fill(0);this.done.push(v.id);}}
  acquire(){
    let candidate=null,score=-Infinity;
    for(let i=0;i<this.maxVoices;i++){
      const v=this.voices[i];if(!v.active)return v;
      const s=v.age+(v.release?300:0)+(v.energy<SILENCE?100:0);
      if(s>score){score=s;candidate=v;}
    }
    this.kill(candidate);
    return candidate;
  }
  // Period-compensated waveguide with a first-order dispersive allpass boundary.
  // Physical stiff-string inharmonicity needs more sections for the high treble;
  // this single section deliberately sacrifices that accuracy to cut mobile CPU.
  setupPeriod(freq,stiff,lpSpeed){
    const a=-clamp(stiff,.05,.46);
    // Exact phase-delay compensation at the fundamental, rather than a
    // DC approximation. This is essential above the middle of the keyboard.
    const omega=TWOPI*freq/this.sr;
    const k=(1-a)/(1+a),half=omega*.5;
    const apPhase=2*Math.atan2(k*Math.sin(half),Math.cos(half));
    const pole=1-lpSpeed;
    const lpPhase=Math.atan2(pole*Math.sin(omega),1-pole*Math.cos(omega));
    const period=clamp(this.sr/freq-(apPhase+lpPhase)/omega,3.5,MAX_DELAY-4);
    const integer=Math.floor(period),fraction=period-integer;
    return {period,integer,fracCoeff:(1-fraction)/(1+fraction),coeff:a};
  }
  // Triangular displacement at the hammer position. A brief localized impulse
  // models the harder felt's higher-frequency excitation without audio samples.
  seedString(line,period,position,level,hardness,variation){
    line.fill(0);
    const count=Math.ceil(period)+3;
    const readStart=MAX_DELAY-period;
    let mean=0;
    for(let k=0;k<count;k++){
      const phi=(k/period)%1;
      const triangle=phi<position?phi/position:(1-phi)/(1-position);
      const distance=Math.abs(phi-position);
      const width=.009+.08*(1-hardness);
      const compression=Math.max(0,1-distance/(width*1.7));
      // Felt contact F=K*compression^3: a cheap nonlinear approximation of hammer force.
      const localized=hardness*.52*compression*compression*compression;
      const val=(triangle-.5+localized)*level*(1+variation);
      line[(Math.floor(readStart+k)+MAX_DELAY)%MAX_DELAY]=val;
      mean+=val;
    }
    // A near-zero-mean wave avoids a sustained DC offset in the feedback loop.
    const correction=mean/count;
    for(let k=0;k<count;k++){
      const idx=(Math.floor(readStart+k)+MAX_DELAY)%MAX_DELAY;
      line[idx]-=correction;
    }
  }
  noteOn({id,key=60,speed=.7,hardness=.5,character='japanese',brightness=.5,decayScale=1,send=.06}){
    key=clamp(Math.round(key),21,108);speed=clamp(speed,.001,1);hardness=clamp(hardness,0,1);
    const cfg=profiles[character]||profiles.japanese;
    const freq=midiHz(key),v=this.acquire();
    const stiffness=cfg.stiff*(.60+.6*(key/108));
    const contactHard=clamp((hardness*.65+speed*.35)*cfg.bright,0,1);
    const speedLP=clamp(.67+.24*clamp((key-64)/40,0,1)-.15*contactHard,.43,.93);
    const tuned=this.setupPeriod(freq,stiffness,speedLP);
    const detuneCents=key<38?.14:cfg.detune*(.6+.4*key/108);
    const freqB=freq*2**(detuneCents/1200);
    const tunedB=this.setupPeriod(freqB,stiffness,speedLP);
    const touch=speed**1.35;
    const excitation=.34*touch*cfg.body*(.68+.32*clamp(brightness,0,1));
    const tension=clamp((key-21)/87,0,1);
    const position=cfg.position-.015*tension;
    this.seedString(v.lineA,tuned.period,position,excitation,contactHard,0);
    if(this.stringCount>1)this.seedString(v.lineB,tunedB.period,position,excitation*.84,contactHard*.94,-.005);
    else v.lineB.fill(0);
    v.id=id;v.key=key;v.freq=freq;v.character=character;v.active=true;v.release=false;
    v.periodA=tuned.period;v.periodB=tunedB.period;v.intPeriodA=tuned.integer;v.intPeriodB=tunedB.integer;
    v.fracCoeffA=tuned.fracCoeff;v.fracCoeffB=tunedB.fracCoeff;v.apCoeff=tuned.coeff;
    v.write=0;v.age=0;v.quiet=0;v.energy=excitation;v.fade=0;
    v.lpA=0;v.lpB=0;v.apXA=0;v.apYA=0;v.apXB=0;v.apYB=0;
    v.fracXA=0;v.fracYA=0;v.fracXB=0;v.fracYB=0;
    v.lpSpeed=speedLP;
    const sustainSec=(21.5*2**(-(key-21)/34))*cfg.decay*clamp(decayScale,.35,2);
    v.loopGain=Math.exp(-6.91/(freq*sustainSec));v.loopTarget=v.loopGain;
    v.releaseTime=.42;
    const pos=clamp((key-65)/45,-1,1),ang=Math.PI/4+pos*.30;
    v.left=Math.cos(ang)*1.13;v.right=Math.sin(ang)*1.13;
    v.level=1;v.levelTarget=1;v.send=v.sendTarget=clamp(send,0,1);
    v.hammerNoise=0.004*speed**2*contactHard;v.noiseState=0;
  }
  noteOff(id,fast=false,release=.4){
    const v=this.find(id);if(!v)return;
    v.release=true;v.releaseTime=fast?.018:clamp(release,.025,3);
    v.loopTarget=Math.exp(-6.91/(v.freq*v.releaseTime));
    if(fast)v.levelTarget=0;
  }
  setSend(id,x){const v=this.find(id);if(v)v.sendTarget=clamp(x,0,1)}
  updateVoice(id,{decayScale,brightness,damping,send,release}={}){
    const v=this.find(id);if(!v)return;
    if(Number.isFinite(send))v.sendTarget=clamp(send,0,1);
    if(Number.isFinite(release))v.releaseTime=clamp(release,.025,3);
    if(Number.isFinite(brightness))v.lpSpeed=clamp(.72-.45*brightness,.18,.80);
    if(Number.isFinite(damping)&&!v.release){
      const cfg=profiles[v.character]||profiles.japanese;
      const sustainSec=(21.5*2**(-(v.key-21)/34))*cfg.decay*clamp(decayScale||1,.35,2)*clamp(1.4-damping,.38,1.6);
      v.loopTarget=Math.exp(-6.91/(v.freq*sustainSec));
    }
  }
  stopAll(){for(let i=0;i<this.voices.length;i++){const v=this.voices[i];if(v.active)this.noteOff(v.id,true,.018)}}
  // One sample from a fractional-delay dispersive string; no temporary arrays.
  tickString(v,which){
    const line=which? v.lineB:v.lineA;
    const period=which?v.intPeriodB:v.intPeriodA;
    let idx=v.write-period;if(idx<0)idx+=MAX_DELAY;
    const raw=line[idx];
    // First-order allpass fractional delay has unit magnitude, unlike linear
    // interpolation which noticeably damps high notes every feedback cycle.
    const h=which?v.fracCoeffB:v.fracCoeffA;
    const prevIn=which?v.fracXB:v.fracXA,prevOut=which?v.fracYB:v.fracYA;
    const fractional=h*raw+prevIn-h*prevOut;
    if(which){v.fracXB=raw;v.fracYB=fractional}
    else {v.fracXA=raw;v.fracYA=fractional}
    const pole=v.lpSpeed,prior=which?v.lpB:v.lpA;
    const filtered=prior+(fractional-prior)*pole;
    const a=v.apCoeff,oldIn=which?v.apXB:v.apXA,oldOut=which?v.apYB:v.apYA;
    const dispersed=a*filtered+oldIn-a*oldOut;
    line[v.write]=dispersed*v.loopGain;
    if(which){v.lpB=filtered;v.apXB=filtered;v.apYB=dispersed}
    else {v.lpA=filtered;v.apXA=filtered;v.apYA=dispersed}
    return fractional;
  }
  // Additive shared board modes approximate wood resonances with only 3–7
  // second-order filters per output sample, rather than convolvers per voice.
  render(L,R,S,n=L.length){
    const stereo=L!==R;
    L.fill(0,0,n);if(stereo)R.fill(0,0,n);if(S)S.fill(0,0,n);
    for(let i=0;i<n;i++){
      let dryL=0,dryR=0,send=0,boardIn=0;
      for(let j=0;j<this.maxVoices;j++){
        const v=this.voices[j];if(!v.active)continue;
        v.loopGain+=(v.loopTarget-v.loopGain)*.0035;
        v.level+=(v.levelTarget-v.level)*.007;
        v.send+=(v.sendTarget-v.send)*.002;
        const x1=this.tickString(v,false);
        const x2=this.stringCount>1?this.tickString(v,true):0;
        v.write++;if(v.write===MAX_DELAY)v.write=0;
        let x=(x1+(this.stringCount>1?x2*.78:0))*(this.stringCount>1?.57:1);
        // The strike transient is physical excitation + a short hammer-noise term.
        if(v.hammerNoise>1e-6){
          v.noiseState+=(this.random()-v.noiseState)*.26;
          x+=v.hammerNoise*v.noiseState;
          v.hammerNoise*=.9978;
        }
        if(v.fade<64){x*=v.fade/64;v.fade++}
        x*=v.level;
        dryL+=x*v.left;dryR+=x*v.right;boardIn+=x*(.42+v.send*1.35);
        send+=x*v.send;
        // Pruning avoids retaining inaudible tails on entry-level phones.
        v.energy=Math.max(Math.abs(x),v.energy*.9999);
      }
      let board=0;
      for(let m=0;m<this.boardModes;m++){
        const y=this.boardA[m]*this.boardY1[m]-this.boardR2[m]*this.boardY2[m]+boardIn*this.boardInput[m];
        this.boardY2[m]=this.boardY1[m];this.boardY1[m]=y;
        board+=y;
      }
      const a=.72*dryL+.20*board,b=.72*dryR+.20*board;
      L[i]=a;if(stereo)R[i]=b;if(S)S[i]=send*.7;
    }
    for(let j=0;j<this.maxVoices;j++){
      const v=this.voices[j];if(!v.active)continue;
      v.age+=n/this.sr;
      // A gradually decaying energy tracker and a release grace period avoid
      // premature voice termination during zero crossings.
      if(v.release && v.age>.12 && v.energy<SILENCE)v.quiet++;else v.quiet=0;
      if(v.quiet>18||v.age>70){this.kill(v)}
    }
  }
}
if(typeof registerProcessor==='function'){
  registerProcessor('palco-physical-piano',class extends AudioWorkletProcessor{
    constructor(){super();this.engine=new PhysicalPianoEngine(sampleRate,'eco');
      this.port.onmessage=({data:m})=>{
        if(m.type==='on')this.engine.noteOn(m);
        else if(m.type==='off')this.engine.noteOff(m.id,m.fast,m.release);
        else if(m.type==='param')this.engine.updateVoice(m.id,m);
        else if(m.type==='send')this.engine.setSend(m.id,m.value);
        else if(m.type==='quality')this.engine.setQuality(m.quality);
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
