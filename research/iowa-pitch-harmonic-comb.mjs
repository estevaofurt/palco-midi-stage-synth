/**
 * Independent FFT harmonic-comb DIAGNOSTIC for piano pitch labels.
 * This deliberately does not share YIN/autocorrelation calculations.
 * No inference of hammer force, acoustic body, or calibrated inharmonicity.
 * A spectral "support" is only a candidate; it is not ground-truth f0.
 */
import {midiHz} from './iowa-f0-label-audit.mjs';
const FFT=32768,LOW=25,HIGH=8000;
function fft(re,im){
 const n=re.length;
 for(let i=1,j=0;i<n;i++){
  let b=n>>>1;
  for(;j&b;b>>>=1)j^=b;
  j^=b;
  if(i<j){[re[i],re[j]]=[re[j],re[i]];[im[i],im[j]]=[im[j],im[i]];}
 }
 for(let len=2;len<=n;len<<=1){
  const wr=Math.cos(2*Math.PI/len),wi=-Math.sin(2*Math.PI/len);
  for(let offset=0;offset<n;offset+=len){
   let pr=1,pi=0;
   for(let j=0;j<len/2;j++){
    const a=offset+j,b=a+len/2;
    const ar=pr*re[b]-pi*im[b],ai=pi*re[b]+pr*im[b];
    re[b]=re[a]-ar; im[b]=im[a]-ai;
    re[a]+=ar; im[a]+=ai;
    const q=pr*wr-pi*wi;pi=pr*wi+pi*wr;pr=q;
   }
  }
 }
}
const round=(v,n=3)=>Number(v.toFixed(n));

export function compareOctaveHarmonicSupport(samples,{sampleRate=48000,key,startSeconds=.10}={}){
 if(!(samples instanceof Float32Array||samples instanceof Float64Array)||
    !Number.isInteger(key)||key<21||key>108||
    !Number.isFinite(sampleRate)||sampleRate<22050||sampleRate>192000||
    !Number.isFinite(startSeconds)||startSeconds<0||
    samples.length<Math.ceil(sampleRate*startSeconds)+FFT)
  throw new RangeError('invalid or insufficient original PCM for spectral pitch check');
 const start=Math.round(sampleRate*startSeconds),re=new Float64Array(FFT),im=new Float64Array(FFT);
 let mean=0;
 for(let i=0;i<FFT;i++)mean+=samples[start+i];
 mean/=FFT;
 for(let i=0;i<FFT;i++){
  const z=samples[start+i]-mean;
  if(!Number.isFinite(z))throw new TypeError('invalid PCM');
  re[i]=z*(.5-.5*Math.cos(2*Math.PI*i/FFT));
 }
 fft(re,im);
 const maxBin=Math.min(FFT/2-1,Math.floor(HIGH*FFT/sampleRate));
 const mag=new Float64Array(maxBin+1);
 let maximum=0;
 for(let k=Math.ceil(LOW*FFT/sampleRate);k<=maxBin;k++){
  mag[k]=Math.hypot(re[k],im[k]);maximum=Math.max(maximum,mag[k]);
 }
 if(!(maximum>1e-10))return {classification:'spectral-inconclusive',reason:'silent window',candidates:[]};
 const peakNear=f=>{
  const k=f*FFT/sampleRate,span=Math.max(2,Math.ceil(.0035*k));
  const lo=Math.max(1,Math.floor(k)-span),hi=Math.min(maxBin,Math.ceil(k)+span);
  let peak=0;
  for(let i=lo;i<=hi;i++)peak=Math.max(peak,mag[i]);
  return peak/maximum;
 };
 const reference=midiHz(key);
 const candidates=[];
 for(const relativeOctave of [-1,0,1]){
  const fundamental=reference*2**relativeOctave;
  if(fundamental>sampleRate*.40)continue;
  let best=null;
  for(const b of [0,.00005,.00015,.0005,.0015,.003]){
   let score=0,hits=0,odd=0;
   // A true fundamental can be very weak, but a subharmonic octave will
   // leave odd multiples missing and should not win by energy alone.
   for(let harmonic=1;harmonic<=10;harmonic++){
    const frequency=fundamental*harmonic*Math.sqrt(1+b*harmonic*harmonic);
    if(frequency>Math.min(HIGH,sampleRate*.45))break;
    const p=peakNear(frequency);
    const weight=1/Math.sqrt(harmonic);
    score+=weight*Math.log1p(p*30);
    if(p>.045){hits++;if(harmonic%2)odd++;}
   }
   // Odd-partial support discourages false half-frequency ("subharmonic")
   // wins but is not guaranteed for every piano spectrum.
   score+=.08*odd;
   if(!best||score>best.score)best={relativeOctave,score,hits,odd,b};
  }
  candidates.push(best);
 }
 const original=candidates.find(x=>x.relativeOctave===0);
 const others=candidates.filter(x=>x.relativeOctave!==0);
 const alt=others.reduce((a,b)=>!a||b.score>a.score?b:a,null);
 const margin=original.score-alt.score;
 return {
  method:'FFT harmonic comb with positive inharmonicity candidates; diagnostic only',
  frequencyBinHz:round(sampleRate/FFT,4),
  fftSeconds:round(FFT/sampleRate,4),
  nominalMidi:key,nominalHz:round(reference,4),
  classification:margin>.55?'spectral-supports-label':
    margin<-.55?'spectral-mismatch-candidate':'spectral-inconclusive',
  scoreMargin:round(margin,3),
  candidates:candidates.map(x=>({relativeOctave:x.relativeOctave,
    score:round(x.score,3),harmonicHits:x.hits,oddHits:x.odd,
    testedInharmonicity:x.b}))
 };
}
