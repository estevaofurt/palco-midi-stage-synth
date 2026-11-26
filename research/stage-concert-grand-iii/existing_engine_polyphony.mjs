// G3.12o: existing B/C/D DSP feasibility. Expanded test objects only.
// Preserve quality settings; no modification of root engines or UI.
import {PhysicalPianoEngine as B} from '../../physical-piano-legacy.js';
import {PhysicalPianoEngine as C} from '../../physical-piano.js';
import {HybridPianoEngine as D} from '../../physical-piano-hybrid.js';
import {performance} from 'node:perf_hooks';
import {mkdirSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const rows=[],out=process.argv[2]??'/tmp/g3-engine-scale';
function probe(name,Engine,rate,quality,count){
  const e=new Engine(rate,quality),Voice=e.voices[0].constructor;
  const original=e.maxVoices;
  while(e.voices.length<count)e.voices.push(new Voice());
  if(e.blockVoices)e.blockVoices.length=Math.max(e.blockVoices.length,count);
  e.maxVoices=count;
  const L=new Float32Array(128),R=new Float32Array(128),S=new Float32Array(128);
  const strike=i=>e.noteOn({id:i,key:36+(i-1)%36,speed:.72,hardness:.5,character:'american',send:.1});
  for(let i=1;i<=count;i++)strike(i);
  assert.equal(e.voices.filter(v=>v.active).length,count);
  e.setSustain?.(1);
  const times=[];let peak=0,minActive=count,silentBlocks=0;
  for(let i=0;i<300;i++){
    // Maintain the full load. Refresh any voice naturally pruned.
    if(i%10===0)for(let j=1;j<=count;j++)if(!e.find(j))strike(j);
    const t=performance.now();e.render(L,R,S,128);const elapsed=(performance.now()-t)*1000;
    if(i>=100){
      times.push(elapsed);
      minActive=Math.min(minActive,e.voices.filter(v=>v.active).length);
      let p=0;for(const buf of [L,R,S])for(const x of buf){assert.ok(Number.isFinite(x));p=Math.max(p,Math.abs(x));}
      peak=Math.max(peak,p);if(p===0)silentBlocks++;
    }
  }
  times.sort((a,b)=>a-b);const budget=128e6/rate,p99=times[197]/budget,overruns=times.filter(t=>t>budget).length;
  assert.ok(peak>0);
  // Verify replacement and release are not silently lost at expanded pool size.
  strike(count+1);assert.ok(e.find(count+1));assert.equal(e.voices.filter(v=>v.active).length,count);
  e.setSustain?.(0);e.stopAll();
  for(let j=0;j<40;j++){e.render(L,R,S,128);assert.ok(L.every(Number.isFinite)&&R.every(Number.isFinite));}
  return {engine:name,rate,quality,voices:count,originalLimit:original,minActive,medianUsPerSample:times[100]/128,
    p99BudgetFraction:p99,overruns,rawPeak:peak,silentBlocks,activeAfterRelease:e.voices.filter(v=>v.active).length,
    headroomGate:minActive===count&&p99<=.70&&overruns===0&&silentBlocks===0};
}
for(const [name,Engine] of [['B',B],['C',C],['D',D]])for(const rate of [48000,96000])
  for(const quality of ['balanced','studio'])for(const count of [32,64,96,128,192,256]){
    const row=probe(name,Engine,rate,quality,count);rows.push(row);
    console.log('G3_EXISTING_ENGINE_SCALE '+JSON.stringify(row));
  }
const summary={gate:true,nodeOnly:true,experimentalPool:true,configurations:rows.length,headroomConfigurations:rows.filter(x=>x.headroomGate).length,
  appPolyphonyValidated:false,physicalG3Validated:false};
mkdirSync(out,{recursive:true});writeFileSync(out+'/existing_engine_scale.json',JSON.stringify({summary,cases:rows},null,2));
console.log('G3_EXISTING_ENGINE_SCALE_GATE '+JSON.stringify(summary));
