import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {HybridPianoEngine as NewD} from '../physical-piano-hybrid.js';
import {HybridPianoEngine as ArchivedD} from '../physical-piano-hybrid-v126.js';

const read=path=>readFileSync(new URL(path,import.meta.url),'utf8');
function block(Model,key){
  const e=new Model(48000,'eco');
  e.noteOn({id:5,key,speed:.78,character:'american',hardness:.5});
  const l=new Float32Array(128),r=new Float32Array(128);
  e.render(l,r,null,128);
  return Array.from(l);
}
test('v1.12.6 historic D has independent immutable engine and calibration imports',()=>{
 const old=read('../physical-piano-hybrid-v126.js');
 const now=read('../physical-piano-hybrid.js');
 assert.match(old,/piano-hybrid-calibration-v126\.js/);
 assert.match(old,/piano-resonance-v126\.js/);
 assert.doesNotMatch(old,/prepareBassContact/);
 assert.match(now,/prepareBassContact/);
 assert.match(read('../acoustic.js'),/endsWith\('\/v1\.12\.6\.html'\)/);
 assert.match(read('../acoustic.js'),/physical-piano-hybrid-v126\.js\?build=1\.12\.6/);
 assert.match(read('../acoustic.js'),/physical-piano-hybrid\.js\?build=1\.12\.7/);
});
test('historical and new D engines produce identical C4–C6 exact PCM',()=>{
 for(const key of [60,72,84])
  assert.deepEqual(block(NewD,key),block(ArchivedD,key),'C4-C6 must match '+key);
});
test('historical and new D bass engines are independently audible candidates',()=>{
 for(const key of [24,36,48]){
  const a=block(NewD,key),b=block(ArchivedD,key);
  assert.notDeepEqual(a,b,'new temporal bass physics must not be a renamed old engine');
  assert.ok(a.some(x=>Math.abs(x)>1e-8),'bass must be audible');
 }
});
