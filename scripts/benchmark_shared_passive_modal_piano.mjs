/** E2.3 O(N) modal-string research benchmark. NOT Stage Worklet/full chain. */
import {performance} from 'node:perf_hooks';
import {SharedPassiveModalPiano} from '../research/shared-passive-modal-piano.mjs';
const SAMPLE_RATE=48000, BLOCK=128, LOOPS=180, WARMUP=50;
const results=[];
for(const notes of [32,48,64]){
 const p=new SharedPassiveModalPiano({sampleRate:SAMPLE_RATE,partialsBass:5,partialsTreble:2,coupling:.12});
 const buf=new Float32Array(BLOCK),durations=[];
 for(let i=0;i<notes;i++)p.noteOn(21+i,{peakForce:30,velocity:74});
 for(let j=0;j<LOOPS+WARMUP;j++){
  const start=performance.now();
  p.render(buf);
  if(j>=WARMUP)durations.push(performance.now()-start);
 }
 durations.sort((a,b)=>a-b);
 const p95=durations[Math.floor(durations.length*.95)];
 results.push({pressedKeys:notes,physicallyConnectedKeys:88,
  stringCoordinates:p.n,sharedBoardCoordinates:2,sampleRate:SAMPLE_RATE,
  medianMs:+durations[Math.floor(durations.length/2)].toFixed(5),
  p95Ms:+p95.toFixed(5),fractionOf128FrameBudget:+(p95/(BLOCK/SAMPLE_RATE*1000)).toFixed(5),
  energyBalanceError:p.energyBalanceError(),finite:Number.isFinite(p.energy())});
}
console.log(JSON.stringify({scope:'Node/Linux mechanical solver ONLY, no D/FX/AudioWorklet/pressure',results},null,2));
if(results.some(x=>!x.finite||!Number.isFinite(x.energyBalanceError)||Math.abs(x.energyBalanceError)>1e-5))process.exitCode=1;
