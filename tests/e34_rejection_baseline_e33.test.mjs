import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {ReactiveFeltDistributedPianoE33}
 from '../research/reactive-felt-distributed-e33.mjs';

function physicalSequence(options={}){
 const model=new ReactiveFeltDistributedPianoE33({
  sampleRate:24000,key:48,hammerVelocityMps:2, ...options
 });
 const peak=[];
 for(let i=0;i<420;i++){
  model.step();
  if(i%10===0)peak.push(model.piano.panelVelocity[0]);
 }
 return {
  peak,
  hammerForce:model.peakForce,
  energy:model.piano.energy(),
  residual:model.relativeEnergyResidual()
 };
}
test('E3.3 8-mode / no-hardening baseline survives E3.4 opt-in exactly',()=>{
 const a=physicalSequence();
 const b=physicalSequence({panelModes:8,feltHardeningRatio:0,
  feltHardeningThresholdM:.00016});
 assert.deepEqual(a,b);
 assert.ok(Math.abs(a.residual)<1e-7);
});
test('rejected hard 16-mode E3.4 is not same signal as E3.3 baseline',()=>{
 const old=physicalSequence();
 const rejected=physicalSequence({panelModes:16,feltHardeningRatio:12});
 assert.notDeepEqual(old,rejected);
 assert.ok(Math.abs(rejected.residual)<1e-7);
 assert.ok(rejected.hammerForce>old.hammerForce);
});
test('audio comparison uses models and equations, not a wav recording or convolution',()=>{
 const code=readFileSync(new URL('../scripts/audit_e33_vs_e34_rejected_timbre.mjs',
   import.meta.url),'utf8');
 assert.match(code,/E34_rejected/);
 assert.match(code,/panelModes:16,feltHardeningRatio:12/);
 assert.match(code,/panelModes:8,feltHardeningRatio:0/);
 assert.doesNotMatch(code,/^import .*(sample-library|piano-bank|sf2-reader|\.wav)/gm);
 assert.doesNotMatch(code,/createConvolver|decodeAudioData|readFileSync\s*\(/);
});
