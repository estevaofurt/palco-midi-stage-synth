/**
 * No-dependency audit of emitted WAVs. These are waveform comparisons, NOT
 * perceptual fidelity scores or a soundboard mobility measurement.
 *
 * node scripts/measure_bass_abcd_similarity.mjs artifacts/stage-bass-wood-ABCD
 * Outputs a numeric JSON in the same directory; never adjusts synth DSP.
 */
import {readFileSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
const RATE=48000;
const names={
  control:'01_stable_48k_estereo_24bit.wav',
  wood:'02_wood_48k_estereo_24bit.wav',
  longitudinal:'03_longitudinal_48k_estereo_24bit.wav',
  combined:'04_combined_48k_estereo_24bit.wav'
};
const cases=[
  {label:'C1',start:.45},
  {label:'A1',start:2.55},
  {label:'C2-pp',start:4.65},
  {label:'C2-mf',start:6.75},
  {label:'C2-ff',start:8.85},
  {label:'C3-mf',start:10.95},
  {label:'C4-mf guard',start:13.05}
];
function load(file){
 const b=readFileSync(file);
 if(b.toString('ascii',0,4)!=='RIFF'||b.toString('ascii',8,12)!=='WAVE'||
    b.toString('ascii',36,40)!=='data'||b.readUInt16LE(20)!==1||
    b.readUInt16LE(22)!==2||b.readUInt32LE(24)!==RATE||
    b.readUInt16LE(34)!==24)
   throw Error('Not 48kHz stereo 24bit little-endian PCM: '+file);
 const count=b.readUInt32LE(40)/6;
 if(!Number.isInteger(count)||b.length!==44+count*6)throw Error('Invalid PCM size');
 const mono=new Float32Array(count);
 for(let i=0;i<count;i++){
  const off=44+i*6;
  mono[i]=.5*(b.readIntLE(off,3)+b.readIntLE(off+3,3))/8388607;
 }
 return mono;
}
function compare(a,b,start,end){
 const first=Math.round(start*RATE),last=Math.round(end*RATE);
 if(first<0||last>a.length||last>b.length)throw Error('Section outside WAV');
 let aa=0,bb=0,ab=0,ma=0,mb=0,dd=0;
 for(let i=first;i<last;i++){
   const x=a[i],y=b[i];
   ma+=x;mb+=y;aa+=x*x;bb+=y*y;ab+=x*y;
   dd+=(x-y)*(x-y);
 }
 const n=last-first;
 const cov=ab-ma*mb/n;
 const ea=aa-ma*ma/n,eb=bb-mb*mb/n;
 const cc=cov/Math.sqrt(Math.max(1e-20,ea*eb));
 return {
   timeSeconds:[start,end],
   waveformCorrelation:Math.round(cc*1000000)/1000000,
   candidateVsControlRms:Math.sqrt(bb/Math.max(1e-20,aa)),
   rmsDifferenceRelativeToControl:Math.sqrt(dd/Math.max(1e-20,aa))
 };
}
const dir=process.argv[2]||'artifacts/stage-bass-wood-ABCD';
const waves=Object.fromEntries(Object.entries(names).map(([k,v])=>[k,load(join(dir,v))]));
const ref=waves.control;
const rows=cases.map(c=>({
 note:c.label,
 candidates:Object.fromEntries(['wood','longitudinal','combined'].map(k=>[
   k,compare(ref,waves[k],c.start+.20,c.start+.55)
 ]))
}));
for(const row of rows){
 console.log('BASS_DIFFERENCE '+row.note+' '+JSON.stringify(row.candidates));
}
for(const row of rows){
 for(const [name,c] of Object.entries(row.candidates)){
  if(!Number.isFinite(c.waveformCorrelation)||Math.abs(c.waveformCorrelation)>1.00001||
     !Number.isFinite(c.rmsDifferenceRelativeToControl))
    throw Error('Invalid difference measure '+row.note+'/'+name);
 }
}
const report={
 schema:'stage-d-bass-abcd-waveform-difference-v1',
 measurement:'mono average of signed PCM24; sustained windows +200ms to +550ms after notes',
 caveats:'Waveform correlation does not prove perceptual equivalence or piano fidelity; panned/stereo information is collapsed only for this diagnostic.',
 codeChangesToPublishedSynth:false,
 cases:rows
};
writeFileSync(join(dir,'waveform_similarity_numeric_only.json'),JSON.stringify(report,null,2)+'\n');
console.log('MEASUREMENTS PASSED: 7 notes x 3 experiments (no audio DSP modified)');
