#!/usr/bin/env node
/** E3.2 88-key reciprocal felt contact CPU audit.
 * Real-time production NOT approved; offline Linux Node only.
 * Capture transient separately from after-contact cost.
 */
import {performance} from 'node:perf_hooks';
import {CoupledNonlinearHammerPiano} from '../research/coupled-nonlinear-hammers-e32.mjs';

const sampleRate=48000,block=128,blocks=56;
const metrics=[];
for(const voices of [1,8,32,48,64]){
 const synth=new CoupledNonlinearHammerPiano({sampleRate,maxHammers:64});
 synth.setSustain(127);
 // Warm JIT without changing the hammer state (no injected energy).
 for(let i=0;i<8*block;i++)synth.step();
 for(let k=0;k<voices;k++)synth.noteOn(21+k,{velocity:85});
 const timings=[];
 let maxContactSamples=0;
 for(let frame=0;frame<blocks;frame++){
  const began=performance.now(),contactStart=synth.contactSampleCount;
  for(let j=0;j<block;j++)synth.step();
  timings.push(performance.now()-began);
  maxContactSamples=Math.max(maxContactSamples,
   synth.contactSampleCount-contactStart);
 }
 const afterContact=timings.slice(12).sort((a,b)=>a-b);
 const p95Index=Math.ceil(afterContact.length*.95)-1;
 metrics.push({
  hammerCount:voices,
  continuousStringCoordinates:synth.piano.n,
  mechanicalBoardCoordinates:2,
  firstBlockContactMs:+timings[0].toFixed(5),
  peakTransientBlockMs:+Math.max(...timings.slice(0,12)).toFixed(5),
  p95PostContactMs:+afterContact[p95Index].toFixed(5),
  blockBudgetMs:+(1000*block/sampleRate).toFixed(5),
  contactSamples:synth.contactSampleCount,
  peakNormalizedContactForce:synth.peakForce,
  relativeEnergyResidual:synth.energyBalanceRelativeError(),
  includesRadiation:false,
  realTimeCertified:false
 });
}
console.log(JSON.stringify({
 label:'E3.2 two-way nonlinear hammer ↔ full 88-key network (offline)',
 sampleRate,block,metrics,
 warnings:[
  'No actual acoustic radiation, browser, hardware MIDI or FX in timing.',
  'Contact stiffness, modal mass, strings and felt are NOT calibrated SI.',
  'Results do NOT demonstrate piano timbre or 64-note real-time safety.'
 ]
},null,2));
