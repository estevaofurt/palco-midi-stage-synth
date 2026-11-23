import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {ReactiveFeltDistributedPianoE33}
 from '../research/reactive-felt-distributed-e33.mjs';

function run({velocity=2,panels=8,rate=48000,seconds=.035,other={}}={}){
 const m=new ReactiveFeltDistributedPianoE33({
  sampleRate:rate,hammerVelocityMps:velocity,panelModes:panels,
  ...other
 });
 for(let i=0;i<Math.round(rate*seconds);i++)m.step();
 return m;
}

test('reactive felt transfers energy into 88-string shared 8-mode plate',()=>{
 const m=run();
 assert.equal(m.piano.n,592);
 assert.equal(m.piano.panelModes,8);
 assert.ok(m.peakForce>0);
 assert.ok(m.contactSamples>0);
 assert.ok(m.piano.externalWork>0);
 assert.ok(m.piano.energy()>0);
 assert.ok(m.piano.dissipated>0);
 assert.ok(Array.from(m.piano.panelVelocity).some(v=>Math.abs(v)>0));
 assert.ok(Math.abs(m.relativeEnergyResidual())<1e-7,
  'full physical energy residual '+m.relativeEnergyResidual());
});

test('contact energy closes with 2 and 8 plate modes',()=>{
 for(const panels of [2,8]){
  const m=run({panels,seconds:.07});
  assert.ok(m.peakForce>0);
  assert.ok(m.piano.energy()>0);
  assert.ok(Math.abs(m.relativeEnergyResidual())<1e-7);
 }
});

test('stronger hammer yields more peak contact force, zero force without motion',()=>{
 const soft=run({velocity:1});
 const hard=run({velocity:3});
 const quiet=run({velocity:0,seconds:.01});
 assert.ok(hard.peakForce>soft.peakForce*1.4);
 assert.equal(quiet.peakForce,0);
 assert.equal(quiet.piano.energy(),0);
 assert.equal(quiet.relativeEnergyResidual(),0);
});

test('distributed reactive contact conserves energy after noteOff and damper motion',()=>{
 const m=new ReactiveFeltDistributedPianoE33({
  sampleRate:48000,key:48,hammerVelocityMps:2,sustain:127
 });
 for(let i=0;i<3400;i++){
  if(i===800)m.noteOff();
  if(i===1400)m.setSustain(0);
  m.step();
 }
 assert.ok(m.piano.dissipated>0);
 assert.ok(Math.abs(m.relativeEnergyResidual())<1e-7);
});

test('multi-panel hammer compliance predicts real displacement for first force step',()=>{
 const m=new ReactiveFeltDistributedPianoE33({hammerGapM:0});
 const p=m.piano;
 const before=m.predictor();
 m.step();
 assert.ok(m.force>0);
 const current=m.stringAtHammer();
 assert.ok(Math.abs(current-(before.qFree+before.compliance*m.force))<1e-13);
 const contactGradient=m.gradient(
  -before.qOld,m.hammerX-current
 );
 assert.ok(Math.abs(m.force-contactGradient)<1e-8*Math.max(1,m.force));
 assert.ok(Math.abs(m.relativeEnergyResidual())<1e-8);
 assert.equal(p.panelModes,8);
});

test('identical input is deterministic at two physics sample rates',()=>{
 for(const rate of [44100,96000]){
  const first=run({rate,seconds:.012});
  const second=run({rate,seconds:.012});
  assert.equal(first.peakForce,second.peakForce);
  assert.equal(first.piano.energy(),second.piano.energy());
  assert.ok(Math.abs(first.relativeEnergyResidual())<1e-7);
 }
});

test('malformed hammer parameters and sound recording dependencies fail closed',()=>{
 for(const x of [
  {key:500},{hammerMassKg:0},{hammerVelocityMps:-1},
  {feltExponent:-1},{panelModes:12},{hammerGapM:-1},{sampleRate:1000}
 ])assert.throws(()=>new ReactiveFeltDistributedPianoE33(x),RangeError);
 const code=readFileSync(new URL('../research/reactive-felt-distributed-e33.mjs',import.meta.url),'utf8');
 assert.doesNotMatch(code,/^import .*(sample-library|sf2-reader|piano-bank|\.wav)/gm);
 assert.doesNotMatch(code,/\bdecodeAudioData\s*\(/);
});
