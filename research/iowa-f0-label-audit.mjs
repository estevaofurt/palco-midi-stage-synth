/**
 * Stage Synth — independent acoustic pitch-label audit for ORIGINAL Iowa AIFF.
 * OFFLINE RESEARCH ONLY. Not an instrument model, and not a physical
 * hammer/bridge estimator. YIN difference/autocorrelation on two late windows
 * guards against confusing a dominant overtone with the missing fundamental.
 *
 * IMPORTANT: YIN is approximate on stiff, inharmonic, multi-string pianos;
 * a near-MIDI estimate is evidence, NOT a verified mechanical f0. Ambiguous
 * windows or disagreements must be reported as INCONCLUSIVE, not silently
 * converted to the filename's pitch or a calibration parameter.
 */
const isSamples = x => x instanceof Float32Array || x instanceof Float64Array;
export const midiHz = key => 440 * 2**((key-69)/12);
const nearestMidi = hz => 69+12*Math.log2(hz/440);
const round = (x,n=3) => Number.isFinite(x)?Number(x.toFixed(n)):null;

/** Downsample 48k to 24k using a simple 2-tap average for this diagnostic.
 * Energy above the new Nyquist can alias; do not use this as a mastering SRC.
 * Our target f0 is at most about 2 kHz for C6 +1 octave. */
function downsample2(signal,start,count){
 const out=new Float64Array(count);
 for(let i=0;i<count;i++)out[i]=.5*(signal[start+2*i]+signal[start+2*i+1]);
 let mean=0;
 for(const x of out)mean+=x;
 mean/=out.length;
 let energy=0;
 for(let i=0;i<out.length;i++){
  out[i]-=mean;
  energy+=out[i]*out[i];
 }
 if(!(energy>1e-12))return null;
 return out;
}

/**
 * YIN cumulative-mean-normalized difference (CMND). The search is broad
 * (a little over one octave above/below the label), specifically to detect
 * off-by-octave mislabeled source audio.
 * Only chooses a first trough below the reliability threshold; if no
 * trustworthy trough is present, reports the best candidate as uncertain.
 */
