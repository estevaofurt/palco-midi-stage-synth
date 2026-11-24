import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {noteParamsV10,modeFrequencyHz} from './c3x-scale-v10.mjs';
const fixture=JSON.parse(readFileSync(new URL('./v10-scale-python-reference.json',import.meta.url),'utf8'));

function assertClose(a,b,name,midi){
  const diff=Math.abs(a-b),tol=1e-11 * Math.max(1,Math.abs(b));
  assert.ok(diff<=tol,`MIDI ${midi} ${name}: JS ${a} vs Python ${b}; diff ${diff}`);
}

test('paridade 88/88: parâmetros JS reproduzem os do Python V10',()=>{
  assert.equal(fixture.length,88);
  for(const original of fixture){
    const js=noteParamsV10(original.midi);
    for(const [key,v] of Object.entries(original)) {
      if(typeof v==='number') assertClose(js[key],v,key,original.midi);
      else assert.deepEqual(js[key],v,`MIDI ${original.midi}: ${key}`);
    }
    assert.equal(Object.keys(js).length,Object.keys(original).length);
  }
});

test('A4 coincide em 440 Hz com temperamento igual',()=>{
  assertClose(noteParamsV10(69).frequencyHz,440,'A4',69);
  assertClose(modeFrequencyHz(noteParamsV10(69),1),440,'parcial 1',69);
});

test('cordas graves e agudas respeitam contagens estimadas sem interpolar a descontinuidade de ponte',()=>{
  assert.equal(noteParamsV10(32).strings,1);
  assert.equal(noteParamsV10(33).strings,2);
  assert.equal(noteParamsV10(49).strings,2);
  assert.equal(noteParamsV10(50).strings,3);
  assert.ok(noteParamsV10(47).lengthM>noteParamsV10(46).lengthM);
  assert.equal(noteParamsV10(49).wound,true);
  assert.equal(noteParamsV10(50).wound,false);
});

test('inharmonicidade positiva e parciais superiores acima de múltiplos inteiros',()=>{
  for(const midi of [21,42,69,88,108]) {
    const p=noteParamsV10(midi);
    assert.ok(p.inharmonicityB>0);
    assert.ok(modeFrequencyHz(p,3)>p.frequencyHz*3);
  }
});

test('fonte estimada explicitamente identificada e MIDI inválido rejeitado',()=>{
  assert.match(noteParamsV10(69).origin,/NAO medida do Yamaha C3X/);
  for(const value of [20,109,69.4,NaN,'69']) assert.throws(()=>noteParamsV10(value),RangeError);
  assert.throws(()=>modeFrequencyHz(noteParamsV10(69),0),RangeError);
});