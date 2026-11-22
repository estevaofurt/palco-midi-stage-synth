/*
 * Stage Synth — Physical Piano Core v0.7 (original DSP, no samples).
 * Lightweight hammered-string waveguide + a shared resonant soundboard.
 * The core is platform-independent JavaScript: it can render in Node or AudioWorklet.
 * This is a perceptual/physically informed model, not a calibrated acoustic piano.
 * All ring buffers and voices are preallocated. render() performs no heap allocations.
 * Reference: J. O. Smith, Physical Audio Signal Processing (digital waveguides).
 */
export const PHYSICAL_PRESETS=Object.freeze({
  eco: {voices:32, strings:1, boardModes:3},
  balanced: {voices:48,strings:2,boardModes:5},
  studio: {voices:64,strings:2,boardModes:7}
});
const TWOPI=2*Math.PI;
const MAX_DELAY=8192; // supports A0 at 48/44.1 kHz and even extended bass notes
const SILENCE=0.000025;
const clamp=(x,lo,hi)=>Math.min(hi,Math.max(lo,x));
export const midiHz=key=>440*2**((key-69)/12);
// Four separate timbral models, calibrated against aligned C4 reference captures
// from the owner. These are *perceptual* targets of instrument + original FX,
// not physical constants inferred from isolated dry recordings. The audio files
// are NOT embedded or required at runtime.
// Partial weights amplify/dampen the low modal harmonics; transientTime/Floor
// model the early, rapidly-decaying radiated sound of the soundboard.
const profiles={
  japanese:{stiff:.27,bright:.91,body:1.08,decay:1.09,detune:.82,position:.128,
    partials:[1.00,8.0,3.3,.90,.82,.70],transientTime:.27,transientFloor:.20,stereo:.96,toneCutoff:0,toneMix:0},
  american:{stiff:.23,bright:.77,body:1.08,decay:1.13,detune:.84,position:.122,
    partials:[1.08,.34,.18,1.15,1.05,.95],transientTime:.38,transientFloor:.30,stereo:1.02,toneCutoff:900,toneMix:.64},
  felt:{stiff:.18,bright:.30,body:.82,decay:.88,detune:.65,position:.148,
    partials:[1.17,.26,.20,.40,.32,.25],transientTime:.33,transientFloor:.24,stereo:.70,toneCutoff:1250,toneMix:.92},
  upright:{stiff:.38,bright:.67,body:.90,decay:.84,detune:1.65,position:.153,
    partials:[1.05,4.6,3.7,1.25,1.08,.95],transientTime:.30,transientFloor:.24,stereo:.78,toneCutoff:0,toneMix:0}
};
// Public, small calibration metadata for deterministic tests and future tuning.
export const PIANO_CALIBRATION=Object.freeze(Object.fromEntries(
  Object.entries(profiles).map(([id,p])=>[id,Object.freeze({
    partials:Object.freeze([...p.partials]),transientTime:p.transientTime,
    transientFloor:p.transientFloor,stereo:p.stereo,toneCutoff:p.toneCutoff
  })])
));
const BOARD=[[87,.18],[134,.13],[198,.11],[279,.090],[398,.078],[590,.060],[876,.045]];
// The fast waveguide handles broadband motion; a few independently damped,
// stretched partials add the multiple decay slopes of a real hammered string.
// They do not use samples or oscillators from the Web Audio graph.
const PARTIALS=[1,2,3,4,5,7];
const PARTIAL_MODES={eco:4,balanced:5,studio:6};

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
    // Tiny second-string fundamental: adds slow beating on eco without a second waveguide.
    this.beatRe=0;this.beatIm=0;this.beatC=1;this.beatS=0;this.beatGain=0;
    this.modalY1=new Float64Array(PARTIALS.length);
    this.modalY2=new Float64Array(PARTIALS.length);
    this.modalA=new Float64Array(PARTIALS.length);
    this.modalR2=new Float64Array(PARTIALS.length);
    this.modalReleaseA=new Float64Array(PARTIALS.length);
    this.modalReleaseR2=new Float64Array(PARTIALS.length);
    this.modalCount=0;
    this.modalMix=0;
    this.hammerBody=0;this.hammerBodyDecay=0;
    this.bridge=0;this.bridgePrevious=0;
    this.keyBrightness=0;this.boardWeight=1;this.hammerContactMs=0;
    this.transient=1;this.transientDecay=1;this.transientFloor=1;
    this.toneZ=0;this.toneSpeed=1;this.toneMix=0;

  }
}
export class PhysicalPianoEngine {
  constructor(sr=48000,quality='eco'){
    this.sr=sr;this.voices=Array.from({length:PHYSICAL_PRESETS.studio.voices},()=>new StringVoice());
    this.mode='eco';this.maxVoices=32;this.stringCount=1;this.boardModes=3;this.partialModes=4;
    this.setQuality(quality);
    this.counter=0;this.done=[];this.doneCount=0;this.seed=0x18ca6c9f;
    this.blockVoices=new Array(PHYSICAL_PRESETS.studio.voices);
    this.boardY1=new Float64Array(BOARD.length);this.boardY2=new Float64Array(BOARD.length);
    this.boardA=new Float64Array(BOARD.length);this.boardR2=new Float64Array(BOARD.length);
    this.boardInput=new Float64Array(BOARD.length);
    this.mixGain=1.2; // active-note headroom with independent fast attack and slow release
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
    this.maxVoices=m.voices;this.stringCount=m.strings;this.boardModes=m.boardModes;this.partialModes=PARTIAL_MODES[this.mode];
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
  // Hammer-to-string traveling-wave excitation: a zero-mean bipolar contact
  // pulse, rather than the triangular DISPLACEMENT of a plucked string.
  // The separation of the pulses represents a hammer striking at beta of the
  // speaking length and suppresses partials around n=1/beta. A soft felt
  // contact spreads force over time; higher velocities shorten the pulse.
  // Both Gaussian pulses wrap around the delay line, without allocating.
  seedString(line,period,position,level,hardness,variation,widthScale=1){
    line.fill(0);
    const count=Math.ceil(period)+3;
    const start=MAX_DELAY-period;
    const width=(.026+.036*(1-hardness))*widthScale;
    const sharp=1/(2*width*width);
    let sum=0;
    for(let k=0;k<count;k++){
      const phi=(k/period)%1;
      const d0=Math.min(phi,1-phi);
      const d1=Math.abs(phi-position);
      // A collision excites travelling velocity waves. Lower partials are
      // deliberately reinforced relative to the former plucked-like bipolar
      // seed, which exaggerated the third harmonic around middle C.
      const contact=Math.exp(-d0*d0*sharp)*.92-Math.exp(-d1*d1*sharp)*.36;
      const val=contact*level*(1+variation);
      line[(Math.floor(start+k)+MAX_DELAY)%MAX_DELAY]=val;
      sum+=val;
    }
    const dc=sum/count;
    for(let k=0;k<count;k++){
      const idx=(Math.floor(start+k)+MAX_DELAY)%MAX_DELAY;
      line[idx]-=dc;
    }
  }
  noteOn({id,key=60,speed=.7,hardness=.5,character='japanese',brightness=.5,decayScale=1,send=.06}){
    key=clamp(Math.round(key),21,108);speed=clamp(speed,.001,1);hardness=clamp(hardness,0,1);
    const cfg=profiles[character]||profiles.japanese;
    const freq=midiHz(key),v=this.acquire();
    const stiffness=cfg.stiff*(.60+.6*(key/108));
    const contactHard=clamp((hardness*.65+speed*.35)*cfg.bright,0,1);
    const isJapanese=character==='japanese';
    const reg=clamp((key-48)/48,0,1); // piano register, not merely MIDI volume
    // CFX reference: rich, rounded bass; short, articulate hammer in the treble.
    // This contact profile is a tuning hypothesis: the supplied performance is
    // polyphonic and reverberant, so no isolated string constants can be measured.
    const stringWidth=isJapanese?1-.43*reg:1;
    // More hammer force must sound brighter, not darker: faster low-pass coefficient.
    const speedLP=clamp(.57+.16*clamp((key-64)/40,0,1)+.19*contactHard,.47,.94);
    const tuned=this.setupPeriod(freq,stiffness,speedLP);
    const detuneCents=key<38?.14:cfg.detune*(.6+.4*key/108);
    const freqB=freq*2**(detuneCents/1200);
    const tunedB=this.setupPeriod(freqB,stiffness,speedLP);
    const touch=speed**1.35;
    const excitation=.21*touch*cfg.body*(.66+.34*clamp(brightness,0,1))*(isJapanese?1-.06*reg:1);
    const tension=clamp((key-21)/87,0,1);
    const position=cfg.position-.015*tension;
    this.seedString(v.lineA,tuned.period,position,excitation,contactHard,0,stringWidth);
    if(this.stringCount>1)this.seedString(v.lineB,tunedB.period,position,excitation*.84,contactHard*.94,-.005,stringWidth);
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
    const pos=clamp((key-65)/45,-1,1),ang=Math.PI/4+pos*.30*cfg.stereo;
    v.left=Math.cos(ang)*1.13;v.right=Math.sin(ang)*1.13;
    // Fast, instrument-specific attack-to-body transition. One multiply per
    // voice per sample, no exp() and no new allocations on the audio thread.
    v.transient=1;
    v.transientDecay=Math.exp(-1/(this.sr*cfg.transientTime));
    v.transientFloor=cfg.transientFloor;
    // A lightweight radiated-sound low-pass specifically for the warm
    // American and Felt characters. This is NOT a global post-EQ: it follows
    // each note's register and is applied before the bridge/body resonance.
    const cutoff=cfg.toneCutoff+Math.max(0,key-60)*21;
    v.toneSpeed=cutoff?1-Math.exp(-TWOPI*cutoff/this.sr):1;
    v.toneZ=0;v.toneMix=cfg.toneMix;
    v.level=1;v.levelTarget=1;v.send=v.sendTarget=clamp(send,0,1);
    // An inexpensive coupled-string beating mode supplements the single
    // economical waveguide; balanced/studio use two actual tuned waveguides.
    const beatHz=freq*2**(detuneCents/1200),beatDamp=Math.exp(-1/(this.sr*(2.8+4.8*(1-tension))));
    const beatPhase=TWOPI*beatHz/this.sr;
    v.beatC=beatDamp*Math.cos(beatPhase);v.beatS=beatDamp*Math.sin(beatPhase);
    v.beatRe=excitation*.20;v.beatIm=0;
    v.beatGain=this.stringCount===1?.16:(isJapanese&&key>=64?.055:.035);
    v.hammerNoise=0.0009*speed**2*contactHard;v.noiseState=0;
    // The hammer compresses felt before rebounding. Faster strikes shorten
    // the force pulse, exciting more high partials. A few physically-informed
    // inharmonic modes give separately evolving spectral components, without
    // multiplying string delay lines on an entry-level Android phone.
    // A fixed 3ms contact at all pitches removed almost every upper partial
    // above C6. An octave-dependent contact is essential for a convincing
    // sparkling treble; low notes retain a softer, longer contact instead.
    const contactMs=isJapanese
      ?clamp(2.7*2**(-(key-60)/28),.27,4.8)*(.55+.72*(1-speed))
      :(character==='felt'?4.2:character==='upright'?2.4:3.0)*(.55+1.25*(1-speed));
    v.hammerContactMs=contactMs;
    v.keyBrightness=reg;
    v.boardWeight=isJapanese?1.16-.25*reg:1;
    const contactSec=contactMs/1000;
    const B=clamp((character==='upright'?.00035:.00014)*2**((key-60)/23),.000015,.003);
    const modeBalance=[1,.44,.20,.14,.075,.035];
    v.modalCount=this.partialModes;
    v.modalMix=(.11+.075*cfg.body)*touch;
    for(let i=0;i<PARTIALS.length;i++){
      const n=PARTIALS[i],f=freq*n*Math.sqrt((1+B*n*n)/(1+B));
      if(i>=v.modalCount||f>=this.sr*.44){v.modalY1[i]=v.modalY2[i]=0;continue;}
      const w=TWOPI*f/this.sr;
      // Two time scales of felt compression: a broad contact for warm body,
      // and a very brief elastic tip that radiates treble transients. This
      // prevents upper notes from losing all upper partials at realistic
      // contact durations (a weakness of the previous single Gaussian).
      const mainContact=Math.exp(-.5*(Math.PI*f*contactSec*.57)**2);
      const fastContact=Math.exp(-.5*(Math.PI*f*contactSec*.14)**2);
      const fastFraction=isJapanese?.16+.40*reg:0;
      const contact=mainContact*(1-fastFraction)+fastContact*fastFraction;
      const strikeNode=Math.max(.14,Math.abs(Math.sin(Math.PI*n*position)));
      const brightnessScale=(.65+.7*contactHard)*(.68+.5*clamp(brightness,0,1));
      // Distinct bass and treble spectra: at higher pitches the fast partials
      // are easier to hear, while in the low register the fundamental dominates.
      const registerTilt=isJapanese
        ?(n===1?1:(.77+reg*.58)*Math.pow(n,-.10*(1-reg)))
        :1;
      // The C4 reference revealed opposite H2/H1 balances across instruments.
      // Keep spectral signatures distinct instead of one sound with four EQs.
      // Weights taper toward keyboard extremes where no isolated reference
      // notes were supplied, preventing over-bright high C or boomy low A.
      // Medições da apresentação não representam notas isoladas. Manter a
      // calibração de C4 local àquela região evita sinos nos registros agudos.
      const refWindow=.12+.88*Math.exp(-(((key-60)/11)**2));
      const weight=1+(cfg.partials[i]-1)*refWindow;
      const amplitude=modeBalance[i]*weight*contact*strikeNode*brightnessScale*registerTilt;
      // Independent decays: bass fundamental lingers, upper partials fade
      // faster; the pattern varies smoothly across the keyboard.
      const modeTau=(n===1?6.2:n===2?3.0:1.9)*2**((60-key)/30)*cfg.decay/Math.sqrt(n);
      const decay=Math.exp(-1/(this.sr*clamp(modeTau,.15,19)));
      const release=Math.exp(-1/(this.sr*clamp(.13+.15/n,.055,.32)));
      v.modalA[i]=2*decay*Math.cos(w);
      v.modalR2[i]=decay*decay;
      v.modalReleaseA[i]=2*release*Math.cos(w);
      v.modalReleaseR2[i]=release*release;
      // Excitation phase comes from the force impulse (a velocity strike).
      v.modalY1[i]=amplitude;
      v.modalY2[i]=amplitude*Math.cos(w);
    }
    v.hammerBody=.006*touch*(.55+contactHard*.6)*cfg.body*(isJapanese?1.17-.22*reg:1);
    v.hammerBodyDecay=Math.exp(-1/(this.sr*(.002+.004*(1-speed))));
    v.bridge=v.bridgePrevious=0;
  }
  noteOff(id,fast=false,release=.4){
    const v=this.find(id);if(!v)return;
    v.release=true;v.releaseTime=fast?.018:clamp(release,.025,3);
    v.loopTarget=Math.exp(-6.91/(v.freq*v.releaseTime));
    // The inexpensive unison resonator must obey the damper too.
    const phase=Math.atan2(v.beatS,v.beatC);
    const r=Math.exp(-6.91/(this.sr*v.releaseTime));
    v.beatC=r*Math.cos(phase);v.beatS=r*Math.sin(phase);
    if(fast)v.levelTarget=0;
    if(!fast){
      for(let i=0;i<v.modalCount;i++){
        const a=v.modalA[i],r2=v.modalR2[i],w=Math.acos(clamp(a/(2*Math.sqrt(r2)),-1,1));
        const r=Math.exp(-1/(this.sr*v.releaseTime));
        v.modalReleaseA[i]=2*r*Math.cos(w);v.modalReleaseR2[i]=r*r;
      }
    }
  }
  setSend(id,x){const v=this.find(id);if(v)v.sendTarget=clamp(x,0,1)}
  updateVoice(id,{decayScale,brightness,damping,send,release}={}){
    const v=this.find(id);if(!v)return;
    if(Number.isFinite(send))v.sendTarget=clamp(send,0,1);
    if(Number.isFinite(release))v.releaseTime=clamp(release,.025,3);
    if(Number.isFinite(brightness))v.lpSpeed=clamp(.53+.38*brightness,.45,.93);
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
    // Compactar a lista uma vez por bloco de 128 amostras evita percorrer
    // 64 vozes inativas em cada amostra e reduz CPU quando há poucas notas.
    let active=0;
    for(let j=0;j<this.maxVoices;j++)if(this.voices[j].active)this.blockVoices[active++]=this.voices[j];
    // A smooth headroom correction, calculated once per block, prevents a
    // 32/64-note chord from overwhelming the final output. Not a hard limiter.
    const targetMix=1.2/Math.sqrt(Math.max(1,active/2.5));
    for(let i=0;i<n;i++){
      this.mixGain+=(targetMix-this.mixGain)*(targetMix<this.mixGain?.028:.0009);
      let dryL=0,dryR=0,send=0,boardIn=0;
      for(let j=0;j<active;j++){
        const v=this.blockVoices[j];
        v.loopGain+=(v.loopTarget-v.loopGain)*.0035;
        v.level+=(v.levelTarget-v.level)*.007;
        v.send+=(v.sendTarget-v.send)*.002;
        const x1=this.tickString(v,false);
        const x2=this.stringCount>1?this.tickString(v,true):0;
        v.write++;if(v.write===MAX_DELAY)v.write=0;
        let x=(x1+(this.stringCount>1?x2*.78:0))*(this.stringCount>1?.57:1);
        // Separate partial decays are the main timbral improvement over the
        // earlier single-loop model. A few recurrences are inexpensive even
        // with 64 voices; all arrays were allocated outside the audio thread.
        let modal=0;
        for(let k=0;k<v.modalCount;k++){
          const a=v.release?v.modalReleaseA[k]:v.modalA[k];
          const r2=v.release?v.modalReleaseR2[k]:v.modalR2[k];
          const next=a*v.modalY1[k]-r2*v.modalY2[k];
          v.modalY2[k]=v.modalY1[k];v.modalY1[k]=next;
          modal+=next;
        }
        x=x*.67+modal*v.modalMix;
        const br=v.beatRe,bi=v.beatIm;
        v.beatRe=br*v.beatC-bi*v.beatS;
        v.beatIm=br*v.beatS+bi*v.beatC;
        x+=br*v.beatGain;
        // The strike transient is physical excitation + a short hammer-noise term.
        if(v.hammerNoise>1e-6){
          v.noiseState+=(this.random()-v.noiseState)*.26;
          x+=v.hammerNoise*v.noiseState;
          v.hammerNoise*=.9978;
        }
        if(v.hammerBody>1e-7){
          // A very short felt/thump component belongs to the attack, not to
          // the sustained string tone, and decays within a few milliseconds.
          x+=v.hammerBody*(.3+.7*v.noiseState);
          v.hammerBody*=v.hammerBodyDecay;
        }
        if(v.fade<96){x*=v.fade/96;v.fade++}
        v.transient*=v.transientDecay;
        x*=v.level*(v.transientFloor+(1-v.transientFloor)*v.transient);
        // Acoustic radiation at the bridge is spectrally different from raw
        // string displacement; a cheap first difference adds that bite.
        if(v.toneMix){
          v.toneZ+=(x-v.toneZ)*v.toneSpeed;
          x=x*(1-v.toneMix)+v.toneZ*v.toneMix;
        }
        const radiation=x-.54*v.bridgePrevious;
        v.bridgePrevious=x;
        dryL+=radiation*v.left;dryR+=radiation*v.right;
        boardIn+=radiation*(.42+v.send*1.35)*v.boardWeight;
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
      L[i]=a*this.mixGain;if(stereo)R[i]=b*this.mixGain;if(S)S[i]=send*.7*this.mixGain;
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
  registerProcessor('palco-physical-piano-legacy',class extends AudioWorkletProcessor{
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
