/**
 * E2.7 — OFFLINE pitch-evidence for private PCM16/24 WAV note crops.
 * A harmonic-family test against ±1/±2 semitone competitors. This detects
 * many mislabeled samples even when the fundamental is inaudible, but it
 * CANNOT distinguish every octave alias, prove acoustic origin/velocity,
 * or certify redistribution rights. Do not use for automatic licensing.
 * Only synthetic WAV buffers in tests; no real recordings in the repo.
 */
import {parseLocalPcmWav} from './private-wav-note-bank.mjs';

const midiHz=key=>440*2**((key-69)/12);
function fft(re,im){
 const n=re.length;
 for(let i=1,j=0;i<n;i++){
  let bit=n>>1;
  for(;j&bit;bit>>=1)j^=bit;
  if(i<j){
   [re[i],re[j]]=[re[j],re[i]];
   [im[i],im[j]]=[im[j],im[i]];
  }
 }
 for(let length=2;length<=n;length*=2){
  const a=-2*Math.PI/length,baseR=Math.cos(a),baseI=Math.sin(a);
  for(let p=0;p<n;p+=length){
   let wr=1,wi=0;
   for(let q=0;q<length/2;q++){
    const a=p+q,c=a+length/2;
    const tr=wr*re[c]-wi*im[c],ti=wr*im[c]+wi*re[c];
    re[c]=re[a]-tr;im[c]=im[a]-ti;
    re[a]+=tr;im[a]+=ti;
    const next=wr*baseR-wi*baseI;
    wi=wr*baseI+wi*baseR;wr=next;
   }
  }
 }
}
export function auditPrivatePcmPitch(source,{midiRoot,offsetSeconds=.15,
 analysisSeconds=.38,minContrastDb=5}={}){
 const fmt=parseLocalPcmWav(source);
 if(!Number.isInteger(midiRoot)||midiRoot<21||midiRoot>108||
    !Number.isFinite(offsetSeconds)||offsetSeconds<0||
    !Number.isFinite(analysisSeconds)||analysisSeconds<.15||analysisSeconds>.8||
    !Number.isFinite(minContrastDb)||minContrastDb<0||minContrastDb>25)
  throw new RangeError('invalid private pitch audit settings');
 const start=Math.round(offsetSeconds*fmt.sampleRate);
 const frames=Math.round(analysisSeconds*fmt.sampleRate);
 if(start+frames>fmt.frames)throw new RangeError('pitch audit window outside WAV');
 let size=1;while(size<frames)size*=2;
 if(size>262144)throw new RangeError('pitch FFT too long');
 const re=new Float64Array(size),im=new Float64Array(size);
 const stride=fmt.blockAlign,width=fmt.bitsPerSample/8;
 const fullScale=2**(fmt.bitsPerSample-1);
 let signalEnergy=0;
 for(let i=0;i<frames;i++){
  let sample=0;
  const frameAt=fmt.offset+(start+i)*stride;
  for(let channel=0;channel<fmt.channels;channel++)
   sample+=source.readIntLE(frameAt+channel*width,width)/fullScale;
  sample/=fmt.channels;
  signalEnergy+=sample*sample;
  re[i]=sample*(.5-.5*Math.cos(2*Math.PI*i/(frames-1)));
 }
 fft(re,im);
 const nyquist=fmt.sampleRate/2,amplitude=new Float64Array(size/2+1);
 for(let i=0;i<amplitude.length;i++)amplitude[i]=Math.hypot(re[i],im[i]);
 function score(key){
  const f0=midiHz(key);let result=0;
  for(let n=1;n<=12;n++){
   const f=f0*n;
   if(f>Math.min(8000,nyquist*.88))break;
   const range=Math.max(1.5,.008*f);
   const low=Math.max(1,Math.ceil((f-range)*size/fmt.sampleRate));
   const high=Math.min(amplitude.length-1,Math.floor((f+range)*size/fmt.sampleRate));
   let peak=0;
   for(let k=low;k<=high;k++)peak=Math.max(peak,amplitude[k]);
   result+=Math.sqrt(peak)/n**.8;
  }
  return result;
 }
 const expected=score(midiRoot);
 const neighbors=[];
 for(let k=midiRoot-2;k<=midiRoot+2;k++){
  if(k===midiRoot||k<21||k>108)continue;
  neighbors.push({midiRoot:k,score:score(k)});
 }
 const competitor=Math.max(...neighbors.map(x=>x.score));
 const contrast=expected>0&&competitor>0?20*Math.log10(expected/competitor):null;
 const rms=Math.sqrt(signalEnergy/frames);
 return {
  midiRoot,sampleRate:fmt.sampleRate,
  method:'Hann FFT; harmonic family vs 4 adjacent semitones; octave unresolved',
  rms,expectedScore:expected,competitorScore:competitor,
  semitoneContrastDb:contrast,
  supportsLabeledSemitone:contrast!==null&&contrast>=minContrastDb&&rms>=1e-6,
  verifiedAbsolutePitch:false,
  commercialRightsVerified:false
 };
}
