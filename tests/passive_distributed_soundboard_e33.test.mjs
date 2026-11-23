import test from 'node:test';
import assert from 'node:assert/strict';
import {PassiveDistributedSoundboardE33}
 from '../research/passive-distributed-soundboard-e33.mjs';

test('E3.3 retains all 88 strings but radiates only 8 actual moving plate modes',()=>{
 const p=new PassiveDistributedSoundboardE33();
 assert.equal(p.keyStart.length,89);
 assert.equal(p.keyStart[88],592);
 assert.equal(p.panelModes,8);
 assert.equal(p.panelVelocity.length,8);
 assert.equal(p.boardSize,9);
 assert.ok(p.panelShapes.some(x=>x[0]===2&&x[1]===1));
 assert.ok(p.panelShapeAtBridge.some(x=>x<0));
 assert.ok(p.panelShapeAtBridge.some(x=>x>0));
 for(let i=0;i<p.n;i++)assert.ok(p.mass[i]>0&&p.coupling[i]>=0);
 for(const x of p.panelMass)assert.ok(x>0);
});

test('zero initial energy remains exactly silent with no impact',()=>{
 const p=new PassiveDistributedSoundboardE33();
 for(let i=0;i<240;i++)p.step();
 assert.equal(p.externalWork,0);assert.equal(p.dissipated,0);
 assert.equal(p.energy(),0);
 assert.ok(Array.from(p.panelVelocity).every(x=>x===0));
});

test('physical 8-mode surface, strings and shared bridge obey work-energy identity',()=>{
 const p=new PassiveDistributedSoundboardE33();
 p.setSustain(127);
 p.noteOn(48,{velocity:100,peakForce:105,contactMs:3});
 let peak=0;
 for(let i=0;i<2000;i++){
  if(i===550)p.noteOff(48);
  const modes=p.step();
  for(const x of modes)peak=Math.max(peak,Math.abs(x));
 }
 assert.ok(p.externalWork>0&&p.dissipated>0);
 assert.ok(peak>1e-16);
 assert.ok(p.energy()>0);
 assert.ok(Math.abs(p.energyBalanceError())<1e-9,
  'passive error '+p.energyBalanceError());
 assert.ok(Math.abs(p.energyBalanceError())/p.externalWork<1e-7);
});

test('resonant board transfers energy from struck note to unstruck string',()=>{
 const p=new PassiveDistributedSoundboardE33({coupling:.5});
 p.setSustain(127);
 p.noteOn(48,{peakForce:105});
 let max=0;
 const remote=p.keyStart[55-21];
 for(let i=0;i<3000;i++){
  p.step();max=Math.max(max,Math.abs(p.x[remote]));
 }
 assert.ok(max>1e-15);
});

test('2-mode and 8-mode distributed panels behave differently without adding external audio',()=>{
 const pairs=[new PassiveDistributedSoundboardE33({panelModes:2}),
  new PassiveDistributedSoundboardE33({panelModes:8})];
 for(const p of pairs){p.setSustain(127);p.noteOn(48,{peakForce:105})}
 let n=0;
 for(let i=0;i<2500;i++){
  pairs[0].step();pairs[1].step();
  n+=Math.abs(pairs[0].panelVelocity[0]-pairs[1].panelVelocity[0]);
 }
 assert.ok(n>1e-16);
 for(const p of pairs)assert.ok(Math.abs(p.energyBalanceError())<1e-8);
});

test('damper + sustain toggles preserve passive decay after hammer pulse',()=>{
 const p=new PassiveDistributedSoundboardE33();
 p.noteOn(48,{peakForce:105});
 for(let i=0;i<300;i++)p.step();
 let previous=p.energy();
 for(let i=0;i<2000;i++){
  if(i===200)p.noteOff(48);
  if(i===450)p.setSustain(127);
  if(i===1400)p.setSustain(0);
  p.step();
  const energy=p.energy();
  assert.ok(energy<=previous*(1+1e-10)+1e-12,'energy increased without input');
  previous=energy;
 }
});

test('E3.3 stays finite under 32/48/64 simultaneous key strikes',()=>{
 for(const voices of [32,48,64]){
  const p=new PassiveDistributedSoundboardE33({panelModes:8});
  p.setSustain(127);
  for(let key=21;key<21+voices;key++)p.noteOn(key,{peakForce:30,velocity:85});
  for(let i=0;i<512;i++)p.step();
  assert.ok(Number.isFinite(p.energy()));
  assert.ok(p.energy()>0);
  assert.ok(Math.abs(p.energyBalanceError())/Math.max(1,p.externalWork)<1e-8);
 }
});

test('external-force mode disables prescribed hammer without modifying 88-key system',()=>{
 const p=new PassiveDistributedSoundboardE33({externalForceMode:true});
 assert.throws(()=>p.noteOn(48),RangeError);
 p.held[48-21]=1;p.updateDampers();
 const first=p.keyStart[48-21];
 p.forces[first]=25;
 for(let i=0;i<300;i++){
  if(i===20)p.forces[first]=0;
  p.step();
 }
 assert.ok(p.energy()>0);
 assert.ok(Math.abs(p.energyBalanceError())<1e-8);
});

test('invalid geometry and mode counts fail closed',()=>{
 for(const opts of [
  {panelModes:1},{panelModes:17},{bridgeU:1.3},
  {bridgePanelSpring:-1},{partialsBass:9},
  {sampleRate:1000},{coupling:-1},{externalForceMode:1}
 ])assert.throws(()=>new PassiveDistributedSoundboardE33(opts),RangeError);
 const p=new PassiveDistributedSoundboardE33();
 assert.throws(()=>p.noteOn(1000),RangeError);
 assert.throws(()=>p.setSustain(-5),RangeError);
});
