#!/usr/bin/env node
/** E2.9 offline Node benchmark: passive 88-key solver + Rayleigh radiator.
 * Never interpret these numbers as PC/Android/browser AudioWorklet certification.
 */
import {performance} from 'node:perf_hooks';
import {SharedPassiveModalPiano} from '../research/shared-passive-modal-piano.mjs';
import {AnalyticSoundboardRadiator} from '../research/analytic-soundboard-radiation.mjs';

const SR=48000,BLOCK=128,COUNT=120,WARM=20;
const timings=[];
for(const voices of [32,48,64]){
 const piano=new SharedPassiveModalPiano({sampleRate:SR});
 const radiation=new AnalyticSoundboardRadiator({sampleRate:SR});
 piano.setSustain(127);
 for(let i=0;i<voices;i++)piano.noteOn(21+i,{
  velocity:80+i%16,peakForce:105,contactMs:3
 });
 const times=[];
 let peak=0;
 for(let b=0;b<COUNT+WARM;b++){
  const start=performance.now();
  for(let i=0;i<BLOCK;i++){
   piano.step();
   radiation.step(piano.bridgeVelocity,piano.boardPanelVelocity);
   peak=Math.max(peak,Math.abs(radiation.left),Math.abs(radiation.right));
  }
  const ms=performance.now()-start;
  if(b>=WARM)times.push(ms);
 }
 times.sort((a,b)=>a-b);
 timings.push({
  simultaneousStruckNotes:voices,
  stringCoordinates:piano.n,boardCoordinates:2,platePatches:radiation.patchCount,
  p50BlockMs:+times[Math.floor(times.length*.5)].toFixed(5),
  p95BlockMs:+times[Math.ceil(times.length*.95)-1].toFixed(5),
  maxBlockMs:+times[times.length-1].toFixed(5),
  theoreticalBudgetMs:+(1000*BLOCK/SR).toFixed(5),
  observedRadiationPeak:peak,
  realTimeDeviceCertified:false
 });
}
console.log(JSON.stringify({
 name:'Stage E2.9 sample-free mechanical+Rayleigh offline Node benchmark',
 sampleRate:SR,blockSize:BLOCK,measurements:timings,
 warning:'CPU Node/Linux, no browser, audio callbacks, memory pressure or hardware validation'
},null,2));
