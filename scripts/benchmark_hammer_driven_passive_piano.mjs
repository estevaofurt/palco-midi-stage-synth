/**
 * E2.1 hammer-driven bridge performance: no webaudio/FX/Stage voices.
 * Runs actual hammer force scheduling + passive 88-key bridge in Node.
 * ms per 128-frame block, not a real-time PC/Android certification.
 */
import {performance} from 'node:perf_hooks';
import {HammerDrivenPassivePiano} from '../research/hammer-driven-passive-piano.mjs';
const RATE=48000, BLOCK=128, MEASURE=180, WARMUP=60;
const results=[];
for(const voices of [32,48,64]){
 const p=new HammerDrivenPassivePiano({sampleRate:RATE,coupling:.12});
 const output=new Float32Array(BLOCK);
 for(let j=0;j<voices;j++)p.noteOn(21+j,{velocity:80,contactMs:3,peakForce:30});
 const durations=[];
 for(let block=0;block<MEASURE+WARMUP;block++){
  if(block===MEASURE>>1){
   // A second hammer event after first contacts have decayed.
   for(let j=0;j<voices;j++)p.noteOn(21+j,{velocity:80,contactMs:3,peakForce:30});
  }
  const t0=performance.now();
  p.render(output);
  const elapsed=performance.now()-t0;
  if(block>=WARMUP)durations.push(elapsed);
 }
 durations.sort((a,b)=>a-b);
 const median=durations[Math.floor(durations.length*.5)];
 const p95=durations[Math.floor(durations.length*.95)];
 results.push({voices,physicalKeys:88,mechanicalCoordinates:176,
   frameCount:BLOCK,sampleRate:RATE,
   blockBudgetMs:BLOCK/RATE*1000,
   medianMs:+median.toFixed(5),p95Ms:+p95.toFixed(5),
   budgetFraction:+(p95/(BLOCK/RATE*1000)).toFixed(4),
   energyBalanceError:p.energyBalanceError(),
   energyFinite:Number.isFinite(p.bridge.energy()),
   externalWorkPositive:p.bridge.externalWork>0});
}
console.log(JSON.stringify({description:'Node-only E2.1 hammer schedule plus 88-key shared bridge; no D, browser or FX',results},null,2));
if(results.some(x=>!x.energyFinite||!x.externalWorkPositive||
                     !Number.isFinite(x.energyBalanceError)||
                     Math.abs(x.energyBalanceError)>1e-5))process.exitCode=1;
