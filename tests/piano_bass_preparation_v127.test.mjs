import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {
 RATE,DURATION,BASS_BINS,transientEnvelope,partialTrajectories,
 renderStageD,diagnoseOne
} from '../scripts/diagnose_piano_bass_envelope.mjs';

const make=(scale=1,kind='slow')=>{
  const frames=Math.ceil(DURATION*RATE),out=new Float32Array(frames);
  for(let i=0;i<frames;i++){
    const t=i/RATE;
    const envelope=kind==='slow'?(1-Math.exp(-t*37)):Math.exp(-t*19);
    out[i]=scale*.12*Math.exp(-t*.75)*envelope*(
      Math.sin(2*Math.PI*130.81*t)+.28*Math.sin(2*Math.PI*261.62*t));
  }
  return out;
};

test('analysis uses a separate true first-12ms broadband bin, not a mislabelled FFT',()=>{
 assert.deepEqual(BASS_BINS[0],[0,.012]);
 assert.deepEqual(BASS_BINS[1],[.012,.036]);
 assert.equal(BASS_BINS.length,7);
 const v=transientEnvelope(make());
 assert.equal(v.envelopeDb.length,7);
 assert.equal(v.highpass900HzDb.length,7);
 assert.ok(v.envelopeDb.every(Number.isFinite));
 assert.ok(v.highpass900HzDb.every(Number.isFinite));
});

test('level-independent envelope compares note shape without mistaking microphone gain for timbre',()=>{
 const a=transientEnvelope(make(1));
 const b=transientEnvelope(make(.07));
 a.envelopeDb.forEach((x,i)=>assert.ok(Math.abs(x-b.envelopeDb[i])<.04));
 a.highpass900HzDb.forEach((x,i)=>assert.ok(Math.abs(x-b.highpass900HzDb[i])<.04));
});

test('first 12ms detects a sharp strike separately from a slowly rising note',()=>{
 const slow=transientEnvelope(make(1,'slow'));
 const impulse=transientEnvelope(make(1,'fast'));
 assert.ok(slow.envelopeDb[0]<impulse.envelopeDb[0]-2,
   'transient must distinguish instantaneous and gradual excitation');
});

test('harmonic trajectories contain independently timed 171ms windows',()=>{
 const pcm=make();
 const series=partialTrajectories(pcm,48);
 assert.equal(series.length,4);
 assert.equal(series[0].startSeconds,.020);
 assert.ok(Math.abs(series[0].spanSeconds-8192/RATE)<1e-10);
 assert.equal(series[3].startSeconds,.850);
 assert.equal(series[0].harmonics[0].n,1);
 assert.equal(series[0].harmonics.length,8);
});

test('Stage D sample generation remains finite for bass and medium-high guardrails',()=>{
 for(const key of [36,48,60,72,84]){
   const pcm=renderStageD(key,80,'american');
   assert.equal(pcm.length,Math.ceil(DURATION*RATE));
   assert.ok(pcm.every(Number.isFinite));
   const profile=transientEnvelope(pcm);
   assert.ok(profile.envelopeDb.every(Number.isFinite));
 }
});

test('invalid source metadata cannot be silently treated as measured evidence',()=>{
 assert.throws(()=>diagnoseOne({key:36,sha256:'not-hash'}),/SHA256/);
 assert.throws(()=>diagnoseOne({key:200,sha256:'a'.repeat(64)}),/invalid note/);
 assert.throws(()=>transientEnvelope(new Float32Array(200)),/too short/);
});

test('diagnostic is research-only and does not change stage D sound files',()=>{
 const file=readFileSync(new URL('../scripts/diagnose_piano_bass_envelope.mjs',import.meta.url),'utf8');
 assert.match(file,/dspModified:false/);
 assert.doesNotMatch(file,/createWriteStream|writeFileSync\(['"]physical-piano-hybrid|new AudioWorkletNode/);
});
