import test from 'node:test';
import assert from 'node:assert/strict';
import {C3XV8Engine as Reference} from '../piano-c3x-v8-web.js';
import {C3XV8Engine as Candidate} from '../research/c3x-v8-block-cache.mjs';

for(const [sr,q,num] of [[22050,'eco',32],[44100,'balanced',48],[48000,'studio',64],[96000,'eco',32],[48000,'eco',1]]){
 test('identical PCM and voice lifecycle: '+sr+' '+q+' '+num,()=>{
  const a=new Reference(sr,q),b=new Candidate(sr,q);
  const both=(method,...args)=>{a[method](...args);b[method](...args)};
  for(let i=0;i<num;i++)both('noteOn',{id:i+1,key:num===1?60:21+(i*7)%88,speed:[.06,.1,.15,.5,1][i%5],hardness:(i%7)/6,brightness:.55});
  const nblocks=num===1?7500:48;
  const L=new Float32Array(128),R=new Float32Array(128),X=new Float32Array(128),Y=new Float32Array(128);
  for(let j=0;j<nblocks;j++){
   if(j===8)both('setSustain',127);
   if(j===10)for(let i=1;i<=num;i+=2)both('noteOff',i,false,.5);
   if(j===12)both('setControls',{brightness:.21,resonance:.8,damping:.1,lid:.9});
   if(j===14)both('updateVoice',1,{brightness:.93,damping:.81,release:.7});
   if(j===16&&num!==1)both('setQuality','eco');
   if(j===20&&num!==1)both('setSustain',0);
   if(j===24&&num!==1)both('noteOn',{id:1000,key:60,speed:.89});
   if(j===30&&num!==1)both('noteOff',1000,true,.02);
   if(j===40&&num!==1)both('stopAll');
   a.render(L,R);b.render(X,Y);
   for(let i=0;i<128;i++){
    assert.ok(Number.isFinite(L[i])&&Number.isFinite(R[i]));
    if(!Object.is(L[i],X[i])||!Object.is(R[i],Y[i]))assert.fail('PCM difference at '+j+':'+i);
   }
   assert.deepEqual(a.done,b.done);
   assert.deepEqual(a.voices.map(v=>v.id),b.voices.map(v=>v.id));
  }
 });
}
