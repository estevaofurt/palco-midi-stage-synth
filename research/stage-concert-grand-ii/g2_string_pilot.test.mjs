import assert from 'node:assert/strict';
import {PILOT_KEYS,DESIGN,StringPilot,wireFor} from './g2_string_pilot.mjs';
import {StiffString,stringMode} from '../stage-concert-grand/stiff-string.mjs';
import {modalCoefficients} from '../stage-concert-grand/exact-modal.mjs';
let cases=0;
for(const key of PILOT_KEYS){
 const w=wireFor(key);
 assert(Math.abs(1200*Math.log2(stringMode(w,1).frequencyHz/w.f1Hz))<1e-8);
 assert(w.tensionN>0&&w.B>0&&w.stressPa>0);
 for(const sr of [44100,48000,96000]){
  const s=new StringPilot(key,sr),ref=new StiffString(w,{sampleRate:sr,maxFrequencyHz:s.cutoffHz,maxModes:DESIGN.maxModes,sigma0PerS:DESIGN.sigma0PerS,sigma2M2PerS:DESIGN.sigma2M2PerS},modalCoefficients);
  const weights=ref.weights(w.lengthM*DESIGN.strikeFraction,DESIGN.widthM);
  assert.equal(s.modes.length,ref.modes.length);
  assert.equal(s.modes.length,({48:67,60:38,84:13})[key]);
  let maxX=0,maxV=0,minLoss=0,peakX=0;
  for(let i=0;i<sr/4;i++){
   const f=i<.002*sr?.3:i>=.05*sr&&i<.052*sr?.15:0;
   const e=s.energy(),work=s.workJ;s.step(f);ref.step(weights,f);
   maxX=Math.max(maxX,Math.abs(s.displacement()-ref.projection(weights)));
   maxV=Math.max(maxV,Math.abs(s.velocity()-ref.projection(weights,ref.v)));
   minLoss=Math.min(minLoss,s.workJ-work+e-s.energy());peakX=Math.max(peakX,Math.abs(s.displacement()));
  }
  assert(maxX<1e-10&&maxV<1e-8);assert(minLoss>=-1e-12&&s.lossJ>=0);assert(peakX>0);
  assert(Math.abs(s.workJ-s.lossJ-s.energy())<1e-10);
  console.log('G2_STRING '+JSON.stringify({key,sr,lengthM:w.lengthM,tensionN:w.tensionN,linearDensityKgM:w.linearDensityKgM,B:w.B,f1Hz:w.f1Hz,stressPa:w.stressPa,modes:s.modes.length,maxX,maxV,minLoss,peakX,workJ:s.workJ,lossJ:s.lossJ,remainingJ:s.energy(),provenance:w.provenance}));cases++;
 }
}
assert.throws(()=>new StringPilot(61),/key/);
assert.throws(()=>new StringPilot(60,22050),/rate/);
const s=new StringPilot(60);assert.throws(()=>s.step(NaN),/force/);
console.log('G2_STRING_PASS',cases);
