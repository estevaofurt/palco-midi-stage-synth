import test from 'node:test';
import assert from 'node:assert/strict';
import {HybridPianoEngine as Current} from '../physical-piano-hybrid.js';
import {HybridPianoEngine as Archived} from '../physical-piano-hybrid-v127.mjs';

// 88-key guard for the deliberately narrow v1.12.8 D change.
// Acoustic improvement itself requires independent listening and instrument checks.
const render=(Engine,key,quality)=>{
  const engine=new Engine(48000,quality);
  engine.noteOn({id:1,key,speed:80/127,hardness:.55,brightness:.5,
    character:'american',send:0});
  const left=new Float32Array(128),right=new Float32Array(128);
  const result=new Float32Array(128*2*8);
  for(let block=0;block<8;block++){
    engine.render(left,right,null,128);
    for(let i=0;i<128;i++){
      result[(block*128+i)*2]=left[i];
      result[(block*128+i)*2+1]=right[i];
    }
  }
  return result;
};

test('D v1.12.8 changes exactly F1–C2, across all 88 keys and 32/48/64 caps',()=>{
  for(const quality of ['eco','balanced','studio']){
    for(let key=21;key<=108;key++){
      const oldPCM=render(Archived,key,quality);
      const nowPCM=render(Current,key,quality);
      for(const value of nowPCM)assert.ok(Number.isFinite(value),`nonfinite ${key}/${quality}`);
      if(key>=29&&key<=36){
        assert.notDeepEqual(nowPCM,oldPCM,`expected changed F1–C2: ${key}/${quality}`);
      }else{
        assert.deepEqual(nowPCM,oldPCM,`unexpected regression: ${key}/${quality}`);
      }
    }
  }
});
