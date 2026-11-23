/**
 * Stage Synth E0: analyze previously acquired licensed single-note recordings.
 * Input contains ONLY local 48 kHz mono Float32-LE PCM files and provenance.
 * No network calls, recording assets, or calibration modifications.
 *
 * node scripts/analyze_reference_audio.mjs /tmp/manifest.json /tmp/results.json
 */
import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {measurePianoNote} from '../tests/piano_acoustic_metrics.mjs';
import {PianoEngine as Modal} from '../piano-worklet.js';
import {PhysicalPianoEngine as Legacy} from '../physical-piano-legacy.js';
import {PhysicalPianoEngine as Mechanical} from '../physical-piano.js';

const RATE=48000, BLOCK=128, DURATION=1.7;
const configs=[['A_modal',Modal],['B_v195',Legacy],['C_mechanical',Mechanical]];
const limit=(v,a,b)=>Math.max(a,Math.min(v,b));

export function decodeF32le(buffer){
 if(buffer.byteLength%4)throw new Error('PCM not aligned to Float32');
 const out=new Float32Array(buffer.byteLength/4);
 for(let i=0;i<out.length;i++)out[i]=buffer.readFloatLE(i*4);
 if(out.length<RATE*DURATION)throw new Error('PCM too short for measurement');
 return out;
}
export function locateAttack(samples,rate=RATE){
 const width=Math.round(rate*.005),total=Math.floor(Math.min(samples.length,rate*3)/width);
 const energies=new Float64Array(total);
 let strongest=0;
 for(let w=0;w<total;w++){
  let sum=0;
  const start=w*width;
  for(let k=0;k<width;k++){const x=samples[start+k];sum+=x*x;}
  energies[w]=Math.sqrt(sum/width);
  strongest=Math.max(strongest,energies[w]);
 }
 if(strongest<1e-5)throw Error('signal too quiet to locate onset');
 const threshold=strongest*.035;
 // Allow an imperfect attack transient; first of two consecutive above threshold.
 for(let i=0;i<total-1;i++)
  if(energies[i]>threshold&&energies[i+1]>threshold)
   return i*width/rate;
 throw Error('onset not identifiable');
}
function cropFromAttack(samples,onset,rate=RATE){
 const start=Math.max(0,Math.round(onset*rate));
 const count=Math.floor(rate*DURATION);
 if(start+count>samples.length)throw Error('insufficient audio after attack');
 return samples.slice(start,start+count);
}
function outputMetric(metric){
 return {
  f0:metric.f0,peak:metric.peak,rms:metric.rms,clipped:metric.clipped,nonFinite:metric.nonFinite,
  windows:metric.windows,earlyDecayDb:metric.earlyDecayDb,lateDecayDb:metric.lateDecayDb,
  bMedian:metric.bMedian,bSampleCount:metric.bSampleCount,
  harmonics:metric.harmonics.map(h=>({n:h.n,expectedHz:h.expectedHz,measuredHz:h.measuredHz,
   cents:h.cents,relativeDb:h.relativeDb,bEstimate:h.bEstimate,
   earlyDb:h.earlyDb,middleDb:h.middleDb,lateDb:h.lateDb}))
 };
}
function renderedStage(key,character='american',speed=80/127){
 const result={};
 for(const [engineId,Engine] of configs){
  const e=engineId==='A_modal'?new Engine(RATE):new Engine(RATE,'eco');
  if(engineId==='C_mechanical')e.setMechanicalModel({enabled:true,amount:.65,sympathy:true});
  e.noteOn({id:1,key,speed,hardness:.5,brightness:.5,character,send:0});
  const left=new Float32Array(BLOCK),right=new Float32Array(BLOCK),send=new Float32Array(BLOCK),out=new Float32Array(Math.floor(RATE*DURATION));
  for(let pos=0;pos<out.length;pos+=BLOCK){
   const n=Math.min(BLOCK,out.length-pos);e.render(left,right,send,n);
   for(let k=0;k<n;k++)out[pos+k]=(left[k]+right[k])*.5;
  }
  result[engineId]=outputMetric(measurePianoNote(out,{sampleRate:RATE,key}));
 }
 return result;
}
export function compareSpectralShape(real,stage){
 const bands=[];
 for(const re of real.harmonics){
  if(re.n===1||re.measuredHz==null||re.relativeDb==null||re.relativeDb< -29)continue;
  const synthetic=stage.harmonics.find(x=>x.n===re.n);
  if(synthetic?.relativeDb==null)continue;
  bands.push({n:re.n,realDb:re.relativeDb,syntheticDb:synthetic.relativeDb,
   deltaDb:synthetic.relativeDb-re.relativeDb});
 }
 return {comparablePartials:bands.length,meanAbsDb:bands.length?
  bands.reduce((a,b)=>a+Math.abs(b.deltaDb),0)/bands.length:null,partials:bands};
}
export function analyzeOne(entry){
 if(!Number.isInteger(entry.key)||entry.key<21||entry.key>108)throw new Error('Invalid MIDI key');
 if(!['american','japanese','felt','upright'].includes(entry.stageCharacter))throw new Error('Invalid character');
 const pcm=decodeF32le(readFileSync(entry.pcmPath));
 const onset=locateAttack(pcm,RATE);
 const real=outputMetric(measurePianoNote(cropFromAttack(pcm,onset,RATE),{sampleRate:RATE,key:entry.key}));
 const stage=renderedStage(entry.key,entry.stageCharacter);
 return {
  id:entry.id,instrument:entry.instrument,key:entry.key,dynamic:entry.dynamic,
  provenance:{originalUrl:entry.originalUrl,sha256:entry.sha256,bytes:entry.bytes,
   originalRate:entry.originalRate,originalChannels:entry.originalChannels,
   originalFormat:entry.originalFormat,captureNotes:entry.captureNotes},
  analysis:{rate:RATE,downmix:'ffmpeg stereo-to-mono average',offsetSeconds:onset,
   analysisSeconds:DURATION,recordingRoom:'non-anechoic'},
  real,stage,shapeDifferences:Object.fromEntries(Object.entries(stage).map(([name,metric])=>
   [name,compareSpectralShape(real,metric)]))
 };
}

