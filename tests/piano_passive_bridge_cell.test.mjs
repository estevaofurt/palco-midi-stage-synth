import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {PassiveStringBridgeCell,PASSIVE_BRIDGE_DIMENSIONS} from '../research/passive-string-bridge-cell.mjs';

const approx=(a,b,rTol=1e-8,aTol=1e-14)=>Math.abs(a-b)<=aTol+rTol*Math.max(Math.abs(a),Math.abs(b));

test('model consists of two independently damped string and two coupled board coordinates',()=>{
 const p=new PassiveStringBridgeCell({sampleRate:48000,key:36,coupling:.12});
 assert.equal(PASSIVE_BRIDGE_DIMENSIONS,4);
 assert.equal(p.frequencies.length,4);
 assert.ok(p.damping.every(v=>v>=0));
 assert.ok(p.mass.every(v=>v>0));
 for(let i=0;i<4;i++){
   assert.ok(p.stiffness[i*4+i]>0);
   for(let j=0;j<4;j++)
     assert.ok(approx(p.stiffness[i*4+j],p.stiffness[j*4+i]),
       'K must be symmetric');
 }
 assert.ok(p.stiffness[2]<0,'fast string must connect to bridge');
 assert.ok(p.stiffness[6]<0,'slow string must connect to bridge');
});

test('exact discrete energy identity — forced response equals input work minus dissipated power',()=>{
 for(const sampleRate of [44100,48000,96000])
 for(const coupling of [0,.03,.12,.7,1]){
   const p=new PassiveStringBridgeCell({sampleRate,key:36,coupling});
   const initial=p.energy();
   for(let i=0;i<Math.round(sampleRate*.12);i++){
     const t=i/sampleRate;
     const force=(t<.012?Math.sin(Math.PI*t/.012)**2:0)*8;
     p.step(force);
     const mechanical=p.energy();
     const target=initial+p.hammerWork-p.dissipatedEnergy;
     assert.ok(Number.isFinite(mechanical)&&mechanical>=-1e-15);
     assert.ok(approx(mechanical,target,7e-7,3e-13),
       'energy balance broken sample='+i+' sr='+sampleRate+' coupling='+coupling+
       ' mechanical='+mechanical+' target='+target);
   }
 }
});

test('zero external force causes non-increasing mechanical energy, never a self-excited bridge',()=>{
 for(const key of [24,36,48])
 for(const coupling of [0,.1,1]){
   const p=new PassiveStringBridgeCell({key,coupling});
   p.setInitialDisplacement(0,.00006);
   p.setInitialDisplacement(1,-.00004);
   let previous=p.energy();
   for(let i=0;i<24000;i++){
     p.step(0);
     const now=p.energy();
     assert.ok(Number.isFinite(now));
     assert.ok(now<=previous+1e-10,
       'passivity violated key='+key+' coupling='+coupling+' sample='+i);
     previous=now;
   }
   assert.ok(p.energy()>=0);
 }
});

test('bridge receives energy only through real coupling in this network',()=>{
 const disconnected=new PassiveStringBridgeCell({key:36,coupling:0});
 const connected=new PassiveStringBridgeCell({key:36,coupling:.3});
 disconnected.setInitialDisplacement(0,.0001);
 connected.setInitialDisplacement(0,.0001);
 let plateEnergyDisconnected=0,plateEnergyConnected=0;
 for(let i=0;i<24000;i++){
   plateEnergyDisconnected+=disconnected.step(0)**2;
   plateEnergyConnected+=connected.step(0)**2;
 }
 assert.ok(plateEnergyDisconnected===0,'no false board sound in decoupled system');
 assert.ok(plateEnergyConnected>1e-10,'real coupling should move board');
 assert.ok(Number.isFinite(connected.bridgeReaction));
});

test('silent zero-state, reset and parameter validation',()=>{
 const p=new PassiveStringBridgeCell();
 for(let i=0;i<4000;i++){
   assert.equal(p.step(0),0);
   assert.equal(p.energy(),0);
 }
 p.step(10);assert.ok(p.energy()>0);
 p.reset();
 assert.equal(p.energy(),0);
 assert.equal(p.plateVelocity,0);
 assert.equal(p.hammerWork,0);
 assert.throws(()=>p.step(NaN),/nonfinite/);
 assert.throws(()=>p.setInitialDisplacement(8,1),/coordinate/);
 assert.throws(()=>new PassiveStringBridgeCell({coupling:-.1}),/coupling/);
 assert.throws(()=>new PassiveStringBridgeCell({key:200}),/MIDI/);
});

test('deliberately does not alter published Stage D, carry new audio assets or claim acoustic pressure',()=>{
 const src=readFileSync(new URL('../research/passive-string-bridge-cell.mjs',import.meta.url),'utf8');
 assert.match(src,/NOT connected to any Stage DSP or UI/);
 assert.match(src,/NOT acoustic pressure/);
 assert.doesNotMatch(src,/readFileSync|fetch\(|AudioWorkletProcessor|writeFileSync|convolver/i);
});
