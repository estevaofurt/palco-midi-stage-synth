import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NonlinearFeltContactPair}
 from '../research/nonlinear-felt-contact-e31.mjs';

function run(velocity,loss=0,samples=9600){
 const model=new NonlinearFeltContactPair({
  sampleRate:96000,hammerInitialVelocityMps:velocity,
  stringLossRate:loss
 });
 for(let i=0;i<samples;i++)model.step();
 return model;
}
test('unilateral felt contact cannot pull a separated string',()=>{
 const model=run(0);
 assert.equal(model.contactSamples,0);
 assert.equal(model.maxForceN,0);
 assert.equal(model.energy(),0);
 assert.equal(model.balanceRelativeError(),0);
});
test('nonlinear compression responds to hammer speed without fixed force pulses',()=>{
 const slow=run(1),fast=run(3);
 assert.ok(slow.maxForceN>0);
 assert.ok(fast.maxForceN>slow.maxForceN*2,
   'faster hammer must generate more than linearized force');
 assert.ok(fast.contactSamples<slow.contactSamples,
   'harder felt compression shortens first contact in this test fixture');
 assert.ok(fast.contactSamples>20&&slow.contactSamples>30);
});
test('conservative nonlinear hammer+string pair nearly conserves energy',()=>{
 const model=run(2,0,24000);
 assert.ok(model.energy()>0);
 assert.equal(model.dissipatedJ,0);
 assert.ok(Math.abs(model.balanceRelativeError())<.001,
   'energy error = '+model.balanceRelativeError());
});
test('positive string losses dissipate energy without creation',()=>{
 const model=run(2,.7,24000);
 assert.ok(model.dissipatedJ>0);
 assert.ok(model.energy()<model.initialEnergyJ);
 assert.ok(Math.abs(model.balanceRelativeError())<.002);
});
test('reject unphysical contact parameters and remain sample-free',()=>{
 for(const opts of [
  {hammerMassKg:0},{stringEffectiveMassKg:-1},
  {feltStiffness:0},{feltExponent:0},
  {hammerGapM:-.1},{hammerInitialVelocityMps:NaN},
  {stringLossRate:-1},{sampleRate:8000}
 ])assert.throws(()=>new NonlinearFeltContactPair(opts),RangeError);
 const source=readFileSync(new URL('../research/nonlinear-felt-contact-e31.mjs',import.meta.url),'utf8');
 assert.doesNotMatch(source,/^import .*\.(wav|sf2)|sample-library|piano-bank|decodeAudioData/gm);
});
