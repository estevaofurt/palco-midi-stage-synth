/**
 * Stage D wood and longitudinal *IN-SAMPLE*, numeric-only Iowa diagnostic.
 * Downloads are handled separately by a SHA256-verifying CI workflow. Never
 * stores source PCM, bundled IRs or reference WAVs in repo/artifacts.
 */
import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {HybridPianoEngine as Stable} from '../physical-piano-hybrid-v127.js';
import {HybridPianoEngine as Experimental} from '../physical-piano-hybrid.js';
import {measurePianoNote} from '../tests/piano_acoustic_metrics.mjs';
import {decodeF32le,locateAttack,measureEarlyPartials} from './analyze_reference_audio.mjs';
import {transientEnvelope} from './diagnose_piano_bass_envelope.mjs';
const RATE=48000,BLOCK=128,SECS=1.7,FRAMES=RATE*SECS;
const STUDIES=[
 ['stable',Stable,'off'],
 ['wood',Experimental,'wood'],
 ['longitudinal',Experimental,'longitudinal'],
 ['combined',Experimental,'combined']
];
function render(Model,study,key,velocity){
 const piano=Model===Stable?new Model(RATE,'eco'):new Model(RATE,'eco',study);
 piano.noteOn({id:1,key,speed:velocity/127,hardness:.5,brightness:.5,
   character:'american',send:0});
 const L=new Float32Array(BLOCK),R=new Float32Array(BLOCK),out=new Float32Array(FRAMES);
 for(let pos=0;pos<FRAMES;pos+=BLOCK){
   const n=Math.min(BLOCK,FRAMES-pos);
   piano.render(L,R,null,n);
   for(let i=0;i<n;i++){
     const v=(L[i]+R[i])*.5;
     if(!Number.isFinite(v)||Math.abs(v)>=.97)
       throw Error('invalid output '+study+'/'+key);
     out[pos+i]=v;
   }
 }
 return out;
}
function error(reference,candidate,minDb,fromEarly){
 const a=fromEarly?reference.harmonics:reference.harmonics;
 const b=fromEarly?candidate.harmonics:candidate.harmonics;
 const pairs=[];
 for(const ra of a){
   if(ra.n<2||ra.n>8||!Number.isFinite(ra.relativeDb)||ra.relativeDb<minDb)continue;
   const rb=b.find(x=>x.n===ra.n);
   if(!rb||!Number.isFinite(rb.relativeDb))continue;
   pairs.push(Math.abs(ra.relativeDb-rb.relativeDb));
 }
 return pairs.length?pairs.reduce((s,n)=>s+n,0)/pairs.length:null;
}
const mean=x=>x.length?x.reduce((s,v)=>s+v,0)/x.length:null;
function analyze(manifest){
 if(manifest.notes?.length!==15)throw Error('expect exactly 15 original piano notes');
 const rows=[];
 for(const e of manifest.notes){
   if(!/^[a-f0-9]{64}$/.test(e.sha256))throw Error('source hash not verified');
   const original=decodeF32le(readFileSync(e.pcmPath));
   const onset=locateAttack(original,RATE);
   const from=Math.round(onset*RATE);
   if(from+FRAMES>original.length)throw Error('source too short');
   const ref=original.slice(from,from+FRAMES);
   const rv=measurePianoNote(ref,{sampleRate:RATE,key:e.key});
   const earlyRef=measureEarlyPartials(ref,e.key);
   const waveformRef=transientEnvelope(ref);
   const velocity={pp:32,mf:80,ff:120}[e.dynamic];
   if(!velocity)throw Error('bad dynamic '+e.dynamic);
   const results={};
   for(const [name,Model,study] of STUDIES){
     const samples=render(Model,study,e.key,velocity);
     const mv=measurePianoNote(samples,{sampleRate:RATE,key:e.key});
     const early=measureEarlyPartials(samples,e.key);
     const shape=transientEnvelope(samples);
     results[name]={
       shortSpectralErrorDb:error(earlyRef,early,-34,true),
       sustainedSpectralErrorDb:error(rv,mv,-30,false),
       attack0to12DeltaDb:shape.envelopeDb[0]-waveformRef.envelopeDb[0],
       rms:mv.rms,peak:mv.peak
     };
   }
   rows.push({key:e.key,dynamic:e.dynamic,originalSha256:e.sha256,results});
 }
 const summary={};
 for(const [name] of STUDIES){
   const early=rows.map(r=>r.results[name].shortSpectralErrorDb).filter(Number.isFinite);
   const late=rows.map(r=>r.results[name].sustainedSpectralErrorDb).filter(Number.isFinite);
   const bass=rows.filter(r=>r.key===36||r.key===48);
   summary[name]={
     spectralInitialMeanAbsDb:mean(early),
     spectralSustainMeanAbsDb:mean(late),
     bass0to12msMeanAbsDb:mean(bass.map(r=>Math.abs(r.results[name].attack0to12DeltaDb)))
   };
 }
 return {schema:'stage-d-bass-wood-comparison-iowa-numeric-v1',
   source:'University of Iowa Steinway B originals: 15 AIFF SHA256 verified by workflow',
   limits:'IN-SAMPLE 15 known anchor notes; recording includes microphone/room, pp/mf/ff not calibrated as MIDI. No perceptual or soundboard-impedance inference.',
   modes:STUDIES.map(x=>x[0]),summary,rows};
}
if(process.argv[1]&&fileURLToPath(import.meta.url)===process.argv[1]){
 const manifest=process.argv[2],output=process.argv[3];
 if(!manifest||!output)throw Error('manifest.json + output.json required');
 const data=analyze(JSON.parse(readFileSync(manifest,'utf8')));
 writeFileSync(output,JSON.stringify(data,null,2)+'\n');
 for(const [name,metrics] of Object.entries(data.summary))
  console.log('WOOD_IOWA '+name+' '+JSON.stringify(metrics));
 console.log('EXPLORATORY ONLY: do not infer piano realism from spectral averages.');
}
