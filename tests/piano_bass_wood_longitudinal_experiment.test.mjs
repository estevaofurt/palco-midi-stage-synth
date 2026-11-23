import test from 'node:test';
import assert from 'node:assert/strict';
import {HybridPianoEngine as Candidate} from '../physical-piano-hybrid.js';
import {HybridPianoEngine as V127} from '../physical-piano-hybrid-v127.js';
import {PianoBassWoodRadiator,PianoBassLongitudinal,BOARD_BANDS} from '../piano-bass-wood.js';

const SR=48000,BLOCK=128;
function pcm(Engine,key,quality='eco',study='off',seconds=.23,velocity=.8){
 const e=Engine===Candidate?new Engine(SR,quality,study):new Engine(SR,quality);
 e.noteOn({id:1,key,speed:velocity,hardness:.55,character:'american',send:0});
 const out=new Float32Array(Math.ceil(seconds*SR)*2);
 const L=new Float32Array(BLOCK),R=new Float32Array(BLOCK);
 for(let i=0;i<out.length/2;i+=BLOCK){
   const n=Math.min(BLOCK,out.length/2-i);
   e.render(L,R,null,n);
   for(let j=0;j<n;j++){
     out[2*(i+j)]=L[j];out[2*(i+j)+1]=R[j];
   }
 }
 return out;
}
const norm=a=>Math.sqrt(a.reduce((s,x)=>s+x*x,0)/a.length);
function difference(a,b){
 assert.equal(a.length,b.length);let d=0;
 for(let i=0;i<a.length;i++){const e=a[i]-b[i];d+=e*e;}
 return Math.sqrt(d/a.length);
}
test('default bass physics study is OFF: legacy v1.12.7 PCM preserved exactly across all ranges',()=>{
 for(const q of ['eco','balanced','studio'])
 for(const key of [24,36,48,49,60,72,84])
 for(const velocity of [.25,.63,.94]){
   const old=pcm(V127,key,q,'off',.06,velocity);
   const now=pcm(Candidate,key,q,'off',.06,velocity);
   assert.deepEqual(now,old,'default PCM changed '+q+' '+key+' '+velocity);
 }
});
test('wood and longitudinal experiments never alter C4–C6 individual notes',()=>{
 for(const study of ['wood','longitudinal','combined'])
 for(const key of [49,60,72,84,108]){
   const base=pcm(V127,key,'eco','off',.13);
   assert.deepEqual(pcm(Candidate,key,'eco',study,.13),base,
     'isolated medium high changed: '+study+'/'+key);
 }
});
test('wood and longitudinal bass experiments are actually independently audible',()=>{
 for(const key of [24,36,48]){
   const baseline=pcm(V127,key,'studio','off',.35);
   const baseRms=norm(baseline);
   for(const study of ['wood','longitudinal','combined']){
     const edited=pcm(Candidate,key,'studio',study,.35);
     const diff=difference(baseline,edited);
     const rel=diff/baseRms;
     assert.ok(rel>1e-6,'inaudible study '+study+'/'+key+'/'+rel);
     assert.ok(rel<1.5,'unbounded study '+study+'/'+key+'/'+rel);
     assert.ok(edited.every(Number.isFinite),'nonfinite '+study+'/'+key);
   }
 }
});
test('soundboard is shared, lossy and bounded after being excited',()=>{
 const wood=new PianoBassWoodRadiator(SR);
 assert.equal(BOARD_BANDS.length,12);
 wood.noteOn(36,.9);
 let peak=0;
 for(let i=0;i<2*SR;i++){
   wood.step(i<SR*.1?.09*Math.sin(2*Math.PI*140*i/SR):0,0);
   assert.ok(Number.isFinite(wood.outputL)&&Number.isFinite(wood.outputR));
   peak=Math.max(peak,Math.abs(wood.outputL),Math.abs(wood.outputR));
 }
 assert.ok(peak>1e-8);
 const tail=Math.max(Math.abs(wood.outputL),Math.abs(wood.outputR));
 assert.ok(tail<peak*.01,'wood must not ring forever');
});
test('longitudinal quadratic modes stay finite and decay without excitation',()=>{
 const l=new PianoBassLongitudinal(SR);l.reset(36,.85);
 let max=0;
 for(let i=0;i<2*SR;i++){
   const source=i<.12*SR?.06*Math.sin(2*Math.PI*65.4*i/SR):0;
   const v=l.step(source,i<100?.0005:0);
   assert.ok(Number.isFinite(v));
   max=Math.max(max,Math.abs(v));
 }
 assert.ok(max>1e-11);
 assert.ok(Math.abs(l.y1[0])+Math.abs(l.y1[1])<max*.1,'no runaway energy');
});
test('64 bass voices and sustain remain finite under combined model',()=>{
 const e=new Candidate(SR,'studio','combined');
 for(let i=0;i<64;i++)e.noteOn({id:i+1,key:21+i%28,speed:.84,send:.2,character:'american'});
 assert.equal(e.voices.filter(x=>x.active).length,64);
 e.setSustain(127);
 const L=new Float32Array(BLOCK),R=new Float32Array(BLOCK),S=new Float32Array(BLOCK);
 let peak=0;
 for(let b=0;b<128;b++){
   e.render(L,R,S,BLOCK);
   for(let i=0;i<BLOCK;i++){
     assert.ok(Number.isFinite(L[i])&&Number.isFinite(R[i])&&Number.isFinite(S[i]));
     peak=Math.max(peak,Math.abs(L[i]),Math.abs(R[i]));
   }
 }
 assert.ok(peak>1e-5&&peak<.97,'unexpected peak '+peak);
 for(let i=0;i<64;i++)e.noteOff(i+1,false,.2);
 e.setSustain(0);
 e.stopAll();
});
