import test from 'node:test';
import assert from 'node:assert/strict';
import {HybridPianoEngine} from '../physical-piano-hybrid.js';
import {hybridRadiationCorrectionDb,hybridRadiationGain,SPECTRAL_SOURCE_RUN} from '../piano-hybrid-calibration.js';
import {readFileSync} from 'node:fs';
const read=p=>readFileSync(new URL(p,import.meta.url),'utf8');

test('calibration comes from verified 15 Steinway B spectral observations, not external code',()=>{
 assert.equal(SPECTRAL_SOURCE_RUN,'45115699255');
 assert.match(read('../piano-hybrid-calibration.js'),/Steinway B\/Iowa AIFF/);
 assert.match(read('../piano-hybrid-calibration.js'),/NOT calibrated hammer velocity/);
 assert.doesNotMatch(read('../piano-hybrid-calibration.js'),/fetch\(|AudioContext|new WebSocket/);
 assert.match(read('../physical-piano-hybrid.js'),/hybridRadiationGain\(key,speed,n\)/);
});

test('radiated excitation corrects bass overtone deficit and upper-note brightness in opposite directions',()=>{
 const mf=80/127;
 assert.ok(hybridRadiationCorrectionDb(36,mf,6)>20,'bass C2 needs strong overtone excitation');
 assert.ok(hybridRadiationGain(36,mf,6)>6);
 assert.ok(hybridRadiationCorrectionDb(48,mf,7)>20,'bass C3 upper partial deficit');
 assert.ok(hybridRadiationCorrectionDb(84,mf,2)<-4,'C6 second partial overexcited');
 assert.ok(hybridRadiationGain(84,mf,2)<1);
 assert.equal(hybridRadiationCorrectionDb(36,mf,1),0,'fundamental is the normalization reference');
 assert.equal(hybridRadiationCorrectionDb(36,mf,14),0,'no fabricated 14th-harmonic measurement');
});

test('bass dynamics react to played MIDI speed, no discontinuity at register or velocity anchors',()=>{
 const slow=32/127,medium=80/127,loud=120/127;
 assert.ok(hybridRadiationGain(36,slow,6)<hybridRadiationGain(36,medium,6),
 'Iowa bass pp and mf differ in spectral partial gain');
 assert.ok(hybridRadiationGain(48,loud,7)>hybridRadiationGain(48,slow,7));
 for(const anchor of [36,48,60,72,84]){
   for(const n of [2,4,6,8,9]){
     const left=hybridRadiationCorrectionDb(anchor-.001,medium,n);
     const right=hybridRadiationCorrectionDb(anchor+.001,medium,n);
     assert.ok(Math.abs(left-right)<.1,'note interpolation must be continuous '+anchor+'/'+n);
   }
 }
 for(const v of [slow,medium,loud]){
   for(const n of [2,3,6,8]){
     const left=hybridRadiationCorrectionDb(48,v-1e-5,n);
     const right=hybridRadiationCorrectionDb(48,v+1e-5,n);
     assert.ok(Math.abs(left-right)<.1);
   }
 }
});

test('all MIDI keys and velocities produce finite bounded spectral gains',()=>{
 for(let key=21;key<=108;key++){
   for(const speed of [0,.15,.35,.65,1]){
     for(let n=1;n<=23;n++){
       const gain=hybridRadiationGain(key,speed,n);
       assert.ok(Number.isFinite(gain)&&gain>0&&gain<=1001,
         'invalid gain key '+key+' speed '+speed+' n '+n+' '+gain);
     }
   }
 }
});

test('real worklet core remains finite and safely limited under 32/48/64 dense note loads',()=>{
 const L=new Float32Array(128),R=new Float32Array(128),S=new Float32Array(128);
 for(const [quality,count] of [['eco',32],['balanced',48],['studio',64]]){
   const piano=new HybridPianoEngine(48000,quality);
   for(let i=0;i<count;i++)piano.noteOn({id:i+1,key:36+i,speed:1,hardness:.65,character:'american',send:.25});
   let peak=0,energy=0;
   for(let block=0;block<80;block++){
     piano.render(L,R,S,128);
     for(let i=0;i<128;i++){
       assert.ok(Number.isFinite(L[i])&&Number.isFinite(R[i])&&Number.isFinite(S[i]));
       peak=Math.max(peak,Math.abs(L[i]),Math.abs(R[i]));
       energy+=L[i]*L[i];
     }
   }
   assert.ok(peak<.961,'clipping '+quality+' '+peak);
   assert.ok(energy>1e-5,'silence '+quality);
   assert.equal(piano.voices.filter(x=>x.active).length,count);
   piano.stopAll();
 }
});

test('two successive notes at nearby pitches change radiated register weights gradually',()=>{
 const rate=48000;
 const make=key=>{
   const piano=new HybridPianoEngine(rate,'eco');
   piano.noteOn({id:1,key,speed:.64,character:'american'});
   const l=new Float32Array(128),r=new Float32Array(128);
   let max=0;
   for(let i=0;i<50;i++){
     piano.render(l,r,null,128);
     for(const x of l){assert.ok(Number.isFinite(x));max=Math.max(max,Math.abs(x));}
   }
   return max;
 };
 const a=make(59),b=make(60);
 assert.ok(a>.0002&&b>.0002);
 assert.ok(Math.max(a,b)/Math.min(a,b)<8,'adjacent key loudness jump');
});
