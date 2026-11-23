import test from 'node:test';
import assert from 'node:assert/strict';
import {compareOctaveHarmonicSupport as compare} from '../research/iowa-pitch-harmonic-comb.mjs';
import {midiHz} from '../research/iowa-f0-label-audit.mjs';

function simulated(key,{noFundamental=false,inharmonicity=.00008}={}){
 const rate=48000,out=new Float32Array(rate*1.4),f=midiHz(key);
 for(let i=0;i<out.length;i++){
  const t=i/rate;
  let x=0;
  for(let n=1;n<=7;n++){
   if(noFundamental&&n===1)continue;
   x+=Math.sin(2*Math.PI*f*n*Math.sqrt(1+inharmonicity*n*n)*t)*
     Math.exp(-t*(.2+.11*n))*[0,.4,.7,.36,.24,.19,.12,.08][n];
  }
  out[i]=x;
 }
 return out;
}
test('independent spectral comb supports known synthetic C2, C3 and C6 label',()=>{
 for(const key of [36,48,84]){
  const result=compare(simulated(key),{key});
  assert.equal(result.classification,'spectral-supports-label',JSON.stringify(result));
  assert.ok(result.scoreMargin>.55);
 }
});
test('independent harmonic pattern does not mistake strong overtone for octave',()=>{
 for(const key of [36,48,60]){
  const result=compare(simulated(key,{noFundamental:true}),{key});
  assert.equal(result.classification,'spectral-supports-label',
    'missing fundamental '+key+' '+JSON.stringify(result));
 }
});
test('actual octave displacement is flagged rather than silently retuned',()=>{
 const shifted=compare(simulated(48),{key:36});
 assert.equal(shifted.classification,'spectral-mismatch-candidate',JSON.stringify(shifted));
});
test('spectral silence and invalid PCM remain inconclusive or rejected',()=>{
 assert.equal(compare(new Float32Array(48000*1.5),{key:48}).classification,'spectral-inconclusive');
 assert.throws(()=>compare(new Float32Array(1000),{key:48}),/insufficient/);
 const bad=new Float32Array(48000*1.5);bad[6000]=NaN;
 assert.throws(()=>compare(bad,{key:48}),/invalid PCM/);
});
