import {performance} from 'node:perf_hooks';
import {CoupledPianoBus} from '../coupled-piano-bus.js';
import {PianoResonanceBody} from '../piano-resonance.js';
import {MultiStringProbe} from './fixtures/surrogate-strings.mjs';

const FS=48000,N=128;
for(const voices of [32,64]){
  const source=new MultiStringProbe(voices,FS);
  const bus=new CoupledPianoBus(source,{body:new PianoResonanceBody({sampleRate:FS}),feedbackGain:.8});
  for(let i=0;i<voices;i++)bus.noteOn(24+i,96);
  const L=new Float32Array(N),R=new Float32Array(N),samples=[];
  for(let i=0;i<2200;i++){
    const start=performance.now();
    bus.render(L,R);
    if(i>=100)samples.push(performance.now()-start);
  }
  samples.sort((a,b)=>a-b);
  const pct=p=>+(samples[Math.min(samples.length-1,Math.floor(p*samples.length))]).toFixed(4);
  console.log(JSON.stringify({source:'simplified waveguide SURROGATES, not actual Stage voices',voices,median_ms:pct(.5),p95_ms:pct(.95),p99_ms:pct(.99),block_budget_ms:+(N*1000/FS).toFixed(4),scope:'Same-callback surrogate strings + body only; EXCLUDES full piano, UI, FX, browser and mobile'},null,2));
}
