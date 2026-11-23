#!/usr/bin/env node
/* E3.0 offline Node/Linux microbenchmark: NOT browser/AudioWorklet approval. */
import {performance} from 'node:perf_hooks';
import {SharedPassiveModalPiano} from '../research/shared-passive-modal-piano.mjs';
import {AnalyticSoundboardRadiator} from '../research/analytic-soundboard-radiation.mjs';

const rate=48000,block=128,measure=120,warmup=20,result=[];
for(const patches of [[8,6],[12,8],[16,12]]){
 for(const voices of [32,48,64]){
  const piano=new SharedPassiveModalPiano({sampleRate:rate});
  const radiator=new AnalyticSoundboardRadiator({
   sampleRate:rate,columns:patches[0],rows:patches[1]
  });
  piano.setSustain(127);
  for(let i=0;i<voices;i++)piano.noteOn(21+i,{velocity:80,peakForce:105});
  const times=[];
  for(let blockIndex=0;blockIndex<measure+warmup;blockIndex++){
   const t=performance.now();
   for(let i=0;i<block;i++){
    piano.step();
    radiator.step(piano.bridgeVelocity,piano.boardPanelVelocity);
   }
   if(blockIndex>=warmup)times.push(performance.now()-t);
  }
  times.sort((a,b)=>a-b);
  result.push({
   numberOfNotes:voices,patches:radiator.patchCount,connectedKeys:88,
   solverCoordinates:piano.n+2,
   p95Ms:+times[Math.ceil(times.length*.95)-1].toFixed(5),
   idealBlockMs:+(1000*block/rate).toFixed(5),
   browserCertified:false
  });
 }
}
console.log(JSON.stringify({
 label:'E3.0 88-key + 48/96/192 patch Rayleigh CPU offline Node only',
 sampleRate:rate,block,results:result
},null,2));
