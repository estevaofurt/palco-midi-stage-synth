import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {AnalyticSoundboardRadiator,encodeRelativeStereoWav16}
 from '../research/analytic-soundboard-radiation.mjs';
import {renderAnalyticPhysicalPiano}
 from '../research/pure-physical-radiation-e29.mjs';

const both={x:0,y:0,z:1};
const options={sampleRate:24000,plateWidthM:.20,plateHeightM:.20,
 columns:4,rows:4,microphoneLeft:both,microphoneRight:both};

test('Rayleigh radiator returns exact silence for silent modal velocities',()=>{
 const rad=new AnalyticSoundboardRadiator(options);
 for(let i=0;i<900;i++){
  const l=rad.step(0,0);
  assert.equal(l,0);assert.equal(rad.right,0);
 }
 rad.reset();assert.equal(rad.samples,0);
 assert.equal(rad.previous0,0);
});

test('radiation is causal and starts only after geometric travel time',()=>{
 const rad=new AnalyticSoundboardRadiator(options);
 const minTravel=Math.floor(Math.min(...Array.from(rad.delays)));
 for(let i=0;i<minTravel;i++){
  rad.step(i===0?.001:0,0);
  assert.equal(rad.left,0,'wave cannot arrive before speed-of-sound delay');
 }
 let heard=false;
 for(let i=minTravel;i<minTravel+10;i++){
  rad.step(0,0);heard||=Math.abs(rad.left)>0;
 }
 assert.ok(heard);
});

test('radiation pressure is linear with source velocity',()=>{
 const a=new AnalyticSoundboardRadiator(options);
 const b=new AnalyticSoundboardRadiator(options);
 for(let i=0;i<900;i++){
  const v=Math.sin(2*Math.PI*150*i/24000)*.003;
  a.step(v,0);b.step(v*3,0);
  assert.ok(Math.abs(b.left-3*a.left)<1e-10);
  assert.ok(Math.abs(b.right-3*a.right)<1e-10);
 }
});

test('acoustic pressure decays close to 1/r for far centered small plate',()=>{
 const near=new AnalyticSoundboardRadiator(options);
 const far=new AnalyticSoundboardRadiator({
  ...options,microphoneLeft:{x:0,y:0,z:2},microphoneRight:{x:0,y:0,z:2}
 });
 let p=0,q=0;
 for(let i=0;i<12000;i++){
  const v=Math.sin(2*Math.PI*150*i/24000)*.001;
  near.step(v,0);far.step(v,0);
  if(i>=6000){p+=near.left*near.left;q+=far.left*far.left;}
 }
 const ratio=Math.sqrt(q/p);
 assert.ok(ratio>.47&&ratio<.53,'analytic pressure 2m/1m ratio '+ratio);
});

test('symmetric ears cancel analytic antisymmetric mode but preserve symmetric mode',()=>{
 const symmetry={...options,
  microphoneLeft:{x:-.35,y:0,z:1.1},
  microphoneRight:{x:.35,y:0,z:1.1}};
 const sym=new AnalyticSoundboardRadiator(symmetry);
 const anti=new AnalyticSoundboardRadiator(symmetry);
 let symError=0,antiError=0,symLevel=0,antiLevel=0;
 for(let i=0;i<5000;i++){
  const v=.002*Math.sin(2*Math.PI*240*i/24000);
  sym.step(v,0);anti.step(0,v);
  if(i>150){
   symError+=Math.abs(sym.left-sym.right);
   symLevel+=Math.abs(sym.left)+Math.abs(sym.right);
   antiError+=Math.abs(anti.left+anti.right);
   antiLevel+=Math.abs(anti.left)+Math.abs(anti.right);
  }
 }
 assert.ok(symLevel>0&&antiLevel>0);
 assert.ok(symError/symLevel<1e-11);
 assert.ok(antiError/antiLevel<1e-11);
});

test('offline physical pipeline renders finite stereo with 88 coupled keys, no samples',()=>{
 const opts={sampleRate:24000,seconds:.65,
 score:[
  {seconds:0,type:'pedal',cc:127},
  {seconds:.04,type:'on',key:48,velocity:88},
  {seconds:.16,type:'on',key:55,velocity:92},
  {seconds:.34,type:'off',key:48},
  {seconds:.38,type:'off',key:55},
  {seconds:.45,type:'pedal',cc:0}
 ]};
 const run=renderAnalyticPhysicalPiano(opts);
 assert.ok(run.diagnostics.peakRelativePressure>0);
 assert.equal(run.diagnostics.connectedKeys,88);
 assert.equal(run.diagnostics.mechanicalStringCoordinates,592);
 assert.equal(run.diagnostics.platePatches,48);
 assert.equal(run.diagnostics.sampleFree,true);
 assert.equal(run.diagnostics.physicallyCalibrated,false);
 assert.equal(run.diagnostics.recordedImpulseResponses,0);
 assert.ok(run.diagnostics.energyBalanceRelativeError<1e-7);
 const repeat=renderAnalyticPhysicalPiano(opts);
 assert.deepEqual(run.left,repeat.left);
 assert.deepEqual(run.right,repeat.right);
});

test('stereo WAV uses one global gain, shared clip ceiling and valid PCM16 header',()=>{
 const samplesL=new Float64Array([0,.1,.8,-.2,0]);
 const samplesR=new Float64Array([0,-.2,-.4,.1,0]);
 const {wav,gain}=encodeRelativeStereoWav16(samplesL,samplesR,24000);
 assert.equal(wav.readUInt16LE(22),2);
 assert.equal(wav.readUInt16LE(34),16);
 assert.equal(wav.readUInt32LE(24),24000);
 assert.equal(wav.readUInt32LE(40),20);
 assert.equal(wav.length,64);
 assert.ok(gain>0);
 assert.throws(()=>encodeRelativeStereoWav16(new Float64Array([0,1]),new Float64Array(1),24000),RangeError);
 assert.throws(()=>encodeRelativeStereoWav16(new Float64Array([NaN]),new Float64Array([1]),24000),TypeError);
});

test('no recording/audio library imported into pure physical source chain',()=>{
 const files=[
  '../research/analytic-soundboard-radiation.mjs',
  '../research/pure-physical-radiation-e29.mjs',
  '../scripts/render_pure_physical_e29.mjs'
 ];
 const texts=files.map(file=>readFileSync(new URL(file,import.meta.url),'utf8'));
 for(const text of texts){
  assert.doesNotMatch(text,/from\s*['"][^'"]*(sample-library|piano-bank|sf2-reader|measured-radiation-adapter|\.wav)['"]/i);
  assert.doesNotMatch(text,/\b(createConvolver|decodeAudioData|readFileSync|fetch)\s*\(/);
 }
});

test('fail closed for impossible geometry, invalid velocity and invalid score',()=>{
 assert.throws(()=>new AnalyticSoundboardRadiator({...options,columns:0}),RangeError);
 assert.throws(()=>new AnalyticSoundboardRadiator({...options,microphoneLeft:{x:0,y:0,z:0}}),RangeError);
 const r=new AnalyticSoundboardRadiator(options);
 assert.throws(()=>r.step(NaN,0),TypeError);
 assert.throws(()=>renderAnalyticPhysicalPiano({seconds:0}),RangeError);
 assert.throws(()=>renderAnalyticPhysicalPiano({score:[{seconds:.1,type:'on',key:180}]}),RangeError);
 assert.throws(()=>renderAnalyticPhysicalPiano({score:[{seconds:.2,type:'on',key:50,velocity:0}]}),RangeError);
});
