import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {ReactiveFeltDistributedPianoE33}
 from '../research/reactive-felt-distributed-e33.mjs';
import {PassiveDistributedSoundboardE33}
 from '../research/passive-distributed-soundboard-e33.mjs';
import {AnalyticSpatialPlateRadiatorE33}
 from '../research/analytic-spatial-plate-radiation-e33.mjs';

const simulate=({
 speed=2.8,ratio=0,panels=8,rate=24000,frames=1600
}={})=>{
 const piano=new ReactiveFeltDistributedPianoE33({
  sampleRate:rate,key:48,hammerVelocityMps:speed,
  feltHardeningRatio:ratio,feltHardeningThresholdM:.00016,
  panelModes:panels,sustain:127
 });
 let hiEnergy=0;
 for(let i=0;i<frames;i++){
  const modes=piano.step();
  if(panels>8)for(let j=8;j<panels;j++)
   hiEnergy+=modes[j]*modes[j];
 }
 return {piano,hiEnergy};
};

test('E3.3 default remains eight passive modes and NO felt hardening',()=>{
 const {piano}=simulate({speed:2});
 assert.equal(piano.piano.panelModes,8);
 assert.equal(piano.hardeningRatio,0);
 assert.equal(piano.hardeningThresholdM,.00016);
 assert.equal(piano.forceAtCompression(.00005),
   piano.k*.00005**piano.exponent);
 assert.ok(Math.abs(piano.relativeEnergyResidual())<1e-7);
});

test('physical felt compaction is a convex energy potential, not a PCM click',()=>{
 const base=new ReactiveFeltDistributedPianoE33({feltHardeningRatio:0});
 const hard=new ReactiveFeltDistributedPianoE33({feltHardeningRatio:8});
 const knee=hard.hardeningThresholdM;
 assert.equal(hard.potential(knee*.8),base.potential(knee*.8));
 assert.equal(hard.forceAtCompression(knee*.8),base.forceAtCompression(knee*.8));
 assert.ok(hard.potential(knee*1.8)>base.potential(knee*1.8));
 assert.ok(hard.forceAtCompression(knee*1.8)>base.forceAtCompression(knee*1.8));
 for(const [start,end] of [
  [-.00002,-.00001],[-.00001,.00005],[.00006,.00020],
  [.00015,.00025],[.00025,.00038]
 ]){
  const F=hard.gradient(start,end);
  const work=F*(end-start);
  const dU=hard.potential(end)-hard.potential(start);
  assert.ok(F>=0);
  assert.ok(Math.abs(work-dU)<1e-13,
   'nonreciprocal compression work: '+F);
 }
});

test('stronger felt compaction changes genuine hammer reaction without extra energy',()=>{
 const base=simulate({ratio:0,frames:2200}).piano;
 const hard=simulate({ratio:8,frames:2200}).piano;
 assert.ok(base.peakForce>0&&hard.peakForce>0);
 assert.ok(hard.peakForce>base.peakForce,
  'denser felt must modify the physical contact impact force');
 assert.ok(Math.abs(base.relativeEnergyResidual())<1e-7);
 assert.ok(Math.abs(hard.relativeEnergyResidual())<1e-7);
 assert.ok(hard.piano.externalWork>0);
});

test('16-mode board has physically active extra modes and still conserves energy',()=>{
 const {piano,hiEnergy}=simulate({panels:16,ratio:8,frames:1600});
 assert.equal(piano.piano.panelModes,16);
 assert.equal(piano.piano.panelVelocity.length,16);
 assert.equal(piano.piano.boardSize,17);
 assert.equal(piano.piano.panelFrequencies.length,16);
 assert.ok(piano.piano.panelFrequencies[15]>1000,
  'added spatial bending resonances must extend bandwidth above original eight');
 assert.ok(hiEnergy>0,'high plate modes must be dynamically excited, not mixed oscillator audio');
 assert.ok(piano.piano.energy()>0);
 assert.ok(Math.abs(piano.relativeEnergyResidual())<1e-7);
 const rad=new AnalyticSpatialPlateRadiatorE33({
  sampleRate:24000,shapes:piano.piano.panelShapes
 });
 assert.equal(rad.modeCount,16);
 rad.step(piano.piano.panelVelocity);
 assert.ok(Number.isFinite(rad.left)&&Number.isFinite(rad.right));
});

test('more plate modes remain opt-in; inappropriate mode counts fail closed',()=>{
 assert.equal(new PassiveDistributedSoundboardE33().panelModes,8);
 assert.throws(()=>new PassiveDistributedSoundboardE33({panelModes:17}),RangeError);
 assert.throws(()=>new ReactiveFeltDistributedPianoE33({feltHardeningRatio:-1}),RangeError);
 assert.throws(()=>new ReactiveFeltDistributedPianoE33({feltHardeningRatio:33}),RangeError);
 assert.throws(()=>new ReactiveFeltDistributedPianoE33({feltHardeningThresholdM:-1}),RangeError);
 assert.throws(()=>new ReactiveFeltDistributedPianoE33({feltHardeningThresholdM:.01}),RangeError);
 assert.throws(()=>new AnalyticSpatialPlateRadiatorE33({
  shapes:Array.from({length:17},()=>[1,1])
 }),RangeError);
});

test('E3.4 sound remains purely mechanical/acoustic; no sampled impact layer',()=>{
 for(const f of [
  '../research/reactive-felt-distributed-e33.mjs',
  '../research/passive-distributed-soundboard-e33.mjs',
  '../research/analytic-spatial-plate-radiation-e33.mjs'
 ]){
  const source=readFileSync(new URL(f,import.meta.url),'utf8');
  assert.doesNotMatch(source,/^import .*\.(wav|sf2)|^import .*(sample-library|piano-bank)|createConvolver|decodeAudioData/gm);
 }
});
