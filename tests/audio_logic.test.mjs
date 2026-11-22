import test from 'node:test';
import assert from 'node:assert/strict';
import {fallbackVelocity} from '../acoustic.js';
import {MAX_POLYPHONY} from '../stage.js';

test('piano sintetizado utiliza a curva de toque',()=>{
  const slow=fallbackVelocity(42,15), normal=fallbackVelocity(42,50), sensitive=fallbackVelocity(42,85);
  assert.ok(slow<normal && normal<sensitive,{slow,normal,sensitive});
  for(const touch of [0,50,100]){
    assert.ok(fallbackVelocity(1,touch)>0);
    assert.ok(fallbackVelocity(127,touch)<=1);
    assert.ok(fallbackVelocity(70,touch)<fallbackVelocity(110,touch));
  }
});

test('limite de polifonia permanece controlado',()=>{
  assert.equal(MAX_POLYPHONY,32);
});
