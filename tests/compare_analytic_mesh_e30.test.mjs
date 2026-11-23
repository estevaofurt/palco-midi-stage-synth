import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {comparePurePhysicalMeshes,encodeMeshStereoWav16,RADIATION_MESHES_E30}
 from '../research/compare-analytic-mesh-e30.mjs';

const score=[
 {seconds:.02,type:'on',key:48,velocity:90},
 {seconds:.18,type:'on',key:55,velocity:78},
 {seconds:.30,type:'off',key:48},
 {seconds:.39,type:'off',key:55}
];
const small=()=>comparePurePhysicalMeshes({
 sampleRate:24000,seconds:.65,score
});

test('increasing Rayleigh quadrature resolution converges numerically',()=>{
 const out=small();
 assert.deepEqual(out.labels,['8x6','12x8','16x12']);
 assert.deepEqual(out.diagnostics.patches,[48,96,192]);
 assert.ok(out.relativeErrors[0]>out.relativeErrors[1],
  '8x6 should differ more from 16x12 than 12x8');
 assert.ok(out.relativeErrors[1]>0);
 assert.equal(out.relativeErrors[2],0);
 assert.equal(out.diagnostics.onlySurfaceQuadratureChanged,true);
 assert.equal(out.diagnostics.humanPerceptualImprovementDemonstrated,false);
});

test('all meshes share same 88-key passive input and non-silent output',()=>{
 const out=small();
 assert.equal(out.diagnostics.connectedKeys,88);
 assert.equal(out.diagnostics.stringCoordinates,592);
 assert.equal(out.diagnostics.boardCoordinates,2);
 assert.equal(out.diagnostics.sampleFree,true);
 assert.ok(out.peak>0&&out.globalListeningGain>0);
 assert.equal(out.results.length,3);
 for(const mesh of out.results){
  assert.equal(mesh.diagnostics.sampleFree,true);
  assert.ok(mesh.diagnostics.energyBalanceRelativeError<1e-7);
 }
});

test('global-gain stereo WAV remains below clipping on all mesh variants',()=>{
 const out=small();
 for(const mesh of out.results){
  const wav=encodeMeshStereoWav16(mesh.left,mesh.right,24000,out.globalListeningGain);
  assert.equal(wav.toString('ascii',0,4),'RIFF');
  assert.equal(wav.readUInt16LE(22),2);
  assert.equal(wav.readUInt32LE(24),24000);
  let peak=0;for(let p=44;p<wav.length;p+=2)peak=Math.max(peak,Math.abs(wav.readInt16LE(p)));
  assert.ok(peak>0&&peak<=26870);
 }
});

test('score and mesh errors are fail closed, no recorded audio source used',()=>{
 assert.throws(()=>comparePurePhysicalMeshes({meshes:[{columns:1,rows:1}]}),RangeError);
 assert.throws(()=>comparePurePhysicalMeshes({score:[{
  seconds:.02,type:'on',key:190
 }],seconds:.7,sampleRate:24000}),RangeError);
 assert.throws(()=>encodeMeshStereoWav16(
  new Float64Array([NaN]),new Float64Array([0]),24000,1),RangeError);
 const source=readFileSync(new URL('../research/compare-analytic-mesh-e30.mjs',import.meta.url),'utf8');
 assert.doesNotMatch(source,/^import .*(sample-library|piano-bank|sf2-reader|\.wav)/gm);
 assert.equal(RADIATION_MESHES_E30.length,3);
});
