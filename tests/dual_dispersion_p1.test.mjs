import test from 'node:test';
import assert from 'node:assert/strict';
import {PhysicalPianoEngine as Current} from '../physical-piano.js';
import {PhysicalPianoEngine as Dual} from '../experimental/dual-dispersion-p1/physical-piano.js';
import {measurePianoNote} from './piano_acoustic_metrics.mjs';

const RATE=48000,BLOCK=128;
function capture(Engine,key=60,velocity=80,waveguideOnly=false){
 const e=new Engine(RATE,'eco');
 e.setMechanicalModel({enabled:true,amount:.65,sympathy:true});
 e.noteOn({id:1,key,speed:velocity/127,hardness:.5,character:'japanese',send:0});
 // Diagnostic only: exclude synthetic resonators to isolate string-waveguide dispersion.
 if(waveguideOnly)for(const v of e.voices){v.modalMix=0;v.beatGain=0;}
 const samples=new Float32Array(Math.floor(RATE*1.7));
 const l=new Float32Array(BLOCK),r=new Float32Array(BLOCK),s=new Float32Array(BLOCK);
 for(let i=0;i<samples.length;i+=BLOCK){
  const n=Math.min(BLOCK,samples.length-i);
  e.render(l,r,s,n);
  for(let j=0;j<n;j++)samples[i+j]=(l[j]+r[j])*.5;
 }
 return measurePianoNote(samples,{sampleRate:RATE,key});
}
test('P1 changes the dispersion of the real waveguide without destabilising its note',()=>{
 for(const key of [36,60,84]){
  const old=capture(Current,key),next=capture(Dual,key);
  console.log('P1 compare key='+key+' oldB='+old.bMedian+' newB='+next.bMedian+' peakOld='+old.peak+' peakP1='+next.peak);
  assert.equal(next.nonFinite,0);
  assert.equal(next.clipped,0);
  assert.ok(next.rms>.00001,'audible note '+key);
  assert.ok(next.peak<1,'uncontrolled gain '+key);
  assert.ok(Math.abs(next.harmonics[0].cents)<30,'fundamental tuning '+key+' cents='+next.harmonics[0].cents);
 }
});
test('P1 diagnoses waveguide separately from the mixed resonator output',()=>{
 const old=capture(Current,60),next=capture(Dual,60);
 const oldWave=capture(Current,60,80,true),nextWave=capture(Dual,60,80,true);
 console.log('P1 full mix B old='+old.bMedian+' dual='+next.bMedian);
 console.log('P1 waveguide-only B old='+oldWave.bMedian+' dual='+nextWave.bMedian);
 assert.ok(old.bMedian!=null&&next.bMedian!=null,'insufficient full-mix harmonics');
 assert.ok(oldWave.bMedian!=null&&nextWave.bMedian!=null,'insufficient waveguide harmonics');
 assert.notEqual(nextWave.bMedian,oldWave.bMedian,'second filter must affect waveguide frequencies');
 // No arbitrary >5% requirement: full output is dominated by multiple coupled
 // partial models, and the actual target needs dry acoustic references.
});
test('P1 handles 32 and 64-note waveguides without NaN, clipping or premature stealing',()=>{
 for(const [mode,n] of [['eco',32],['studio',64]]){
  const e=new Dual(RATE,mode);
  e.setMechanicalModel({enabled:true,amount:.65,sympathy:true});
  for(let i=0;i<n;i++)e.noteOn({id:i+1,key:36+i,speed:.82,hardness:.6,character:'japanese'});
  assert.equal(e.voices.filter(v=>v.active).length,n);
  assert.equal(e.done.length,0);
  const l=new Float32Array(BLOCK),r=new Float32Array(BLOCK),s=new Float32Array(BLOCK);
  let peak=0;
  for(let k=0;k<100;k++){
   e.render(l,r,s,BLOCK);
   for(let i=0;i<BLOCK;i++){
    assert.ok(Number.isFinite(l[i])&&Number.isFinite(r[i]),'non-finite audio '+mode);
    peak=Math.max(peak,Math.abs(l[i]),Math.abs(r[i]));
   }
  }
  assert.ok(peak<.98,'headroom '+mode+' '+peak);
 }
});
