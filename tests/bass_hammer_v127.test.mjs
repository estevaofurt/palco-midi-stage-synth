import test from 'node:test';
import assert from 'node:assert/strict';
import {HybridPianoEngine,hybridContactTime,bassContactTransferMagnitude} from '../physical-piano-hybrid.js';

const R=48000;
function samples(engine,seconds=.32){
 const n=Math.ceil(seconds*R),l=new Float32Array(128),r=new Float32Array(128);
 let peak=0,sum=0,head=0,body=0;
 for(let pos=0;pos<n;pos+=128){
  const count=Math.min(128,n-pos);
  engine.render(l,r,null,count);
  for(let i=0;i<count;i++){
   const x=l[i],y=r[i];
   assert.ok(Number.isFinite(x)&&Number.isFinite(y),'finite stereo output');
   peak=Math.max(peak,Math.abs(x),Math.abs(y));
   sum+=x*x;
   if(pos+i<R*.012)head+=x*x;
   else if(pos+i<R*.120)body+=x*x;
  }
 }
 return {peak,rms:Math.sqrt(sum/n),head,body};
}
test('hammer applies a positive finite-area force to C1–C3 only',()=>{
 for(const key of [24,36,48]){
  const e=new HybridPianoEngine(R,'eco');
  e.noteOn({id:1,key,speed:.72,hardness:.5,character:'american'});
  const v=e.find(1);
  assert.ok(v.forceCount>=16&&v.forceCount<=512);
  assert.equal(v.forceIndex,0);
  let total=0;
  for(let i=0;i<v.forceCount;i++){
   assert.ok(v.force[i]>=0&&Number.isFinite(v.force[i]));
   total+=v.force[i];
  }
  assert.ok(Math.abs(total-1)<1e-10,'normalized contact force');
  assert.ok(v.drive.slice(0,v.count).some(x=>x>0));
  assert.ok(v.y1.slice(0,v.count).every(x=>x===0),'no string displacement before strike');
  const sound=samples(e,.24);
  assert.ok(sound.rms>.00002,'non-silent mode after contact '+key);
  assert.ok(sound.peak<.961,'bounded output '+key);
  assert.equal(v.forceIndex,v.forceCount,'force must finish without allocations');
 }
 for(const key of [49,60,72,84,108]){
  const e=new HybridPianoEngine(R,'eco');
  e.noteOn({id:1,key,speed:.72});
  assert.equal(e.find(1).forceCount,0,'middle/high path must be untouched');
 }
});

test('hammer contact changes with touch/soft felt and has no static onset fake impulse',()=>{
 const soft=hybridContactTime(36,.3,.1,'american');
 const hard=hybridContactTime(36,.95,.95,'american');
 assert.ok(soft>hard);
 const e=new HybridPianoEngine(R);
 e.noteOn({id:2,key:36,speed:.76});
 const v=e.find(2);
 assert.equal(v.impact,0);
 assert.equal(v.attack,1);
 samples(e,.15);
 assert.equal(v.forceIndex,v.forceCount);
});

test('bass force does not prevent note-off, pedal or voice termination',()=>{
 const e=new HybridPianoEngine(R,'eco');
 e.noteOn({id:11,key:36,speed:.67});
 samples(e,.1);
 e.setSustain(127);e.noteOff(11,false,.14);
 assert.equal(e.find(11).damped,false);
 e.setSustain(0);assert.equal(e.find(11).damped,true);
 samples(e,2.0);
 assert.equal(e.find(11),null);
});

test('dense bass loads remain finite across 32/48/64 without NaN',()=>{
 for(const [quality,n] of [['eco',32],['balanced',48],['studio',64]]){
  const e=new HybridPianoEngine(R,quality);
  for(let i=0;i<n;i++)e.noteOn({id:i+1,key:24+i%25,speed:.85,character:'american'});
  assert.equal(e.voices.filter(v=>v.active).length,n);
  const sound=samples(e,.14);
  assert.ok(sound.rms>.00001);
  assert.ok(sound.peak<.961);
  e.stopAll();
 }
});

test('closed-form force spectrum matches direct DFT from the actual discrete pressure kernel',()=>{
  for(const n of [16,17,32,60,144,333,512]){
    const e=new HybridPianoEngine(R,'eco');
    // No need for exact n from MIDI: use the identical normalized raised-cosine
    // discrete pressure formula to independently verify its analytic spectrum.
    for(const w of [0,.002,.03,.09,.22,.53,1.21,2.31,2.75,Math.PI]){
      let re=0,im=0;
      for(let j=0;j<n;j++){
        const force=(1-Math.cos(2*Math.PI*(j+.5)/n))/n;
        re+=force*Math.cos(w*j);im+=force*Math.sin(w*j);
      }
      const direct=Math.hypot(re,im);
      const fast=bassContactTransferMagnitude(n,w);
      assert.ok(Math.abs(direct-fast)<2e-9,
        'wrong exact contact transfer n='+n+' w='+w+' diff='+Math.abs(direct-fast));
    }
  }
});
