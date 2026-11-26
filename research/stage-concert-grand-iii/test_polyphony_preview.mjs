import {test} from 'node:test';
import assert from 'node:assert/strict';
import {candidateModalCapacity,candidateVoiceLimit} from './polyphony_preview.mjs';
test('preserve default and bound experimental caps',()=>{
  assert.equal(candidateModalCapacity('auto','full',48000),32);
  assert.equal(candidateModalCapacity(256,'full',48000),192);
  assert.equal(candidateModalCapacity(192,'full',96000),64);
  assert.equal(candidateModalCapacity(192,'lite',48000),64);
  assert.equal(candidateVoiceLimit(192,64,192,false),64);
  assert.equal(candidateVoiceLimit(192,64,192,true),192);
  assert.equal(candidateVoiceLimit(32,64,32,false),32);
});
