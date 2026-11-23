import test from 'node:test';
import assert from 'node:assert/strict';
import {SharedPassiveModalPiano} from '../research/shared-passive-modal-piano.mjs';

test('88 MIDI keys preserve multi-partial transverse structure without 88 independent boards',()=>{
 const p=new SharedPassiveModalPiano();
 assert.ok(p.n>176,'should retain more than one partial per string');
 assert.ok(p.n<88*2*8,'bounded mode bank');
 assert.equal(p.keyStart.length,89);
 assert.equal(p.keyStart[0],0);
 assert.equal(p.keyStart[88],p.n);
 assert.equal(p.bx.length,2);
 const c2=36-21;
 assert.equal(p.keyStart[c2+1]-p.keyStart[c2],10,'C2: five partials x two polarizations');
 const c5=72-21;
 assert.equal(p.keyStart[c5+1]-p.keyStart[c5],4,'C5: two partials x two polarizations');
 for(let i=0;i<p.n;i++){
  assert.ok(p.mass[i]>0&&p.ground[i]>0);
  assert.ok(p.coupling[i]>=0&&p.damping[i]>=0);
  assert.ok(p.frequency[i]<p.sampleRate*.43);
 }
});
test('C2 harmonics have positive inharmonicity and shared strike projections',()=>{
 const p=new SharedPassiveModalPiano({inharmonicity:.001});
 const start=p.keyStart[36-21];
 const freq1=p.frequency[start],freq2=p.frequency[start+2];
 assert.ok(freq2>freq1*2,'stiff string overtones must be stretched');
 assert.notEqual(p.strikeWeights[start],p.strikeWeights[start+2]);
});
test('no input gives zero output and conserved zero state',()=>{
 const p=new SharedPassiveModalPiano();
 for(let i=0;i<1000;i++)assert.equal(p.step(),0);
 assert.equal(p.energy(),0);
 assert.equal(p.externalWork,0);
});
test('modal network balances work, dissipation and energy at three sample rates',()=>{
 for(const sampleRate of [44100,48000,96000]){
  const p=new SharedPassiveModalPiano({sampleRate,coupling:.7});
  p.noteOn(36,{velocity:96,peakForce:120,contactMs:4});
  p.noteOn(43,{velocity:83,peakForce:80,contactMs:3});
  for(let i=0;i<2500;i++){
   if(i===350)p.noteOff(36);
   if(i===800)p.setSustain(127);
   if(i===1500)p.setSustain(0);
   if(i===1850)p.noteOff(43);
   const output=p.step();
   assert.ok(Number.isFinite(output));
   assert.ok(Number.isFinite(p.energy()));
  }
  assert.equal(p.activeContacts,0);
  assert.ok(p.externalWork>0&&p.dissipated>0);
  const error=Math.abs(p.energyBalanceError());
  assert.ok(error/Math.max(1,p.externalWork)<1e-8,'energy mismatch '+sampleRate+': '+error);
 }
});
test('after hammer contact, dampers and pedal cannot create energy',()=>{
 const p=new SharedPassiveModalPiano({coupling:.9});
 p.noteOn(36,{peakForce:90});
 while(p.activeContacts)p.step();
 let before=p.energy();
 assert.ok(before>0);
 for(let i=0;i<4000;i++){
  if(i===100)p.noteOff(36);
  if(i===200)p.setSustain(127);
  if(i===2400)p.setSustain(0);
  p.step();
  const now=p.energy();
  assert.ok(now<=before*(1+1e-10)+1e-13,'passivity '+i);
  before=now;
 }
});
test('only physically coupled bridge can excite an untouched remote partial',()=>{
 const linked=new SharedPassiveModalPiano({coupling:.8});
 const independent=new SharedPassiveModalPiano({coupling:0});
 for(const p of [linked,independent]){
  p.noteOn(43,{peakForce:0});
  p.noteOn(36,{peakForce:130});
 }
 const target=linked.keyStart[43-21];
 let max=0;
 for(let i=0;i<5000;i++){
  linked.step();independent.step();
  max=Math.max(max,Math.abs(linked.x[target]));
 }
 assert.equal(independent.x[target],0);
 assert.ok(max>1e-14,'bridge did not transfer energy to untouched C/G chord partial');
});
test('32/48/64 key strikes stay finite, limited to one board, and reset',()=>{
 for(const notes of [32,48,64]){
  const p=new SharedPassiveModalPiano({coupling:.12});
  for(let i=0;i<notes;i++)p.noteOn(21+i,{velocity:72,peakForce:30});
  const signal=new Float64Array(128);
  for(let i=0;i<80;i++){
   p.render(signal);
   for(const y of signal)assert.ok(Number.isFinite(y));
  }
  assert.equal(p.activeContacts,0);
  assert.equal(p.bx.length,2);
  assert.ok(p.energy()>0);
  assert.ok(Math.abs(p.energyBalanceError())<1e-6);
  p.reset();assert.equal(p.energy(),0);
  assert.equal(p.activeContacts,0);
 }
});
test('invalid coupling, notes, high sample alias parameters and output windows fail closed',()=>{
 assert.throws(()=>new SharedPassiveModalPiano({partialsBass:0}),RangeError);
 assert.throws(()=>new SharedPassiveModalPiano({inharmonicity:1}),RangeError);
 const p=new SharedPassiveModalPiano();
 assert.throws(()=>p.noteOn(200),RangeError);
 assert.throws(()=>p.noteOn(36,{contactMs:80}),RangeError);
 assert.throws(()=>p.noteOn(36,{velocity:0}),RangeError);
 assert.throws(()=>p.setSustain(-1),RangeError);
 assert.throws(()=>p.render(new Float32Array(5),4,2),RangeError);
});
