import test from 'node:test';
import assert from 'node:assert/strict';
import {DamperAwareSharedBridge,ALL_PIANO_KEYS} from '../research/damper-aware-shared-bridge.mjs';

test('full 88-key load is permanent; strike only excites passive states',()=>{
 const a=new DamperAwareSharedBridge({coupling:.2});
 assert.equal(ALL_PIANO_KEYS.length,88);
 assert.equal(a.n,176);
 const old=a.sumK;
 a.noteOn(36);a.strike(36);a.noteOff(36);a.setSustain(127);
 assert.equal(a.sumK,old,'key release must not remove bridge load');
 assert.equal(a.n,176);
 assert.ok(a.energy()>0);
});
test('damper raises only nonnegative damping and never changes stiffness',()=>{
 const e=new DamperAwareSharedBridge({coupling:.3});
 const i=(36-21)*2,closed=e.damping[i],k=e.ground[i],kc=e.coupling[i];
 e.noteOn(36);
 assert.ok(e.damping[i]<closed);
 e.noteOff(36);
 assert.equal(e.damping[i],closed);
 e.setSustain(127);
 assert.ok(e.damping[i]<closed);
 e.noteOn(36);e.noteOn(36);e.noteOff(36);
 assert.equal(e.held[36-21],1);
 e.setSustain(0);
 assert.ok(e.damping[i]<closed,'held repeated note must retain damper');
 e.noteOff(36);
 assert.equal(e.damping[i],closed);
 assert.equal(e.ground[i],k);assert.equal(e.coupling[i],kc);
});
test('energy cannot grow during free evolution after a strike and damper changes',()=>{
 for(const sr of [44100,48000,96000]){
  const e=new DamperAwareSharedBridge({sampleRate:sr,coupling:.7});
  e.noteOn(36);e.strike(36,{displacement:.00008});
  let last=e.energy();
  for(let i=0;i<1700;i++){
   if(i===250)e.noteOff(36);
   if(i===600)e.setSustain(127);
   if(i===850)e.setSustain(0);
   e.step();
   const now=e.energy();
   assert.ok(Number.isFinite(now)&&now>=0,'invalid energy');
   assert.ok(now<=last*(1+1e-10)+1e-15,'energy creation '+sr+' sample '+i+' '+(now-last));
   last=now;
  }
  assert.ok(e.energy()<e.externalWork+e.dissipated+1, 'bounded');
 }
});
test('no bridge energy or radiation proxy on zero input',()=>{
 const e=new DamperAwareSharedBridge();
 for(let i=0;i<1024;i++)assert.equal(e.step(),0);
 assert.equal(e.energy(),0);
});
test('physical sympathetic bridge response depends on coupling, not additive wood sine',()=>{
 const silent=new DamperAwareSharedBridge({coupling:0});
 const shared=new DamperAwareSharedBridge({coupling:.8});
 for(const e of [silent,shared]){
  e.noteOn(36);e.noteOn(43);e.strike(36,{displacement:.0001});
 }
 let max=0;
 for(let i=0;i<5000;i++){
  silent.step();shared.step();
  max=Math.max(max,Math.abs(shared.x[(43-21)*2]));
 }
 assert.equal(silent.x[(43-21)*2],0,'zero coupling must not re-excite another string');
 assert.ok(max>1e-14,'coupled bridge did not re-excite held unison');
 assert.ok(Number.isFinite(shared.energy()));
});
test('64-key stress remains finite, with 88 string load and no voice duplication',()=>{
 for(const n of [32,48,64]){
  const e=new DamperAwareSharedBridge({coupling:.12});
  for(let i=0;i<n;i++){e.noteOn(21+i);e.strike(21+i,{displacement:.000006});}
  for(let i=0;i<2000;i++){
   const p=e.step();
   assert.ok(Number.isFinite(p));
  }
  assert.equal(e.n,176);
  assert.ok(e.energy()>=0&&Number.isFinite(e.energy()));
 }
});
test('bad parameters and MIDI controls are rejected',()=>{
 assert.throws(()=>new DamperAwareSharedBridge({releaseDamping:-1}),RangeError);
 const e=new DamperAwareSharedBridge();
 assert.throws(()=>e.noteOn(200),RangeError);
 assert.throws(()=>e.noteOff(20),RangeError);
 assert.throws(()=>e.strike(36,{displacement:Infinity}),RangeError);
 assert.throws(()=>e.setSustain(200),RangeError);
 e.strike(60);
 e.reset();
 assert.equal(e.energy(),0);
 assert.equal(e.held[60-21],0);
});
