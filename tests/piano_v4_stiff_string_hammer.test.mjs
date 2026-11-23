import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {StiffStringHammerV4}
 from '../research/piano-v4/stiff-string-hammer.mjs';

function run(velocity,steps=4800,params={}){
 const piano=new StiffStringHammerV4({
  hammerInitialVelocityMps:velocity,...params
 });
 let bridgePeak=0,firstContactStart=-1,firstContactMs=0,firstEnded=false;
 for(let i=0;i<steps;i++){
  bridgePeak=Math.max(bridgePeak,Math.abs(piano.step()));
  if(piano.contactForceN>0&&firstContactStart<0&&!firstEnded)
   firstContactStart=i;
  if(piano.contactForceN===0&&firstContactStart>=0&&!firstEnded){
   firstContactMs=(i-firstContactStart)*1000/piano.sampleRate;
   firstEnded=true;
  }
 }
 return {piano,bridgePeak,firstContactMs};
}
test('steel geometry determines positive C4 tension and stiffness',()=>{
 const p=new StiffStringHammerV4();
 assert.equal(p.n,32);
 assert.ok(p.tensionN>450&&p.tensionN<800);
 assert.ok(p.modalMassKg>.001&&p.modalMassKg<.003);
 assert.ok(p.inharmonicityB>0&&p.inharmonicityB<.002);
 assert.ok(Math.abs(p.frequenciesHz[0]-261.625565)<1e-8);
});
test('stiff-string partials follow physical dispersion, not ad-hoc detuning',()=>{
 const p=new StiffStringHammerV4();
 for(let i=1;i<p.n;i++){
  const n=i+1,ratio=p.frequenciesHz[i]/(n*p.frequenciesHz[0]);
  const expected=Math.sqrt((1+p.inharmonicityB*n*n)/
   (1+p.inharmonicityB));
  assert.ok(Math.abs(ratio-expected)<1e-12);
  assert.ok(ratio>1);
  assert.ok(p.frequenciesHz[i]<.42*p.sampleRate);
 }
});
test('hammer strike position creates geometrical eighth-partial node',()=>{
 const p=new StiffStringHammerV4({hammerStrikeFraction:.125});
 assert.ok(Math.abs(p.strikeShapes[7])<1e-13);
 assert.ok(Math.abs(p.strikeShapes[6])>.1);
});
test('zero hammer velocity is exactly silent, not a free-running synth',()=>{
 const {piano:p,bridgePeak}=run(0,3500);
 assert.equal(p.peakContactForceN,0);
 assert.equal(p.contactSamples,0);
 assert.equal(p.dissipatedJ,0);
 assert.equal(p.totalEnergyJ(),0);
 assert.equal(p.relativeEnergyBalance(),0);
 assert.equal(bridgePeak,0);
});
test('faster hammer produces stronger and shorter FIRST physical contact',()=>{
 const soft=run(.8),hard=run(3.8);
 assert.ok(soft.piano.peakContactForceN>0);
 assert.ok(hard.piano.peakContactForceN>
  soft.piano.peakContactForceN*3);
 assert.ok(hard.firstContactMs>0&&soft.firstContactMs>0);
 assert.ok(hard.firstContactMs<soft.firstContactMs);
 assert.ok(hard.bridgePeak>soft.bridgePeak);
});
test('hammer-string-contact energy is conserved with positive loss',()=>{
 for(const velocity of [.8,1.5,2.5,3.8]){
  const {piano:p}=run(velocity,5000);
  assert.ok(p.dissipatedJ>0);
  assert.ok(p.totalEnergyJ()<p.initialEnergyJ);
  assert.ok(Math.abs(p.relativeEnergyBalance())<1e-8,
   'energy at '+velocity+'m/s: '+p.relativeEnergyBalance());
 }
});
test('passivity survives 44.1 and 96 kHz',()=>{
 for(const sampleRate of [44100,96000]){
  const {piano:p}=run(2,Math.round(.075*sampleRate),{sampleRate});
  assert.ok(p.peakContactForceN>0);
  assert.ok(Math.abs(p.relativeEnergyBalance())<1e-8);
 }
});
test('same initial conditions are bit-exact and deterministic',()=>{
 const x=run(1.5,2000),y=run(1.5,2000);
 assert.deepEqual(x.piano.q,y.piano.q);
 assert.deepEqual(x.piano.v,y.piano.v);
 assert.equal(x.piano.peakContactForceN,y.piano.peakContactForceN);
});
test('unphysical geometry and contact settings fail closed',()=>{
 for(const opts of [
  {sampleRate:8000},{numberOfModes:2},{radiusM:0},
  {lengthM:-1},{densityKgM3:-10},{targetFundamentalHz:9000},
  {hammerStrikeFraction:1},{hammerMassKg:0},{feltScale:0},
  {feltExponent:1},{hammerInitialVelocityMps:NaN},
  {youngModulusPa:4e11,radiusM:.002,lengthM:.15,targetFundamentalHz:28}
 ])assert.throws(()=>new StiffStringHammerV4(opts),RangeError);
});
test('new single-note mechanical engine imports no old DSP or recorded audio',()=>{
 const src=readFileSync(
  new URL('../research/piano-v4/stiff-string-hammer.mjs',import.meta.url),
  'utf8'
 );
 assert.doesNotMatch(src,/^import\s+/m);
 assert.doesNotMatch(src,
  /sample-library|\.wav|\.sf2|readFile|fetch\(|decodeAudioData|createConvolver/);
});
