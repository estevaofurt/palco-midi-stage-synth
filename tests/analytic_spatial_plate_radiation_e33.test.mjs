import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {AnalyticSpatialPlateRadiatorE33}
 from '../research/analytic-spatial-plate-radiation-e33.mjs';

const params={sampleRate:24000,columns:4,rows:4,
 plateWidthM:.3,plateHeightM:.2,
 microphones:[{x:-.3,y:0,z:1},{x:.3,y:0,z:1}],
 shapes:[[1,1],[2,1]]};

test('zero moving surface produces exactly zero audible relative pressure',()=>{
 const r=new AnalyticSpatialPlateRadiatorE33(params);
 for(let i=0;i<500;i++){
  r.step(new Float64Array([0,0]));
  assert.equal(r.left,0);assert.equal(r.right,0);
 }
 r.reset();assert.equal(r.left,0);
});

test('radiation from all spatial modes is causal after geometric r/c delay',()=>{
 const r=new AnalyticSpatialPlateRadiatorE33(params);
 const minDelay=Math.min(...Array.from(r.delays));
 for(let i=0;i<minDelay;i++){
  r.step(new Float64Array([i===0?.001:0,0]));
  assert.equal(r.left,0);assert.equal(r.right,0);
 }
 let peak=0;
 for(let i=0;i<15;i++){
  r.step(new Float64Array([0,0]));
  peak=Math.max(peak,Math.abs(r.left),Math.abs(r.right));
 }
 assert.ok(peak>0);
});

test('symmetric and antisymmetric physical panel modes yield appropriate stereo',()=>{
 const even=new AnalyticSpatialPlateRadiatorE33(params);
 const odd=new AnalyticSpatialPlateRadiatorE33(params);
 let evenDiff=0,evenEnergy=0,oddSum=0,oddEnergy=0;
 for(let i=0;i<3000;i++){
  const v=.001*Math.sin(2*Math.PI*210*i/24000);
  even.step(new Float64Array([v,0]));
  odd.step(new Float64Array([0,v]));
  if(i>250){
   evenDiff+=Math.abs(even.left-even.right);
   oddSum+=Math.abs(odd.left+odd.right);
   evenEnergy+=Math.abs(even.left)+Math.abs(even.right);
   oddEnergy+=Math.abs(odd.left)+Math.abs(odd.right);
  }
 }
 assert.ok(evenEnergy>0&&oddEnergy>0);
 assert.ok(evenDiff/evenEnergy<1e-11);
 assert.ok(oddSum/oddEnergy<1e-11);
});

test('pressure is proportional to plate-mode vibration amplitude',()=>{
 const a=new AnalyticSpatialPlateRadiatorE33(params);
 const b=new AnalyticSpatialPlateRadiatorE33(params);
 for(let i=0;i<450;i++){
  const value=.001*Math.sin(2*Math.PI*180*i/24000);
  a.step(new Float64Array([value,value*.5]));
  b.step(new Float64Array([value*3,value*1.5]));
  assert.ok(Math.abs(a.left*3-b.left)<1e-10);
  assert.ok(Math.abs(a.right*3-b.right)<1e-10);
 }
});

test('no sampled piano, recorded impulse, SF2 or PCM audio enters analytic model',()=>{
 const src=readFileSync(
  new URL('../research/analytic-spatial-plate-radiation-e33.mjs',import.meta.url),'utf8');
 assert.doesNotMatch(src,/^import .*sample-library|^import .*\.wav|decodeAudioData|createConvolver/gm);
 assert.throws(()=>new AnalyticSpatialPlateRadiatorE33({...params,columns:100}),RangeError);
 assert.throws(()=>new AnalyticSpatialPlateRadiatorE33({...params,shapes:[[0,1]]}),RangeError);
 const r=new AnalyticSpatialPlateRadiatorE33(params);
 assert.throws(()=>r.step(new Float64Array([1])),RangeError);
 assert.throws(()=>r.step(new Float64Array([1,NaN])),TypeError);
});
