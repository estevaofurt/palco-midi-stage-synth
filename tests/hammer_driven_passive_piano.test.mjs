import test from 'node:test';
import assert from 'node:assert/strict';
import {HammerDrivenPassivePiano} from '../research/hammer-driven-passive-piano.mjs';

test('causal hammer contacts and finite mechanical output at 44.1/48/96 kHz',()=>{
 for(const sampleRate of [44100,48000,96000]){
  const p=new HammerDrivenPassivePiano({sampleRate,coupling:.2});
  assert.equal(p.step(),0);
  p.noteOn(36,{velocity:90,contactMs:3,peakForce:120});
  assert.equal(p.activeContactCount,1);
  let peak=0;
  for(let i=0;i<Math.round(sampleRate*.055);i++){
   const value=p.step();
   assert.ok(Number.isFinite(value));
   peak=Math.max(peak,Math.abs(value));
  }
  assert.ok(peak>0,'mechanical response absent');
  assert.equal(p.activeContactCount,0);
  assert.ok(p.bridge.externalWork>0,'hammer force should inject work');
  assert.ok(p.bridge.dissipated>0,'damping should remove energy');
  const error=p.energyBalanceError();
  const scale=Math.max(1,p.bridge.externalWork,p.bridge.energy());
  assert.ok(Math.abs(error)/scale<1e-7,'passive work/energy mismatch '+sampleRate+': '+error);
 }
});

test('after hammer contacts finish, free energy monotonically decreases through pedal and releases',()=>{
 const p=new HammerDrivenPassivePiano({coupling:.7});
 p.noteOn(36,{velocity:100,peakForce:80});
 p.noteOn(43,{velocity:85,peakForce:65});
 while(p.activeContactCount)p.step();
 let energy=p.bridge.energy();
 assert.ok(energy>0);
 for(let i=0;i<3400;i++){
  if(i===100)p.noteOff(36);
  if(i===200)p.setSustain(127);
  if(i===1200)p.setSustain(0);
  if(i===2200)p.noteOff(43);
  p.step();
  const now=p.bridge.energy();
  assert.ok(now<=energy*(1+1e-10)+1e-16,'spontaneous growth '+i);
  energy=now;
 }
 assert.ok(Math.abs(p.energyBalanceError())<1e-6);
});

test('force causally re-excites another string only when bridge coupling is present',()=>{
 const connected=new HammerDrivenPassivePiano({coupling:.8});
 const disconnected=new HammerDrivenPassivePiano({coupling:0});
 for(const p of [connected,disconnected]){
  p.noteOn(43);
  p.noteOn(36,{peakForce:120});
 }
 let max=0;
 for(let i=0;i<5000;i++){
  connected.step();disconnected.step();
  max=Math.max(max,Math.abs(connected.bridge.x[(43-21)*2]));
 }
 assert.equal(disconnected.bridge.x[(43-21)*2],0);
 assert.ok(max>1e-15,'no passive cross-string transfer');
});

test('block render is identical to sample-by-sample and remains within buffers',()=>{
 const a=new HammerDrivenPassivePiano(),b=new HammerDrivenPassivePiano();
 for(const p of [a,b])p.noteOn(36,{velocity:97,peakForce:90});
 const out=new Float64Array(1024);
 const before=new Float64Array(1024);
 a.render(out);
 for(let i=0;i<1024;i++)before[i]=b.step();
 assert.deepEqual(out,before);
 assert.throws(()=>a.render(out,1000,100),RangeError);
 assert.equal(a.samples,1024);
});

test('full 88-key mechanical load, 32/48/64 active contacts and energy checks',()=>{
 for(const n of [32,48,64]){
  const p=new HammerDrivenPassivePiano();
  for(let i=0;i<n;i++)p.noteOn(21+i,{peakForce:30,velocity:64});
  assert.equal(p.activeContactCount,n);
  assert.equal(p.bridge.n,176);
  const block=new Float32Array(128);
  for(let j=0;j<30;j++){
   p.render(block);
   for(const x of block)assert.ok(Number.isFinite(x));
  }
  assert.equal(p.activeContactCount,0);
  assert.ok(p.bridge.energy()>0);
  assert.ok(Math.abs(p.energyBalanceError())<1e-6);
  p.reset();
  assert.equal(p.bridge.energy(),0);
  assert.equal(p.activeContactCount,0);
 }
});

test('reject unbounded contact, invalid inputs and negative forces',()=>{
 assert.throws(()=>new HammerDrivenPassivePiano({maxContactMs:100}),RangeError);
 const p=new HammerDrivenPassivePiano();
 for(const args of [{contactMs:50},{peakForce:-1},{velocity:0},{contactMs:NaN}])
  assert.throws(()=>p.noteOn(36,args),RangeError);
 assert.throws(()=>p.noteOn(200),RangeError);
 assert.throws(()=>p.setSustain(160),RangeError);
 assert.throws(()=>p.render(new Float32Array(5),-1,1),RangeError);
 assert.equal(p.bridge.energy(),0);
});
