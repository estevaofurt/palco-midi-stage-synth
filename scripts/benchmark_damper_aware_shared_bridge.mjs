/**
 * Offline, isolated Schur O(88) solver profile, NOT AudioWorklet real-time certification.
 * node scripts/benchmark_damper_aware_shared_bridge.mjs
 */
import {performance} from 'node:perf_hooks';
import {DamperAwareSharedBridge} from '../research/damper-aware-shared-bridge.mjs';
const cases=[32,48,64],BLOCK=128,RUNS=180,WARMUP=50;
const rows=[];
for(const notes of cases){
 const s=new DamperAwareSharedBridge({sampleRate:48000,coupling:.12});
 for(let k=0;k<notes;k++){
   s.noteOn(21+k);
   s.strike(21+k,{displacement:.000001});
 }
 const durations=[];
 for(let j=0;j<RUNS+WARMUP;j++){
   const start=performance.now();
   for(let i=0;i<BLOCK;i++)s.step();
   const dt=performance.now()-start;
   if(j>=WARMUP)durations.push(dt);
 }
 durations.sort((a,b)=>a-b);
 const median=durations[Math.floor(durations.length*.5)];
 const p95=durations[Math.floor(durations.length*.95)];
 rows.push({notes,allPhysicalStrings:88,blockFrames:BLOCK,budgetMs:BLOCK/48,
   medianMs:+median.toFixed(5),p95Ms:+p95.toFixed(5),
   approximateBudgetFraction:+(p95/(BLOCK/48)).toFixed(4),
   finite:Number.isFinite(s.energy())});
}
console.log(JSON.stringify({description:'Research passive solver only: no synth, fx, UI, browser callback',rows},null,2));
if(rows.some(r=>!r.finite))process.exitCode=1;
