/**
 * CPU comparison: one shared two-mode plate versus independent 4-DOF
 * cells per string/note. Only a Node/Linux microbenchmark.
 */
import {performance} from 'node:perf_hooks';
import {SharedPassivePianoBridge} from '../research/shared-passive-piano-bridge.mjs';
import {PassiveStringBridgeCell} from '../research/passive-string-bridge-cell.mjs';
const SR=48000,BLOCK=128;
const round=x=>Number(x.toFixed(4));
const percentile=(a,q)=>a[Math.floor((a.length-1)*q)];
function runShared(notes){
 const keys=Array.from({length:notes},(_,i)=>21+i%28);
 const p=new SharedPassivePianoBridge({sampleRate:SR,keys,coupling:.12});
 for(let i=0;i<p.n;i+=3)p.setInitialStringDisplacement(i,.00002);
 return benchmark('shared',notes,()=>{
   let out=0;
   for(let i=0;i<BLOCK;i++)out+=p.step();
   return out;
 });
}
function runIndependent(notes){
 const cells=Array.from({length:notes},(_,i)=>{
   const p=new PassiveStringBridgeCell({sampleRate:SR,key:21+i%28,coupling:.12});
   p.setInitialDisplacement(0,.00002);
   return p;
 });
 return benchmark('independent',notes,()=>{
   let out=0;
   for(let i=0;i<BLOCK;i++)
     for(let c=0;c<cells.length;c++)out+=cells[c].step();
   return out;
 });
}
function benchmark(architecture,notes,fn){
 for(let i=0;i<125;i++)fn();
 const arr=[];
 let checksum=0;
 for(let i=0;i<360;i++){
   const t=performance.now(),y=fn();
   arr.push(performance.now()-t);
   checksum+=y*y;
 }
 if(!Number.isFinite(checksum))throw Error('nonfinite mechanical output');
 arr.sort((a,b)=>a-b);
 return {architecture,notes,blockTimeMs:round(BLOCK/SR*1000),
   meanMs:round(arr.reduce((s,x)=>s+x,0)/arr.length),
   p95Ms:round(percentile(arr,.95)),p99Ms:round(percentile(arr,.99)),
   worstMs:round(arr.at(-1)),finite:true};
}
const results=[];
for(const n of [16,32,64]){
 results.push(runShared(n));
 results.push(runIndependent(n));
}
console.log('SHARED_BRIDGE_CPU '+JSON.stringify({
 schema:'stage-shared-passive-bridge-v1',
 environment:'Node/Linux microbenchmark; NOT AudioWorklet/Android',
 note:'Different numerical topologies: cost comparison, NOT identical acoustic response. Current Stage D also costs CPU in a real browser.',
 results
}));
for(const r of results)console.log('CELL '+JSON.stringify(r));
