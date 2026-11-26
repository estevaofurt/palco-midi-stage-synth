import {test} from 'node:test';
import assert from 'node:assert/strict';
import {candidateModalCapacity,candidateVoiceLimit,physicalOverride,physicalLimit} from './polyphony_preview.mjs';
test('preserve default and bound experimental caps',()=>{
  assert.equal(candidateModalCapacity('auto','full',48000),32);
  assert.equal(candidateModalCapacity(256,'full',48000),192);
  assert.equal(candidateModalCapacity(192,'full',96000),64);
  assert.equal(candidateModalCapacity(192,'lite',48000),64);
  assert.equal(candidateVoiceLimit(192,64,192,false),64);
  assert.equal(candidateVoiceLimit(192,64,192,true),192);
  assert.equal(candidateVoiceLimit(32,64,32,false),32);
});

test('physical caps preserve presets and restrict expanded requests',()=>{
  assert.equal(physicalOverride('auto','full',48000),null);
  assert.equal(physicalLimit(null,'balanced'),48);
  assert.equal(physicalLimit(null,'studio'),64);
  assert.equal(physicalOverride(256,'full',48000),128);
  assert.equal(physicalOverride(192,'lite',48000),64);
  assert.equal(physicalOverride(192,'full',96000),64);
  assert.equal(physicalLimit(128,'eco'),32);
  assert.equal(physicalLimit(128,'studio'),128);
});