if(process.argv[1]&&fileURLToPath(import.meta.url)===process.argv[1]){
 const [manifestFile,outputFile]=process.argv.slice(2);
 if(!manifestFile||!outputFile)throw Error('usage: node scripts/analyze_reference_audio.mjs manifest.json output.json');
 const manifest=JSON.parse(readFileSync(manifestFile,'utf8'));
 const analyses=manifest.notes.map(analyzeOne);
 const result={schema:'stage-piano-reference-e0-v1',reference:'University of Iowa Steinway Model B',
  notes:analyses,qualifications:[
   'Iowa recording is non-anechoic: tails include room response.',
   'pp/mf/ff are descriptive musical dynamics; Stage synth speed is 80/127 for all comparisons and is NOT a matched velocity.',
   'Different microphones and positions: relative spectral shape is diagnostic, not an objective realism score.',
   'B estimated with finite FFT and few sufficiently loud harmonics; null or unstable values are not physical certainties.',
   'Sources, SHA256 and numeric summaries only: no sample files are retained in GitHub artifacts.'
  ]};
 writeFileSync(outputFile,JSON.stringify(result,null,2)+'\n');
 console.log('E0 complete: '+analyses.length+' single-note measurements');
 for(const r of analyses){
  console.log('E0 '+r.instrument+' C'+(r.key/12-1)+' '+r.dynamic+' onset='+r.analysis.offsetSeconds.toFixed(3)+
   's rms='+r.real.rms.toFixed(5)+' B='+r.real.bMedian+' reliableB='+r.real.bSampleCount+
   ' harmonics='+r.real.harmonics.length);
  for(const [name,c] of Object.entries(r.shapeDifferences)){
   console.log('  '+name+' relative spectral delta (NOT fidelity score): '+
    (c.meanAbsDb==null?'n/a':c.meanAbsDb.toFixed(2)+'dB')+' ('+c.comparablePartials+' partials)');
  }
 }
}
