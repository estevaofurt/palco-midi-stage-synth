import test from 'node:test';
import assert from 'node:assert/strict';
import {HybridPianoEngine as Baseline} from '../physical-piano-hybrid.js';
import {HybridPianoEngine as Candidate} from '../physical-piano-hybrid-v129-candidate.mjs';
const render=(Model,key,quality,blocks=12)=>{
  const e=new Model(48000,quality);
  e.noteOn({id:1,key,speed:80/127,hardness:.55,brightness:.5,character:'american',send:0});
  const l=new Float32Array(128),r=new Float32Array(128),out=new Float32Array(256*blocks);
  for(let b=0;b<blocks;b++){
    e.render(l,r,null,128);
    for(let i=0;i<128;i++){
      out[b*256+i*2]=l[i];out[b*256+i*2+1]=r[i];
    }
  }
  return out;
};
test('isolated D129 has finite sound and preserves other registers (88 keys, 3 qualities)',()=>{
  for(const q of ['eco','balanced','studio']){
    for(let key=21;key<=108;key++){
      const old=render(Baseline,key,q),fresh=render(Candidate,key,q);
      for(const a of fresh)assert.ok(Number.isFinite(a),'nonfinite PCM '+q+' '+key);
      if(key>=29&&key<=36)assert.notDeepEqual(fresh,old,'candidate did not change '+key+'/'+q);
      else assert.deepEqual(fresh,old,'unexpected register change '+key+'/'+q);
    }
  }
});
test('D129 32/48/64 simultaneous voices remain finite and within safe output range',()=>{
  for(const [q,count] of [['eco',32],['balanced',48],['studio',64]]){
    const e=new Candidate(48000,q),l=new Float32Array(128),r=new Float32Array(128);
    for(let i=0;i<count;i++)e.noteOn({id:i+1,key:21+i,speed:.65,hardness:.55,brightness:.5,character:'american',send:0});
    for(let b=0;b<120;b++){
      e.render(l,r,null,128);
      for(let i=0;i<128;i++){
        assert.ok(Number.isFinite(l[i])&&Number.isFinite(r[i]),'nonfinite polyphony');
        assert.ok(Math.abs(l[i])<=1&&Math.abs(r[i])<=1,'clipping');
      }
    }
    assert.ok(e.voices.filter(v=>v.active).length<=count,'voice cap');
  }
});
test('bass C2 CC64 sustain and release are finite and voices are bounded',()=>{
  const e=new Candidate(48000,'studio'),l=new Float32Array(128),r=new Float32Array(128);
  e.setSustain(127);e.noteOn({id:5,key:36,speed:.8,character:'american'});
  for(let b=0;b<20;b++)e.render(l,r,null,128);
  e.noteOff(5);e.setSustain(0);
  for(let b=0;b<200;b++){e.render(l,r,null,128);for(const x of l)assert.ok(Number.isFinite(x));}
  assert.ok(e.voices.filter(v=>v.active).length<=64);
});
