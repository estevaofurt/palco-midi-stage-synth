import test from 'node:test';
import assert from 'node:assert/strict';
import {estimateBridgeAccelerationToPressure as estimate} from '../research/bridge-radiation-h1.mjs';

function noise(seed=17){
 let s=seed>>>0;
 return ()=>{
   s=(Math.imul(s,1664525)+1013904223)>>>0;
   return 2*(s/4294967296)-1;
 };
}
function fixture(rate=48000,length=16384,{noisy=false,unrelated=false,seed=1}={}){
 const ra=noise(seed),rb=noise(seed+8);
 const acceleration=new Float64Array(length),pressure=new Float64Array(length);
 for(let i=0;i<length;i++)acceleration[i]=ra();
 for(let i=0;i<length;i++){
   // Synthetic signal with a known FIR response and integer-sample delay.
   const related=(i>=3?.65*acceleration[i-3]:0)-
                 (i>=4?.2*acceleration[i-4]:0);
   pressure[i]=(unrelated?0:related)+(noisy?.65*rb():unrelated?rb():0);
 }
 return {acceleration,pressure,sampleRate:rate};
}
function analytic(frequency,rate){
 const a=-2*Math.PI*frequency/rate;
 const real=.65*Math.cos(3*a)-.2*Math.cos(4*a);
 const imag=.65*Math.sin(3*a)-.2*Math.sin(4*a);
 return {real,imag};
}
function mean(a){return a.reduce((s,v)=>s+v,0)/a.length;}

test('identifies a known causal pressure/acceleration impulse, magnitude and phase at 44.1/48/96 kHz',()=>{
 for(const rate of [44100,48000,96000]){
  const out=estimate({...fixture(rate),windowSize:1024});
  assert.equal(out.transferUnit,'Pa/(m/s²)');
  assert.ok(out.segments>=30);
  assert.ok(out.validFraction>.95);
  for(const bin of [10,30,100,220,400]){
   const row=out.spectrum[bin],truth=analytic(row.frequencyHz,rate);
   assert.ok(row.valid && row.coherence>.99,'known-input bin must be coherent');
   assert.ok(Math.abs(row.real-truth.real)<.035,
     'real error at '+rate+'/'+bin+': '+row.real+' expected '+truth.real);
   assert.ok(Math.abs(row.imag-truth.imag)<.035,
     'imag error at '+rate+'/'+bin+': '+row.imag+' expected '+truth.imag);
  }
 }
});

test('additive unrelated output noise reduces coherence and does not become trusted transfer',()=>{
 const clean=estimate(fixture());
 const noisy=estimate(fixture(48000,16384,{noisy:true}));
 const separate=estimate(fixture(48000,16384,{unrelated:true}));
 const mids=[20,40,60,80,100,120,160,180,200];
 const coherence=x=>mean(mids.map(i=>x.spectrum[i].coherence));
 assert.ok(coherence(clean)>.995);
 assert.ok(coherence(noisy)<.7);
 assert.ok(coherence(separate)<.12);
 assert.ok(separate.validFraction<.05,'unrelated pressure must not pass coherence gate');
 assert.ok(noisy.validBins<clean.validBins);
 assert.ok(separate.spectrum[60].magnitude===null);
});

test('rejects sensor inputs that are not identifiable or misaligned in length',()=>{
 const f=fixture();
 assert.throws(()=>estimate({...f,pressure:f.pressure.subarray(1)}),/equal-length/);
 assert.throws(()=>estimate({...f,sampleRate:0}),/sample rate/);
 assert.throws(()=>estimate({...f,windowSize:257}),/power of two/);
 assert.throws(()=>estimate({...f,hopSize:0}),/hopSize/);
 assert.throws(()=>estimate({...f,coherenceThreshold:2}),/coherence threshold/);
 assert.throws(()=>estimate({...f,relativeInputFloor:1}),/relativeInputFloor/);
 assert.throws(()=>estimate({...f,acceleration:new Float64Array(f.acceleration.length)}),/no resolvable energy/);
 const contaminated=f.pressure.slice();contaminated[90]=NaN;
 assert.throws(()=>estimate({...f,pressure:contaminated}),/non-finite/);
 assert.throws(()=>estimate({acceleration:new Float64Array(300),pressure:new Float64Array(300),sampleRate:48000}),/four Welch windows/);
});

test('gain scaling tracks units and phase when pressure sensor calibration changes',()=>{
 const f=fixture(),base=estimate(f);
 const scaled=estimate({...f,pressure:Float64Array.from(f.pressure,v=>2.5*v)});
 for(const k of [20,90,210]){
  const a=base.spectrum[k],b=scaled.spectrum[k];
  assert.ok(a.valid&&b.valid);
  assert.ok(Math.abs(b.magnitude/a.magnitude-2.5)<1e-10);
  assert.ok(Math.abs(a.phaseRadians-b.phaseRadians)<1e-10);
 }
});

test('independent synthetic holdout recovers the same known radiative transfer',()=>{
 const train=estimate(fixture(48000,16384,{seed:2}));
 const holdout=estimate(fixture(48000,16384,{seed:901}));
 for(const k of [18,32,71,133,241,420]){
  const a=train.spectrum[k],b=holdout.spectrum[k];
  assert.ok(a.valid&&b.valid);
  assert.ok(Math.hypot(a.real-b.real,a.imag-b.imag)<.045,
   'held-out transfer failed at bin '+k);
 }
});

test('an unaccounted sensor-channel delay changes recovered phase even with high coherence',()=>{
 const f=fixture(),reference=estimate(f);
 const delayed=new Float64Array(f.pressure.length);
 for(let i=9;i<delayed.length;i++)delayed[i]=f.pressure[i-9];
 const shifted=estimate({...f,pressure:delayed});
 const k=100,a=reference.spectrum[k],b=shifted.spectrum[k];
 assert.ok(a.valid&&b.valid);
 const expected=-2*Math.PI*k*9/1024;
 const z0=[a.real,a.imag],z1=[b.real,b.imag];
 const ratioPhase=Math.atan2(z1[1]*z0[0]-z1[0]*z0[1],z1[0]*z0[0]+z1[1]*z0[1]);
 const phaseError=Math.atan2(Math.sin(ratioPhase-expected),Math.cos(ratioPhase-expected));
 assert.ok(Math.abs(phaseError)<.1,'channel delay must appear as phase offset');
});
