import {test} from 'node:test';
import assert from 'node:assert/strict';
import {parsePolyphony,resolvePolyphony} from './polyphony_policy.mjs';
test('legacy profiles and bad preferences',()=>{
  assert.equal(resolvePolyphony('auto',{profile:'full'}).effective,64);
  assert.equal(resolvePolyphony('auto').effective,32);
  for(const x of [0,999,NaN,'128x',{},true,' 128'])assert.equal(parsePolyphony(x),'auto');
});
test('independent engine and verified limits',()=>{
  assert.equal(resolvePolyphony(256,{profile:'full',engineCapacity:32,verifiedCapacity:256}).effective,32);
  assert.equal(resolvePolyphony(128,{profile:'full',engineCapacity:256,verifiedCapacity:96}).effective,96);
  assert.equal(resolvePolyphony(128,{profile:'full',engineCapacity:256,verifiedCapacity:128}).effective,128);
  assert.equal(resolvePolyphony(256,{profile:'full',engineCapacity:256}).effective,64);
});
