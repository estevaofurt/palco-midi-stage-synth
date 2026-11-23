import test from 'node:test';
import assert from 'node:assert/strict';
import {midiHz,rmsWindow,spectrum,findPartial,partialAmplitude,measurePianoNote} from './piano_acoustic_metrics.mjs';
const RATE=48000;
function synth({key=60,amp=.18,b=.0004,decay=.5,seconds=1.6}={}){
 const out=new Float32Array(Math.ceil(seconds*RATE)),f0=midiHz(key);
 for(let i=0;i<out.length;i++){
   const t=i/RATE;let s=0;
   for(let n=1;n<=5;n++){
     const f=n*f0*Math.sqrt((1+b*n*n)/(1+b));
     s+=amp/(n*n)*Math.exp(-t*decay*n)*Math.sin(2*Math.PI*f*t);
   }
   out[i]=s;
 }
 return out;
}
test('FFT finds A440 within one cent and amplitude is normalised',()=>{
 const x=new Float32Array(RATE*2);
 for(let i=0;i<x.length;i++)x[i]=.2*Math.sin(2*Math.PI*440*i/RATE);
 const p=findPartial(spectrum(x,RATE,.18),440);
 assert.ok(Math.abs(p.cents)<1,'cents='+p.cents);
 const amp=partialAmplitude(x,RATE,440,.2,.4);
 assert.ok(Math.abs(amp-.2)<.0005,'amplitude='+amp);
});
test('RMS, clipping and non-finite samples are identified',()=>{
 const x=synth();x[200]=1.3;x[201]=NaN;
 assert.equal(rmsWindow(x,RATE,0,.01),null);
 const m=measurePianoNote(x,{sampleRate:RATE});
 assert.equal(m.clipped,1);assert.equal(m.nonFinite,1);
 assert.ok(m.peak>1.29);
});
test('inharmonicity estimate distinguishes a stiff string from ideal harmonics',()=>{
 const stretched=measurePianoNote(synth({b:.0007}),{sampleRate:RATE,key:60});
 const ideal=measurePianoNote(synth({b:0}),{sampleRate:RATE,key:60});
 assert.ok(stretched.bSampleCount>=2);
 assert.ok(stretched.bMedian>.0001&&stretched.bMedian<.002,'B='+stretched.bMedian);
 assert.ok(stretched.bMedian>Math.max(0,ideal.bMedian||0)+.00005);
});
test('different decay constants change late envelope',()=>{
 const fast=measurePianoNote(synth({decay:3}),{sampleRate:RATE});
 const slow=measurePianoNote(synth({decay:.3}),{sampleRate:RATE});
 assert.ok(fast.lateDecayDb<slow.lateDecayDb);
 assert.ok(fast.harmonics.length>3);
 assert.ok(fast.harmonics.every(h=>Number.isFinite(h.relativeDb)));
});
test('short recordings are rejected',()=>{
 assert.throws(()=>measurePianoNote(new Float32Array(100)),RangeError);
});
