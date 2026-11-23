import test from 'node:test';
import assert from 'node:assert/strict';
import {auditPitchLabel,yinWindow,midiHz} from '../research/iowa-f0-label-audit.mjs';

function syntheticPiano(key,{sampleRate=48000,seconds=1.50,
  noFundamental=false,inharmonicity=.00007,detuneCents=0,noise=.00001
}={}){
 const a=new Float32Array(Math.round(sampleRate*seconds));
 const f0=midiHz(key)*2**(detuneCents/1200);
 let seed=1234567;
 for(let i=0;i<a.length;i++){
  const t=i/sampleRate;
  let y=0;
  for(let n=1;n<=5;n++){
   if(noFundamental&&n===1)continue;
   const fn=n*f0*Math.sqrt(1+inharmonicity*n*n);
   y+=Math.sin(2*Math.PI*fn*t+.07*n)*Math.exp(-t*(.12+.09*n))*
      ([0,.42,.61,.40,.25,.12][n]);
  }
  seed=(Math.imul(seed,1664525)+1013904223)>>>0;
  const r=seed/4294967296-.5;
  a[i]=y+noise*r;
 }
 return a;
}

test('labels C2–C6 are recognized from original-style musical signals',()=>{
 for(const key of [36,48,60,72,84]){
  const result=auditPitchLabel(syntheticPiano(key),{key});
  assert.equal(result.classification,'label-consistent',
    'key '+key+': '+JSON.stringify(result));
  assert.ok(result.reliable);
  assert.ok(Math.abs(result.centsFromLabel)<45);
  assert.ok(result.agreementCents<50);
 }
});

test('weak or absent fundamental does not promote loud second harmonic by an octave',()=>{
 for(const key of [36,48,60]){
  const result=auditPitchLabel(syntheticPiano(key,{noFundamental:true}),{key});
  assert.equal(result.classification,'label-consistent',
    'missing f0 key='+key+': '+JSON.stringify(result));
 }
});

test('off-by-octave label is flagged instead of calibrating the wrong key',()=>{
 const original=syntheticPiano(48);
 const result=auditPitchLabel(original,{key:36});
 assert.equal(result.classification,'label-mismatch-candidate',JSON.stringify(result));
 assert.ok(result.centsFromLabel>1000&&result.centsFromLabel<1400);
 assert.equal(result.nearestMidi,48);
});

test('incomplete and silent signals do not pass as verified reference notes',()=>{
 const pcm=new Float32Array(48000*1.5);
 const result=auditPitchLabel(pcm,{key:48});
 assert.equal(result.classification,'inconclusive');
 assert.equal(result.reliable,false);
 assert.throws(()=>auditPitchLabel(new Float32Array(1000),{key:48}),/1.1 seconds/);
 assert.throws(()=>auditPitchLabel(pcm,{key:20}),/MIDI key/);
 assert.throws(()=>yinWindow(pcm,48000,0),/invalid sample rate or expected pitch/);
});

test('note detuning stays visible in cents rather than silently overwriting source labels',()=>{
 const result=auditPitchLabel(syntheticPiano(48,{detuneCents:24}),{key:48});
 assert.equal(result.classification,'label-consistent',JSON.stringify(result));
 assert.ok(result.centsFromLabel>10&&result.centsFromLabel<45,JSON.stringify(result));
});

test('contradictory note windows are not classified as verified labels',()=>{
 const pcm=syntheticPiano(36);
 const second=syntheticPiano(48);
 pcm.set(second.subarray(Math.round(.57*48000)),Math.round(.57*48000));
 const result=auditPitchLabel(pcm,{key:36});
 assert.equal(result.classification,'inconclusive',JSON.stringify(result));
 assert.equal(result.reliable,false);
});