export function yinWindow(signal,rate,expectedHz,{
 startSeconds=.12,windowSeconds=.35,maxRatio=2.2,threshold=.20
}={}){
 if(!isSamples(signal)||signal.length<Math.ceil(rate*(startSeconds+windowSeconds)))
  throw new RangeError('insufficient Float PCM for YIN window');
 if(!Number.isFinite(rate)||rate<8000||rate>192000||
    !Number.isFinite(expectedHz)||expectedHz<=0)
  throw new RangeError('invalid sample rate or expected pitch');
 if(!(startSeconds>=0&&windowSeconds>=.15&&maxRatio>1&&maxRatio<=4&&threshold>0&&threshold<1))
  throw new RangeError('invalid window options');
 // Original references are decoded to 48 kHz by existing Iowa acquisition.
 const factor=rate===48000?2:1;
 const dr=rate/factor;
 const start=Math.round(startSeconds*rate);
 const usable=Math.floor(Math.min(windowSeconds*dr,(signal.length-start)/factor));
 const x= factor===2?downsample2(signal,start,usable):
   Float64Array.from(signal.slice(start,start+usable));
 if(!x)return {f0Hz:null,periodicity:null,selectedByThreshold:false,reason:'silent-window'};
 if(factor===1){
  let avg=0;for(const v of x)avg+=v;avg/=x.length;
  for(let i=0;i<x.length;i++)x[i]-=avg;
 }
 let lagLow=Math.max(3,Math.floor(dr/(expectedHz*maxRatio)));
 let lagHigh=Math.min(Math.ceil(dr/(expectedHz/maxRatio)),Math.floor(x.length*.3));
 if(lagHigh<lagLow+3)throw new RangeError('pitch cannot be resolved at selected sample rate');
 const len=x.length-lagHigh;
 const d=new Float64Array(lagHigh+2), cmnd=new Float64Array(lagHigh+2);
 for(let lag=1;lag<=lagHigh;lag++){
  let sum=0;
  // Constant integration duration for all lags avoids artificial preference
  // for short periods when the piano signal decays.
  for(let i=0;i<len;i++){
   const z=x[i]-x[i+lag];
   sum+=z*z;
  }
  d[lag]=sum;
 }
 let cum=0;
 for(let lag=1;lag<=lagHigh;lag++){
  cum+=d[lag];
  cmnd[lag]=cum>0?lag*d[lag]/cum:1;
 }
 // earliest reliable local trough, else global best with an uncertainty flag.
 let selected=-1,selectedByThreshold=false;
 for(let lag=lagLow+1;lag<lagHigh;lag++){
  if(cmnd[lag]<threshold && cmnd[lag]<=cmnd[lag-1] && cmnd[lag]<=cmnd[lag+1]){
   selected=lag;selectedByThreshold=true;break;
  }
 }
 if(selected<0){
  let best=Infinity;
  for(let lag=lagLow;lag<=lagHigh;lag++){
   if(cmnd[lag]<best){best=cmnd[lag];selected=lag;}
  }
 }
 if(selected<0) return {f0Hz:null,periodicity:null,selectedByThreshold:false,reason:'no-trough'};
 const ym=cmnd[Math.max(1,selected-1)],y=cmnd[selected],
  yp=cmnd[Math.min(lagHigh,selected+1)];
 const den=ym-2*y+yp;
 const offset=Math.abs(den)>1e-12?Math.max(-.5,Math.min(.5,.5*(ym-yp)/den)):0;
 const f0Hz=dr/(selected+offset);
 return {f0Hz:round(f0Hz,5),periodicity:round(y,5),
  selectedByThreshold,reason:selectedByThreshold?'first-reliable-trough':'fallback-trough',
  sampleRate:dr,approximateWindowSeconds:round(len/dr,4),lag:selected};
}

export function auditPitchLabel(samples,{sampleRate=48000,key,
  windowStarts=[.10,.60],threshold=.20}={}){
 if(!isSamples(samples)||samples.length<Math.ceil(sampleRate*1.1))
  throw new RangeError('need at least 1.1 seconds of Float PCM');
 if(!Number.isInteger(key)||key<21||key>108)
  throw new RangeError('invalid expected MIDI key');
 const expected=midiHz(key);
 const windows=windowStarts.map(t=>yinWindow(samples,sampleRate,expected,{
  startSeconds:t,windowSeconds:.35,threshold
 }));
 const usable=windows.filter(w=>w.f0Hz!==null);
 const agreementCents=usable.length===2?
  Math.abs(1200*Math.log2(usable[0].f0Hz/usable[1].f0Hz)):null;
 // Require two independently timed stable estimates, not just two
 // identical audio blocks or a single strong harmonic peak.
 const reliable=usable.length===2&&
  usable.every(w=>w.selectedByThreshold&&w.periodicity<.25)&&
  agreementCents<50;
 const f0Hz=usable.length===2?
   Math.sqrt(usable[0].f0Hz*usable[1].f0Hz):null;
 const midi=f0Hz===null?null:nearestMidi(f0Hz);
 const nearest=f0Hz===null?null:Math.round(midi);
 const cents=f0Hz===null?null:(midi-nearest)*100;
 // Distinguish "not proven" from "contradictory observed octave".
 const deviation=f0Hz===null?null:1200*Math.log2(f0Hz/expected);
 const classification=!reliable?'inconclusive':
   Math.abs(deviation)<=55?'label-consistent':
   Math.abs(deviation)>=500?'label-mismatch-candidate':
   'tuning-or-label-review';
 return {
  key,expectedHz:round(expected,5),
  f0Hz:round(f0Hz,5),nearestMidi:nearest,cents:round(cents,1),
  centsFromLabel:round(deviation,1),reliable,
  classification,agreementCents:round(agreementCents,1),
  windows
 };
}
