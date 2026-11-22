import test from 'node:test';
import assert from 'node:assert/strict';
import {defaultProfile,getProfile,profilePolyphony} from '../audio-profile.js';
import {engines,loadState} from '../patches.js';

test('Moto g04s entra em modo leve, computadores permanecem completos',()=>{
  assert.equal(defaultProfile({userAgent:'Mozilla/5.0 (Linux; Android 14; moto g04s) Chrome/131 Mobile'}),'lite');
  assert.equal(defaultProfile({userAgent:'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131',hardwareConcurrency:8}),'full');
  assert.equal(defaultProfile({userAgent:'Linux Chrome',deviceMemory:3}),'lite');
  assert.equal(getProfile({getItem:()=> 'full'},{userAgent:'Android'}),'full');
  assert.equal(getProfile({getItem:()=> 'lite'},{userAgent:'Windows'}),'lite');
});
test('limite de vozes e bypass preservam as preferências originais',()=>{
  assert.equal(profilePolyphony('lite'),32);
  assert.equal(profilePolyphony('full'),64);
  const state=loadState(null);
  assert.ok(Object.keys(engines).length===5);
  assert.equal(state.patches.piano.values.soundEngine,'physical');
  assert.ok(Object.keys(state.fx.slots).length===8);
});
