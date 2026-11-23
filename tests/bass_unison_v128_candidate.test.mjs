import test from 'node:test';
import assert from 'node:assert/strict';
import {HybridPianoEngine as Original} from '../physical-piano-hybrid-v127.mjs';
import {HybridPianoEngine as Candidate} from '../physical-piano-hybrid-v128-candidate.mjs';

const R=48000,B=128;
const prepare=(Engine,key,velocity=80,quality='studio',character='american')=>{
 const e=new Engine(R,quality);
 e.noteOn({id:1,key,speed:velocity/127,hardness:.55,brightness:.5,send:0,character});
 return e;
};
function capture(e,frames=48000){
 const out=new Float32Array(frames*2),L=new Float32Array(B),Rr=new Float32Array(B);
 for(let i=0;i<frames;i+=B){
  const n=Math.min(B,frames-i);
  e.render(L,Rr,null,n);
  for(let j=0;j<n;j++){
   out[(i+j)*2]=L[j];out[(i+j)*2+1]=Rr[j];
  }
 }
 return out;
}
const rms=a=>Math.sqrt(a.reduce((s,x)=>s+x*x,0)/a.length);
test('candidate enables two unison modes per low partial from F1 to C2, but preserves monochord A0–E1',()=>{
 for(const key of [21,24,28]){
  for(const q of ['eco','balanced','studio']){
   const a=prepare(Original,key,80,q),b=prepare(Candidate,key,80,q);
   assert.equal(a.find(1).count,b.find(1).count,'single string boundary stays identical');
  }
 }
 for(const key of [29,33,36]){
  for(const q of ['eco','balanced','studio']){
   const a=prepare(Original,key,80,q),b=prepare(Candidate,key,80,q);
   assert.equal(b.find(1).count-a.find(1).count,b.paired);
   assert.ok(b.find(1).count<=32,'preallocated MAX_MODES');
   assert.ok(b.find(1).forceCount>0,'causal hammer unchanged');
  }
 }
});
test('original and candidate PCM remain bitwise identical on A0-E1 and C3-C8 in 3 qualities',()=>{
 let frames=0;
 for(const key of [21,24,28,37,48,49,60,72,84,108]){
  for(const q of ['eco','balanced','studio']){
   const a=capture(prepare(Original,key,80,q),B*80);
   const b=capture(prepare(Candidate,key,80,q),B*80);
   assert.deepEqual(a,b,'unexpected sonic regression key='+key+' quality='+q);
   frames+=a.length;
  }
 }
 assert.ok(frames>600000);
});
test('upper bass notes C2, A1, F1 change materially without NaN/clipping or sample allocation',()=>{
 for(const key of [29,33,36]){
  const a=capture(prepare(Original,key),R*.42);
  const b=capture(prepare(Candidate,key),R*.42);
  let diff=0,peak=0;
  for(let i=0;i<a.length;i++){
   if(a[i]!==b[i])diff++;
   peak=Math.max(peak,Math.abs(b[i]));
   assert.ok(Number.isFinite(b[i]));
  }
  assert.ok(diff>5000,'no meaningful changed samples key='+key);
  assert.ok(peak<.961,'candidate output limiter exceeded key='+key+' '+peak);
  assert.ok(rms(b)>.00001);
 }
});
test('bass experiment preserves pedal, CC64, note-off and release semantics',()=>{
 const e=prepare(Candidate,36,80,'studio');
 capture(e,R*.08);
 e.setSustain(127);e.noteOff(1,false,.14);
 assert.equal(e.find(1).damped,false);
 e.setSustain(0);assert.equal(e.find(1).damped,true);
 capture(e,R*2.2);
 assert.equal(e.find(1),null);
});
test('candidate allocates 32/48/64 voices with bounded audio output for bass stress',()=>{
 for(const [quality,count] of [['eco',32],['balanced',48],['studio',64]]){
  const e=new Candidate(R,quality);
  for(let i=0;i<count;i++)e.noteOn({id:100+i,key:29+i%20,speed:.85,
    hardness:.6,brightness:.5,character:'american',send:0});
  assert.equal(e.voices.filter(v=>v.active).length,count);
  assert.ok(e.voices.filter(v=>v.active).reduce((sum,v)=>sum+v.count,0)<=count*32);
  const rendered=capture(e,B*150);
  assert.ok(rms(rendered)>.00001);
  assert.ok(rendered.every(Number.isFinite));
  assert.ok(Math.max(...rendered.subarray(0,128))<.961);
  e.stopAll();
 }
});
