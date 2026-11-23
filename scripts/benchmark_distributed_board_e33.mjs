#!/usr/bin/env node
/** E3.3 offline CPU of 88 passive strings + 2/4/8 spatial panel modes.
 * 32/48/64 struck notes use the legacy known bounded force pulse as a
 * baseline. They do NOT represent 32/48/64 simultaneous reactive hammers.
 * Not a real-time AudioWorklet, Windows or Android certification.
 */
import {performance} from 'node:perf_hooks';
import {PassiveDistributedSoundboardE33}
 from '../research/passive-distributed-soundboard-e33.mjs';

const RATE=48000,BLOCK=128,SAMPLES=160,WARM=40;
const report=[];
for(const panels of [2,4,8]){
 for(const struckNotes of [32,48,64]){
  const p=new PassiveDistributedSoundboardE33({
   sampleRate:RATE,panelModes:panels
  });
  p.setSustain(127);
  for(let i=0;i<struckNotes;i++){
   p.noteOn(21+i,{velocity:75+i%23,peakForce:80});
  }
  let max=0;
  const times=[];
  for(let block=0;block<WARM+SAMPLES;block++){
   const start=performance.now();
   for(let sample=0;sample<BLOCK;sample++){
    const modes=p.step();
    for(let j=0;j<modes.length;j++)
     max=Math.max(max,Math.abs(modes[j]));
   }
   if(block>=WARM)times.push(performance.now()-start);
  }
  times.sort((a,b)=>a-b);
  report.push({
   struckNotes,connectedKeys:88,stringModes:p.n,plateModes:panels,
   bridgePointModes:1,processedPhysicalDoFs:p.n+panels+1,
   p50Ms:+times[Math.floor(times.length*.5)].toFixed(5),
   p95Ms:+times[Math.ceil(times.length*.95)-1].toFixed(5),
   theoreticalBlockBudgetMs:+(1000*BLOCK/RATE).toFixed(5),
   peakPanelVelocityProxy:max,
   energyBalanceRelativeError:Math.abs(p.energyBalanceError())/
    Math.max(1,p.externalWork),
   testedSimultaneousReactiveHammers:0,
   realTimeDeviceCertified:false
  });
 }
}
console.log(JSON.stringify({
 stage:'E3.3 offline distributed soundboard Schur/Cholesky',
 sampleRate:RATE,framesPerBlock:BLOCK,measurements:report,
 caveat:'The 32/48/64 strikes are legacy fixed pulses, NOT reactive multi-hammer polyphony; no radiated air, browser, FX or real-time certification.'
},null,2));
