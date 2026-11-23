/**
 * Node/Linux baseline for a four-degree-of-freedom bridge/string/plate network.
 * DOES NOT INCLUDE the rest of Stage Synth and DOES NOT certify AudioWorklet
 * 32-64 voice polyphony or Android audio deadlines.
 * Usage: node scripts/benchmark_passive_bridge_cell.mjs
 */
import {performance} from 'node:perf_hooks';
import {PassiveStringBridgeCell} from '../research/passive-string-bridge-cell.mjs';
const SR=48000,BLOCK=128,BLOCK_TIME_MS=BLOCK/SR*1000;
function one(count){
 const cells=Array.from({length:count},(_,i)=>{
  const p=new PassiveStringBridgeCell({sampleRate:SR,
    key:Math.round(24+24*(i%24)/24),coupling:.12});
  p.setInitialDisplacement(0,.00004*(1+i%3));
  p.setInitialDisplacement(1,-.00003);
  return p;
 });
 for(let w=0;w<150;w++)
   for(let i=0;i<BLOCK;i++)
     for(let k=0;k<count;k++)cells[k].step(0);
 const times=[],blocks=600;
 let maxAbs=0,sum=0;
 for(let b=0;b<blocks;b++){
   const t0=performance.now();
   for(let i=0;i<BLOCK;i++){
     let bridge=0;
     for(let k=0;k<count;k++)bridge+=cells[k].step(0);
     if(!Number.isFinite(bridge))throw Error('nonfinite plate velocity');
     maxAbs=Math.max(maxAbs,Math.abs(bridge));
     sum+=bridge*bridge;
   }
   times.push(performance.now()-t0);
 }
 times.sort((a,b)=>a-b);
 const mean=times.reduce((s,x)=>s+x,0)/times.length;
 const p=q=>times[Math.floor((times.length-1)*q)];
 const round=x=>Number(x.toFixed(4));
 return {simulatedCells:count,coordinates:count*4,
   modalMidpointSolvesPerSecond:count*SR,
   blockMeanMs:round(mean),blockP95Ms:round(p(.95)),
   blockP99Ms:round(p(.99)),blockWorstMs:round(times.at(-1)),
   blockDeadlineMs:round(BLOCK_TIME_MS),
   maxPlateVelocity:round(maxAbs),
   rmsPlateVelocity:round(Math.sqrt(sum/(blocks*BLOCK)))};
}
const results=[16,32,64].map(one);
const out={schema:'passive-bridge-cell-benchmark-v1',
 platform:process.platform,node:process.version,sampleRate:SR,blockFrames:BLOCK,
 limits:'Node/Linux microbenchmark of passive 4-mode cell ONLY, no Stage string-bank, no browser worklet, no FX, no rendering output',
 note:'Cell contains 4 coupled coordinates per note. Full per-note bridge network may cost more CPU than shared impedance model. Do not integrate until reduced and tested on PC/Android.',
 results};
for(const d of results)console.log('BRIDGE_CPU '+JSON.stringify(d));
console.log('BRIDGE_CPU_REPORT '+JSON.stringify(out));
