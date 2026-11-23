import test from 'node:test';
import assert from 'node:assert/strict';
import {estimateBridgeMobilityH1,estimateDocumentedBridgeMobility}
 from '../research/bridge-mobility-h1.mjs';

const RATE=48000;
function fixture(length=32768,{gain=.002,delay=0}={}){
 const force=new Float64Array(length),velocity=new Float64Array(length);
 let state=0x3a271b95;
 for(let i=0;i<length;i++){
  state^=state<<13;state^=state>>>17;state^=state<<5;
  force[i]=state/2147483648;
  if(i>=delay)velocity[i]=gain*force[i-delay];
 }
 return {force,velocity};
}
function binOf(s,f){return s.spectrum[Math.round(f/s.frequencyResolutionHz)]}
const documentary={
 inputUnit:'N',outputUnit:'m/s',transferUnit:'(m/s)/N',
 forceLocation:'bridge',velocityLocation:'same-bridge-point',
 synchronized:true,calibrated:true,
 sourceType:'instrumented-bridge-force-velocity',
 sourceId:'SYNTHETIC-FIXTURE-NOT-MEASURED',
 rightsDocumentId:'TEST-ONLY-NOT-A-LICENSE',
 commercialUseAuthorized:true,sampleRate:RATE
};

test('calibrated-mobility contract refuses force measured on key/hammer instead of bridge',()=>{
 const {force,velocity}=fixture(10000);
 for(const override of [
  {forceLocation:'key-bed'}, {velocityLocation:'microphone'},
  {inputUnit:'m/s2'},{outputUnit:'Pa'},{transferUnit:'Pa/N'},
  {sourceType:'key-hammer-force'}, {synchronized:false},
  {calibrated:false},{sourceId:''},{rightsDocumentId:''},
  {commercialUseAuthorized:false},{sampleRate:44100}
 ]){
  assert.throws(()=>estimateDocumentedBridgeMobility({
   force,velocity,sampleRate:RATE,metadata:{...documentary,...override}
  }),RangeError);
 }
 assert.throws(()=>estimateDocumentedBridgeMobility({force,velocity,sampleRate:RATE}),RangeError);
});
test('H1 recovers synthetic flat driving-point mobility magnitude and phase',()=>{
 const {force,velocity}=fixture(32768);
 const s=estimateBridgeMobilityH1({
  bridgeForce:force,bridgeVelocity:velocity,sampleRate:RATE,
  windowSize:1024,coherenceThreshold:.95
 });
 assert.equal(s.inputUnit,'N');assert.equal(s.outputUnit,'m/s');
 assert.equal(s.transferUnit,'(m/s)/N');assert.ok(s.validBins>400);
 for(const f of [375,1406.25,3750,9000]){
  const b=binOf(s,f);
  assert.ok(b.valid,'valid bin '+f);
  assert.ok(Math.abs(b.magnitude-.002)<1e-10,'mobility magnitude '+f+': '+b.magnitude);
  assert.ok(Math.abs(b.phaseRadians)<1e-9,'phase '+f+': '+b.phaseRadians);
  assert.ok(b.coherence>.9999,'coherence '+f);
 }
});
test('H1 delay shifts phase, and magnitude remains near source gain',()=>{
 const {force,velocity}=fixture(32768,{gain:.002,delay:3});
 const s=estimateBridgeMobilityH1({
  bridgeForce:force,bridgeVelocity:velocity,sampleRate:RATE,
  windowSize:2048,relativeInputFloor:1e-9
 });
 const f=1500,b=binOf(s,f);
 assert.ok(b.valid);
 assert.ok(Math.abs(b.magnitude-.002)<.00006);
 const expected=-2*Math.PI*b.frequencyHz*3/RATE;
 assert.ok(Math.abs(b.phaseRadians-expected)<.05,
  'phase should include ~3 sample delay: '+b.phaseRadians+' vs '+expected);
 assert.ok(b.coherence>.97);
});
test('documented wrapper returns the same mathematical estimate with bounded metadata only',()=>{
 const {force,velocity}=fixture(8192,{delay:0});
 const opts={windowSize:512,coherenceThreshold:.8};
 const a=estimateDocumentedBridgeMobility({force,velocity,sampleRate:RATE,
  metadata:documentary,...opts});
 const b=estimateBridgeMobilityH1({bridgeForce:force,bridgeVelocity:velocity,
  sampleRate:RATE,...opts});
 assert.equal(a.validBins,b.validBins);
 assert.equal(a.provenance.metadataOnly,true);
 assert.equal(a.provenance.forceLocation,'bridge');
 assert.equal(a.spectrum[15].magnitude,b.spectrum[15].magnitude);
});
test('invalid and uninformative sensors cannot pass the estimator',()=>{
 const {force,velocity}=fixture(16384);
 assert.throws(()=>estimateBridgeMobilityH1({
  bridgeForce:force,bridgeVelocity:new Float64Array(2),sampleRate:RATE}),TypeError);
 assert.throws(()=>estimateBridgeMobilityH1({
  bridgeForce:new Float64Array(force.length),bridgeVelocity:velocity,sampleRate:RATE}),RangeError);
 const contaminated=force.slice();contaminated[43]=NaN;
 assert.throws(()=>estimateBridgeMobilityH1({
  bridgeForce:contaminated,bridgeVelocity:velocity,sampleRate:RATE}),TypeError);
 assert.throws(()=>estimateBridgeMobilityH1({
  bridgeForce:force,bridgeVelocity:velocity,sampleRate:RATE,windowSize:300}),RangeError);
});
