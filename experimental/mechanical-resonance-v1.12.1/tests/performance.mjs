import {performance} from 'node:perf_hooks';
import {PianoResonanceBody} from '../piano-resonance.js';
const fs=48000,N=128,seconds=12;
const e=new PianoResonanceBody({sampleRate:fs});
const inL=new Float32Array(N),inR=new Float32Array(N),outL=new Float32Array(N),outR=new Float32Array(N);
e.setSustain(127);
const ms=[];
let samples=0;
for(let b=0;b<seconds*fs/N;b++){
  for(let i=0;i<N;i++){
    const t=(samples+i)/fs;
    inL[i]=inR[i]=0.12*(Math.sin(2*Math.PI*130.81*t)+Math.sin(2*Math.PI*261.63*t)+Math.sin(2*Math.PI*523.25*t));
  }
  const start=performance.now();
  e.process(inL,inR,outL,outR);
  const end=performance.now();
  if(b>=100)ms.push(end-start);
  samples+=N;
}
ms.sort((a,b)=>a-b);
const percentile=p=>Number(ms[Math.min(ms.length-1,Math.round(p*(ms.length-1)))].toFixed(4));
console.log(JSON.stringify({sampleRate:fs,blockSamples:N,blockBudgetMs:+(N/fs*1000).toFixed(4),medianBlockMs:percentile(.50),p95BlockMs:percentile(.95),p99BlockMs:percentile(.99),simulatedSeconds:seconds,scope:'ONLY SHARED RESONANCE; EXCLUDES PIANO, FX, BROWSER, AND MOBILE CPU'},null,2));
