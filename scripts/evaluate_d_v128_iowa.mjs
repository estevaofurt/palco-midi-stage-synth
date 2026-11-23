/**
 * Numeric-only external acoustic check of Stage D v1.12.7 vs isolated
 * bass-unison candidate. Reads original downloaded Iowa C2/C3 mf PCM
 * from ephemeral runner after original-source hash/byte verification.
 * No reference audio gets copied into Git, WAV artifacts, nor release.
 *
 * Usage:
 *  node scripts/evaluate_d_v128_iowa.mjs /tmp/iowa/manifest.json /tmp/iowa/result.json
 */
import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {HybridPianoEngine as V127} from '../physical-piano-hybrid-v127.mjs';
import {HybridPianoEngine as V128} from '../physical-piano-hybrid-v128-candidate.mjs';
import {decodeF32le,locateAttack} from './analyze_reference_audio.mjs';
import {transientEnvelope,partialTrajectories} from './diagnose_piano_bass_envelope.mjs';
const RATE=48000,DURATION=1.65,BLOCK=128,FRAMES=Math.ceil(DURATION*RATE);
const expected=new Map(JSON.parse(readFileSync(new URL('../research/commercial_audio/iowa_steinway_b_verified_original_sha256.json',import.meta.url))).items.map(x=>[x.id,x]));
function render(Model,key,velocity=80){
 const e=new Model(RATE,'studio'),o=new Float32Array(FRAMES),l=new Float32Array(BLOCK),r=new Float32Array(BLOCK);
 e.noteOn({id:1,key,speed:velocity/127,hardness:.55,brightness:.5,character:'american',send:0});
 for(let p=0;p<FRAMES;p+=BLOCK){
  const n=Math.min(BLOCK,FRAMES-p);
  e.render(l,r,null,n);
  for(let j=0;j<n;j++)o[p+j]=(l[j]+r[j])*.5;
 }
 return o;
}
function absoluteError(a,b){return Math.abs(a-b)}
function partialError(ref,other){
 const out=[];
 for(let i=0;i<ref.length;i++){
  const a=ref[i],b=other[i];
  if(a.startSeconds!==b.startSeconds)throw Error('not aligned windows');
  const stable=[];
  for(let n=1;n<a.harmonics.length;n++){
   const x=a.harmonics[n],y=b.harmonics[n];
   if(x.n!==y.n)throw Error('not aligned partial');
   if(x.relativeDb>-29&&Number.isFinite(y.relativeDb))
    stable.push(absoluteError(x.relativeDb,y.relativeDb));
  }
  out.push({startSeconds:a.startSeconds,windowDurationSeconds:a.spanSeconds,
   validPartials:stable.length,
   meanAbsoluteRelativeDb:stable.length?Number((stable.reduce((s,x)=>s+x,0)/stable.length).toFixed(3)):null});
 }
 return out;
}
const manifest=JSON.parse(readFileSync(process.argv[2]||'','utf8'));
const reportFile=process.argv[3];
if(!reportFile||manifest.notes?.length!==2)throw Error('expected Iowa original C2/C3 mf pair and output path');
const rows=[];
for(const note of manifest.notes){
 if(note.dynamic!=='mf'||![36,48].includes(note.key))throw Error('only C2/C3 mf accepted');
 const pitch=note.key===36?'c2':'c3';
 const verified=expected.get('iowa-steinway-b-'+pitch+'-mf');
 if(!verified||note.sha256!==verified.sha256||note.bytes!==verified.bytes||
    note.originalRate!==44100||note.originalChannels!==2||
    note.originalFormat!=='pcm_s16be')
   throw Error('original Iowa provenance mismatch '+pitch);
 const audio=decodeF32le(readFileSync(note.pcmPath));
 const onset=locateAttack(audio,RATE),start=Math.round(onset*RATE);
 if(start+FRAMES>audio.length)throw Error('original recording too short');
 const ref=audio.slice(start,start+FRAMES);
 const old=render(V127,note.key),newV=render(V128,note.key);
 const sourceEnvelope=transientEnvelope(ref);
 const sourcePartials=partialTrajectories(ref,note.key);
 const oldEnvelope=transientEnvelope(old),newEnvelope=transientEnvelope(newV);
 const oldPartial=partialTrajectories(old,note.key),newPartial=partialTrajectories(newV,note.key);
 const errors={};
 for(const [name,env,parts] of [['v127',oldEnvelope,oldPartial],['v128',newEnvelope,newPartial]]){
  errors[name]={
   first12msMeanAbsDb:Math.abs(env.envelopeDb[0]-sourceEnvelope.envelopeDb[0]),
   early12to36msMeanAbsDb:Math.abs(env.envelopeDb[1]-sourceEnvelope.envelopeDb[1]),
   late900to1400msMeanAbsDb:Math.abs(env.envelopeDb[6]-sourceEnvelope.envelopeDb[6]),
   harmonicWindows:partialError(sourcePartials,parts)
  };
 }
 const change={
   first12msDb:Number((errors.v128.first12msMeanAbsDb-errors.v127.first12msMeanAbsDb).toFixed(3)),
   early12to36msDb:Number((errors.v128.early12to36msMeanAbsDb-errors.v127.early12to36msMeanAbsDb).toFixed(3)),
   late900to1400msDb:Number((errors.v128.late900to1400msMeanAbsDb-errors.v127.late900to1400msMeanAbsDb).toFixed(3)),
   harmonicWindows:errors.v128.harmonicWindows.map((w,i)=>({
    time:w.startSeconds,comparableHarmonics:w.validPartials,
    deltaMeanAbsDb:w.meanAbsoluteRelativeDb===null||errors.v127.harmonicWindows[i].meanAbsoluteRelativeDb===null?
      null:Number((w.meanAbsoluteRelativeDb-errors.v127.harmonicWindows[i].meanAbsoluteRelativeDb).toFixed(3))
   }))
 };
 rows.push({
  key:note.key,dynamic:'mf',
  originalSHA256:note.sha256,originalSizeBytes:note.bytes,
  onsetSeconds:onset,originalIsMeasuredHammerForce:false,
  separatePianoMicrophonesAndRoomUncontrolled:true,
  sameUncalibratedNominalMidiVelocity:80,
  errors,deltaErrorCandidateMinusV127:change
 });
 console.log('IOWA_STAGED_V128 '+JSON.stringify({key:note.key,change,originalSha:note.sha256}));
}
writeFileSync(reportFile,JSON.stringify({schema:'stage-original-iowa-v128-vs-v127-2-notes-v1',
 originalSamplesEmbedded:false,normalization:'each signal to its own 100–220 ms for temporal envelope only',
 spectralNote:'harmonic 8192-point Hann ≈171ms; NOT first 12ms transient spectrum; source mic/room included; scores in-sample for v127 calibration',
 verdict:'numeric diagnostics only, not perceptual approval',
 rows},null,2)+'\n');
