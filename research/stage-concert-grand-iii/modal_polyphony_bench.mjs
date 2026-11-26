// Experimental benchmark of the EXISTING modal DSP in Node, not the browser audio graph.
// Expand the pool on the test instance only. No stable source modifications.
import {PianoEngine,MAX_VOICES} from '../../piano-worklet.js';
import {performance} from 'node:perf_hooks';
import {mkdirSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const out=process.argv[2]??'/tmp/g3-polyphony';
const rows=[];
function probe(rate,count,partials){
  const e=new PianoEngine(rate), Voice=e.voices[0].constructor;
  while(e.voices.length<count)e.voices.push(new Voice());
  e.maxPartials=partials;
  const L=new Float32Array(128),R=new Float32Array(128),S=new Float32Array(128);
  const strike=(i)=>e.noteOn({id:i+1,key:36+i%36,speed:.8,hardness:.6,send:.12});
  for(let i=0;i<count;i++)strike(i);
  assert.equal(e.voices.filter(v=>v.active).length,count);
  for(let i=0;i<100;i++)e.render(L,R,S,128);
  const times=[];let maxPeak=0,minActive=count;
  for(let i=0;i<200;i++){
    if(i%10===0)for(let j=0;j<count;j++)if(!e.find(j+1))strike(j);
    const t=performance.now();e.render(L,R,S,128);times.push((performance.now()-t)*1000);
    minActive=Math.min(minActive,e.voices.filter(v=>v.active).length);
    for(const buf of [L,R,S])for(const x of buf){assert.ok(Number.isFinite(x));maxPeak=Math.max(maxPeak,Math.abs(x));}
  }
  times.sort((a,b)=>a-b);const budget=128e6/rate;
  return {rate,voices:count,partials,minActive,medianUsPerSample:times[100]/128,
    p99BudgetFraction:times[197]/budget,overruns:times.filter(x=>x>budget).length,
    rawPeak:maxPeak,headroomGate:minActive===count&&times[197]<=.70*budget&&times.every(x=>x<=budget)};
}
for(const rate of [44100,48000,96000])for(const count of [32,64,88,96,128,192,256])for(const partials of [16,28]){
  const row=probe(rate,count,partials);rows.push(row);console.log('G3_MODAL_POLYPHONY_CASE '+JSON.stringify(row));
}
mkdirSync(out,{recursive:true});
const summary={gate:true,productionPool:MAX_VOICES,experimentalPool:true,nodeOnly:true,configurations:rows.length,
  headroomConfigurations:rows.filter(x=>x.headroomGate).length,appPolyphonyValidated:false};
writeFileSync(out+'/modal_polyphony.json',JSON.stringify({summary,cases:rows},null,2));
console.log('G3_MODAL_POLYPHONY_GATE '+JSON.stringify(summary));
