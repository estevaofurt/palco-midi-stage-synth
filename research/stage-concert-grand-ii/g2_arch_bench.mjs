import {performance} from 'node:perf_hooks';
import {mkdirSync,writeFileSync} from 'node:fs';
import {design,ModalCore,ExactControl,DelayCore,render} from './g2_arch_core.mjs';
const rows=[];
for(const sr of [48000,96000])for(const n of [1,8,32,64])for(const [name,C] of [['G1-local-exact',ExactControl],['modal',ModalCore],['delay-flexible',DelayCore]]){
 const voices=Array.from({length:n},(_,i)=>new C(design(sr,[368,184,46][i%3]*sr/48000,{sigma:2})));
 const out=new Float64Array(128),times=[];let peak=0;
 for(let k=0;k<600;k++){
  const t=performance.now();
  if(k%37===0)for(let i=0;i<n;i++)voices[i].strike(.01/n);
  render(voices,out);
  const elapsed=performance.now()-t;
  if(k>=100)times.push(elapsed);
  for(const x of out){if(!Number.isFinite(x))throw Error('nonfinite');peak=Math.max(peak,Math.abs(x));}
 }
 times.sort((a,b)=>a-b);const q=p=>times[Math.ceil(times.length*p)-1],deadline=128000/sr;
 rows.push({sr,voices:n,core:name,partials:8,blockFrames:128,p50Ms:q(.5),p95Ms:q(.95),p99Ms:q(.99),maxMs:times.at(-1),overDeadline:times.filter(x=>x>deadline).length,deadlineMs:deadline,peak});
}
const result={scope:'Node CI isolated 8-partial flexible displacement cores, includes repeated injections, no full G1, hammer, board, audio pressure or browser/hardware; no polyphony claim',node:process.version,rows};
mkdirSync('/tmp/g2arch',{recursive:true});writeFileSync('/tmp/g2arch/benchmark.json',JSON.stringify(result,null,2));
for(const r of rows)console.log('G2_ARCH_BENCH '+JSON.stringify(r));
