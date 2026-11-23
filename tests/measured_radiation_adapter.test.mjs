import test from 'node:test';
import assert from 'node:assert/strict';
import {MeasuredRadiationAdapter,CalibratedPassivePianoResearchChain}
 from '../research/measured-radiation-adapter.mjs';

// ALL metadata below are test fixtures. There is no real authorized IR.
const syntheticMetadata={
 inputUnit:'m/s2',outputUnit:'Pa',transferUnit:'Pa/(m/s2)',
 measured:true,sourceType:'synchronized-calibrated-bridge-and-microphone',
 sourceId:'SYNTHETIC-FIXTURE-NOT-A-REAL-MEASUREMENT',
 rightsDocumentId:'SYNTHETIC-UNIT-TEST-ONLY',
 commercialUseAuthorized:true,sampleRate:48000,alignmentSamples:0,
 bridgeCoordinateCalibrated:true
};
const newAdapter=(left=[.3,.2,-.1],right=[.4,.1,.05])=>
 new MeasuredRadiationAdapter({sampleRate:48000,
 impulseLeft:Float64Array.from(left),impulseRight:Float64Array.from(right),
 metadata:syntheticMetadata});

test('no transfer without explicit provenance and calibrated sensor units',()=>{
 const input={sampleRate:48000,impulseLeft:Float64Array.of(1),
 impulseRight:Float64Array.of(1),metadata:{...syntheticMetadata}};
 for(const delta of [
  {measured:false},{sourceType:'spectral-estimate-unvalidated'},
  {inputUnit:'velocity'},{outputUnit:'arbitrary'},
  {commercialUseAuthorized:false},{rightsDocumentId:''},
  {sourceId:''},{sampleRate:44100},{alignmentSamples:-1}
 ]){
  assert.throws(()=>new MeasuredRadiationAdapter({...input,metadata:{...input.metadata,...delta}}),
    RangeError);
 }
 assert.throws(()=>new MeasuredRadiationAdapter({...input,impulseLeft:Float64Array.of(NaN)}));
 assert.throws(()=>new MeasuredRadiationAdapter({...input,impulseRight:Float64Array.of(.4,.3)}));
 assert.throws(()=>new CalibratedPassivePianoResearchChain({
  sampleRate:48000,measuredImpulseLeft:Float64Array.of(1),
  measuredImpulseRight:Float64Array.of(1),
  metadata:{...syntheticMetadata,bridgeCoordinateCalibrated:false}}),RangeError);
});

test('FIR sample response is causal acceleration-to-pressure with stereo phase signs',()=>{
 const t=newAdapter();
 const l=new Float64Array(8),r=new Float64Array(8);
 const v=new Float64Array([1/48000,1/48000,1/48000,1/48000,1/48000,1/48000,1/48000,1/48000]);
 t.render(v,l,r);
 // acceleration is [1, 0,...], so the output equals impulse taps.
 for(let i=0;i<8;i++){
  assert.ok(Math.abs(l[i]-(i<3?[.3,.2,-.1][i]:0))<1e-12);
  assert.ok(Math.abs(r[i]-(i<3?[.4,.1,.05][i]:0))<1e-12);
 }
 assert.equal(t.samples,8);
});

test('block convolution and offline step are bitwise-identical across discontinuities',()=>{
 const a=newAdapter(),b=newAdapter(),l=new Float64Array(256),r=new Float64Array(256);
 const vel=new Float64Array(256);
 for(let i=0;i<256;i++)vel[i]=.001*Math.sin(i*.097);
 a.render(vel,l,r);
 for(let i=0;i<256;i++){
  const x=b.step(vel[i]);
  assert.equal(l[i],x.left);
  assert.equal(r[i],x.right);
 }
 a.reset();b.reset();
 assert.equal(a.samples,0);
 assert.deepEqual(a.history,new Float64Array(3));
 assert.throws(()=>a.render(vel,l,l),RangeError);
 assert.throws(()=>a.renderBlock(vel,l,r,300),RangeError);
});

test('synthesized energy stays mechanical; synthetic radiation is a test fixture only',()=>{
 const chain=new CalibratedPassivePianoResearchChain({
  sampleRate:48000,coupling:.12,
  measuredImpulseLeft:Float64Array.of(.0002,.0001),
  measuredImpulseRight:Float64Array.of(.0003,-.00005),
  metadata:syntheticMetadata
 });
 chain.noteOn(36,{velocity:85,peakForce:90});
 chain.setSustain(127);
 const left=new Float64Array(128),right=new Float64Array(128);
 let peak=0;
 for(let i=0;i<35;i++){
  chain.render(left,right);
  for(let j=0;j<128;j++){
   assert.ok(Number.isFinite(left[j])&&Number.isFinite(right[j]));
   peak=Math.max(peak,Math.abs(left[j]),Math.abs(right[j]));
  }
 }
 assert.ok(peak>1e-12,'chain should radiate synthetic FIR response in test');
 assert.ok(Math.abs(chain.mechanics.energyBalanceError())<1e-7);
 chain.noteOff(36);chain.setSustain(0);chain.reset();
 assert.equal(chain.mechanics.bridge.energy(),0);
 assert.equal(chain.radiation.samples,0);
});

test('zero bridge velocity never generates output without a signal source',()=>{
 const a=newAdapter(),v=new Float64Array(512),l=new Float64Array(512),r=new Float64Array(512);
 a.render(v,l,r);
 assert.ok(l.every(x=>x===0));assert.ok(r.every(x=>x===0));
});
