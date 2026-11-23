/**
 * Stage D CPU REVIEW — informative ONLY. Produces NO audio assets,
 * never modifies the synth, never certifies real-time browser/device latency.
 * Usage: node scripts/benchmark_piano_d_cpu.mjs
 */
import {performance} from 'node:perf_hooks';
import os from 'node:os';
import {HybridPianoEngine} from '../physical-piano-hybrid.js';

const SR=48000, BLOCK=128, BUDGET=BLOCK/SR*1000;
const ARRANGEMENTS=['bass-repeated','keyboard-spread'];
const QUALITIES=[['eco',32],['balanced',48],['studio',64]];
function quantile(sorted,q){return sorted[Math.min(sorted.length-1,Math.floor((sorted.length-1)*q))]}
function pitchFor(kind,i,total){
  if(kind==='bass-repeated')return 24+i%24; // C1..B2: demanding sustained bass repetitions.
  return 21+Math.round(i*87/(Math.max(1,total-1)));
}
function run(quality,voices,kind){
  const engine=new HybridPianoEngine(SR,quality),L=new Float32Array(BLOCK),
    R=new Float32Array(BLOCK),S=new Float32Array(BLOCK);
  // Warm up the JS runtime before measuring steady-state DSP; outside the loop.
  engine.noteOn({id:9999,key:60,speed:.5,character:'american'});
  for(let i=0;i<128;i++)engine.render(L,R,S,BLOCK);
  engine.stopAll();
  for(let i=0;i<300;i++)engine.render(L,R,S,BLOCK);
  // Fresh engine to ensure no previous voices consume CPU in the real test.
  const piano=new HybridPianoEngine(SR,quality);
  const init=performance.now();
  for(let i=0;i<voices;i++)piano.noteOn({id:i+1,key:pitchFor(kind,i,voices),
    speed:.85,hardness:.65,send:0,character:'american'});
  const initMs=performance.now()-init;
  const active=piano.voices.filter(v=>v.active);
  const resonators=active.reduce((sum,v)=>sum+v.count,0);
  const samples=360,times=new Float64Array(samples);
  let peak=0,checksum=0;
  for(let i=0;i<samples;i++){
    const t0=performance.now();
    piano.render(L,R,S,BLOCK);
    times[i]=performance.now()-t0;
    for(let j=0;j<BLOCK;j++){
      const x=L[j],y=R[j];
      if(!Number.isFinite(x)||!Number.isFinite(y))throw Error('Nonfinite PCM');
      peak=Math.max(peak,Math.abs(x),Math.abs(y));checksum+=x*x;
    }
  }
  times.sort();
  const avg=times.reduce((a,b)=>a+b,0)/times.length;
  return {
    profile:quality,arrangement:kind,requestedVoices:voices,
    activeVoices:active.length,resonators,
    theoreticalResonatorUpdatesPerSecond:resonators*SR,
    noteOnBatchMs:Number(initMs.toFixed(3)),
    avgBlockMs:Number(avg.toFixed(3)),p50BlockMs:Number(quantile(times,.5).toFixed(3)),
    p95BlockMs:Number(quantile(times,.95).toFixed(3)),
    p99BlockMs:Number(quantile(times,.99).toFixed(3)),
    worstBlockMs:Number(times[times.length-1].toFixed(3)),
    estimatedAvgRenderBudgetPercent:Number((avg/BUDGET*100).toFixed(1)),
    peak:Number(peak.toFixed(5)),rms:Number(Math.sqrt(checksum/(samples*BLOCK)).toFixed(5))
  };
}

const results=[];
for(const [quality,n] of QUALITIES)
  for(const kind of ARRANGEMENTS)
    results.push(run(quality,n,kind));
const report={schema:'stage-d-cpu-profiling-preparation-v1',sr:SR,framesPerBlock:BLOCK,
  theoreticalBlockTimeMs:BUDGET,environment:'Node process - NOT AudioWorklet/Chrome/Android',
  node:process.version,arch:process.arch,platform:process.platform,
  cpu:os.cpus()[0]?.model||'not available',
  disclaimer:'Timing from GitHub-hosted Linux is NOT a hard real-time deadline or commercial device certification. Different V8, processor speed, thermal throttle, audio graph and garbage collection matter.',
  data:results};
console.log(JSON.stringify(report,null,2));
