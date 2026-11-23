/**
 * Offline research tradeoff: structural mechanical complexity versus CPU
 * and normalized board response. NOT audible pressure or piano quality.
 */
import {performance} from 'node:perf_hooks';
import {SharedPassiveModalPiano} from '../research/shared-passive-modal-piano.mjs';
const RATE=48000,BLOCK=128,LOOPS=130,WARMUP=40;
const configurations=[
 {name:'light-3bass-2treble',partialsBass:3,partialsTreble:2},
 {name:'reference-5bass-2treble',partialsBass:5,partialsTreble:2},
 {name:'heavy-6bass-3treble',partialsBass:6,partialsTreble:3}
];
function render(config){
 const p=new SharedPassiveModalPiano({sampleRate:RATE,...config});
 const frames=RATE;const result=new Float64Array(frames);
 p.noteOn(36,{velocity:80,peakForce:100,contactMs:3.5});
 for(let pos=0;pos<frames;pos++)result[pos]=p.step();
 return {signal:result,n:p.n,energyError:p.energyBalanceError()};
}
function correlation(a,b){
 let aa=0,bb=0,ab=0,difference=0;
 for(let i=0;i<a.length;i++){
  aa+=a[i]*a[i];bb+=b[i]*b[i];ab+=a[i]*b[i];
  difference+=(a[i]-b[i])**2;
 }
 return {correlation:ab/Math.sqrt(aa*bb),
  differenceRms:Math.sqrt(difference/a.length),
  referenceRms:Math.sqrt(aa/a.length)};
}
const responses=configurations.map(render);
const rows=[];
for(let i=0;i<configurations.length;i++){
 const conf=configurations[i],engine=new SharedPassiveModalPiano({sampleRate:RATE,...conf});
 const buffer=new Float32Array(BLOCK),duration=[];
 for(let key=21;key<85;key++)engine.noteOn(key,{velocity:80,peakForce:30});
 for(let j=0;j<LOOPS+WARMUP;j++){
  const start=performance.now();engine.render(buffer);
  if(j>=WARMUP)duration.push(performance.now()-start);
 }
 duration.sort((a,b)=>a-b);
 const p95=duration[Math.floor(duration.length*.95)];
 rows.push({profile:conf.name,coordinates:engine.n,pressedKeys:64,
  mechanicalCorrelationToFiveBass:correlation(responses[1].signal,responses[i].signal),
  p95Ms:+p95.toFixed(5),budgetFraction:+(p95/(BLOCK/RATE*1000)).toFixed(4),
  energyError:responses[i].energyError,
  source:'normalized board velocity only, no pressure calibration'});
}
console.log(JSON.stringify({purpose:'structural tradeoff only, NOT sound quality or real-time certification',rows},null,2));
if(rows.some(r=>!Number.isFinite(r.p95Ms)||
                !Number.isFinite(r.mechanicalCorrelationToFiveBass.correlation)||
                Math.abs(r.energyError)>1e-7))process.exitCode=1;
