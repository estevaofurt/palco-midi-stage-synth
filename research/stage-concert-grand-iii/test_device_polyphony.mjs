import {test} from 'node:test';
import assert from 'node:assert/strict';
import {candidates,score,recommend} from './device_polyphony_logic.mjs';
test('caps match preview constraints',()=>{
  assert.deepEqual(candidates('modal','studio','full',48000),[32,64,88,96,128,192]);
  assert.deepEqual(candidates('physical','studio','full',48000),[32,64,88,96,128]);
  assert.deepEqual(candidates('hybrid','eco','full',48000),[32]);
  assert.deepEqual(candidates('modal','studio','full',96000),[32,64]);
  assert.throws(()=>candidates('unknown','studio','full',48000));
});
test('timing margin and contiguous repeated passes',()=>{
  assert.equal(score(Array(200).fill(1),true,48000).pass,true);
  assert.equal(score([...Array(199).fill(1),3],true,48000).pass,false);
  assert.equal(score(Array(200).fill(1),false,48000).pass,false);
  assert.throws(()=>score(Array(200).fill(0),true,48000));
  const rows=[32,64,88].flatMap(n=>[0,1].map(t=>({voices:n,pass:n!==64||t===0})));
  assert.equal(recommend(rows,[32,64,88]),32);
  assert.equal(recommend([], [32]),null);
});
