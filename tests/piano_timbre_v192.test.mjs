import test from 'node:test';
import assert from 'node:assert/strict';
import {PhysicalPianoEngine,PHYSICAL_PRESETS,midiHz} from '../physical-piano.js';

function capture(key=60,speed=.8,seconds=1.35,quality='eco'){
  const e=new PhysicalPianoEngine(48000,quality),N=Math.floor(e.sr*seconds);
  const out=new Float32Array(N),l=new Float32Array(128),r=new Float32Array(128),s=new Float32Array(128);
  e.noteOn({id:1,key,speed,hardness:.6,character:'japanese'});
  for(let pos=0;pos<N;pos+=128){const n=Math.min(128,N-pos);e.render(l,r,s,n);out.set(l.subarray(0,n),pos);}
  return out;
}
function harmonicEnergy(pcm,sampleRate,t,f){
  const start=Math.floor(t*sampleRate),count=8192;
  const omega=2*Math.PI*f/sampleRate;
  let cosine=0,sine=0;
  for(let i=0;i<count;i++){
    const window=.5-.5*Math.cos(2*Math.PI*i/(count-1)),v=pcm[start+i]*window;
    cosine+=v*Math.cos(omega*i);sine+=v*Math.sin(omega*i);
  }
  return Math.hypot(cosine,sine);
}
test('C4 fundamental is stronger than the third harmonic after hammer excitation',()=>{
  const x=capture();const f=midiHz(60);
  const first=harmonicEnergy(x,48000,.08,f),third=harmonicEnergy(x,48000,.08,3*f);
  assert.ok(first>third*1.35,`${first} vs ${third}`);
});
test('high harmonics decay faster than fundamental rather than remaining organ-like',()=>{
  const x=capture(),f=midiHz(60);
  const ratio=t=>harmonicEnergy(x,48000,t,4*f)/harmonicEnergy(x,48000,t,f);
  const early=ratio(.07),late=ratio(.8);
  assert.ok(late<early*.70,`late ${late} not substantially weaker than early ${early}`);
});
test('physical timbre stays audible and below clipping at the extremes',()=>{
  for(const key of [21,36,60,84,108]){
    const x=capture(key);let peak=0,rms=0;
    for(const v of x){peak=Math.max(peak,Math.abs(v));rms+=v*v;}
    assert.ok(peak>.0005&&peak<1,`key ${key} peak ${peak}`);
    assert.ok(rms>0,`key ${key} is silent`);
  }
});
test('32/64 simultaneous physical notes retain headroom with the brighter attack',()=>{
  for(const [quality,n] of [['eco',32],['studio',64]]){
    const e=new PhysicalPianoEngine(48000,quality),l=new Float32Array(128),r=new Float32Array(128),s=new Float32Array(128);
    for(let k=0;k<n;k++)e.noteOn({id:k+1,key:36+(k%64),speed:.92,hardness:.95});
    assert.equal(e.voices.filter(x=>x.active).length,PHYSICAL_PRESETS[quality].voices);
    let peak=0;
    for(let b=0;b<300;b++){
      e.render(l,r,s);
      for(let i=0;i<128;i++)peak=Math.max(peak,Math.abs(l[i]),Math.abs(r[i]));
    }
    assert.ok(peak<.9,`${quality} ${n} keys, peak ${peak}`);
  }
});
