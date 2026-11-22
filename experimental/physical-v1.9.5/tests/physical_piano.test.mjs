import test from 'node:test';
import assert from 'node:assert/strict';
import {PhysicalPianoEngine,PHYSICAL_PRESETS,midiHz} from '../physical-piano.js';
function render(e,seconds){const n=Math.floor(seconds*e.sr),L=new Float32Array(128),R=new Float32Array(128),S=new Float32Array(128),pcm=new Float32Array(n);let peak=0,energy=0;for(let pos=0;pos<n;pos+=128){const k=Math.min(128,n-pos);e.render(L,R,S,k);pcm.set(L.subarray(0,k),pos);for(let i=0;i<k;i++){const v=L[i];assert.ok(Number.isFinite(v),'finite sample');peak=Math.max(peak,Math.abs(v));energy+=v*v;}}return {pcm,peak,rms:Math.sqrt(energy/n)};}
test('waveguide plays a C4 and a low note with finite nonzero signal',()=>{for(const key of [21,48,60,88,108]){const e=new PhysicalPianoEngine(48000);e.noteOn({id:1,key,speed:.8});const a=render(e,.25);assert.ok(a.peak>.001, `${key}, peak ${a.peak}`);assert.ok(a.peak<1,`${key}, clipped ${a.peak}`)}});
test('attack velocity influences loudness',()=>{const quiet=new PhysicalPianoEngine(48000),loud=new PhysicalPianoEngine(48000);quiet.noteOn({id:1,key:60,speed:.2});loud.noteOn({id:1,key:60,speed:1});const x=render(quiet,.3),y=render(loud,.3);assert.ok(y.rms>2*x.rms,`${y.rms} / ${x.rms}`)});
test('profile limits simultaneous voices and interrupts oldest voices',()=>{const e=new PhysicalPianoEngine(48000,'eco');for(let i=0;i<37;i++)e.noteOn({id:i+1,key:48+i,speed:.7});assert.equal(e.voices.filter(v=>v.active).length,PHYSICAL_PRESETS.eco.voices);e.setQuality('balanced');assert.equal(e.maxVoices,48);e.setQuality('studio');assert.equal(e.maxVoices,64)});
test('release damps string and eventually ends voices',()=>{const e=new PhysicalPianoEngine(48000);e.noteOn({id:1,key:60,speed:.65});render(e,.1);e.noteOff(1,false,.12);render(e,6);assert.equal(e.find(1),null)});
test('parameters update while notes play, and panic does not leave stuck notes',()=>{const e=new PhysicalPianoEngine(48000);e.noteOn({id:1,key:60,speed:.8});const v=e.find(1);const before=v.loopTarget;e.updateVoice(1,{decayScale:.5,damping:.7,brightness:.1,send:.4});assert.notEqual(v.loopTarget,before);assert.equal(v.sendTarget,.4);e.stopAll();render(e,3);assert.equal(e.find(1),null)});
test('no uncontrolled feedback in sustained 8-note chord',()=>{const e=new PhysicalPianoEngine(48000,'eco');[48,52,55,60,64,67,72,76].forEach((key,i)=>e.noteOn({id:i+1,key,speed:.9}));const a=render(e,3);assert.ok(a.peak<2,`peak ${a.peak}`)});

test('minimum 32 notes and ideal 64 notes remain allocated without stealing',()=>{
  for(const [quality,n] of [['eco',32],['studio',64]]){
    const engine=new PhysicalPianoEngine(48000,quality);
    for(let i=0;i<n;i++)engine.noteOn({id:i+1,key:36+i,speed:.72});
    assert.equal(engine.voices.filter(v=>v.active).length,n);
    assert.equal(engine.done.length,0);
    const left=new Float32Array(128),right=new Float32Array(128),aux=new Float32Array(128);
    for(let i=0;i<100;i++)engine.render(left,right,aux,128);
    assert.ok(left.every(Number.isFinite));
    engine.stopAll();
  }
});
test('harder strike has greater high-frequency energy than soft strike',()=>{
  const soft=new PhysicalPianoEngine(48000,'eco'),hard=new PhysicalPianoEngine(48000,'eco');
  soft.noteOn({id:1,key:60,speed:.65,hardness:.1});hard.noteOn({id:1,key:60,speed:.65,hardness:.95});
  const x=render(soft,.24).pcm,y=render(hard,.24).pcm;
  const hf=a=>{let sum=0;for(let i=3;i<a.length;i++){const d=a[i]-2*a[i-1]+a[i-2];sum+=d*d;}return sum/a.length};
  assert.ok(hf(y)>hf(x),`hard attack should be brighter: ${hf(y)} / ${hf(x)}`);
});

test('headroom prevents clipping of 32 and 64 loud physical piano notes',()=>{
  for(const [quality,n] of [['eco',32],['studio',64]]){
    const e=new PhysicalPianoEngine(48000,quality);
    for(let i=0;i<n;i++)e.noteOn({id:i+1,key:36+i,speed:.85,hardness:.7});
    const L=new Float32Array(128),R=new Float32Array(128),S=new Float32Array(128);let peak=0;
    for(let i=0;i<375;i++){e.render(L,R,S,128);for(let j=0;j<128;j++)peak=Math.max(peak,Math.abs(L[j]),Math.abs(R[j]))}
    assert.ok(peak<.98,`clipping with ${n} notes: ${peak}`);
  }
});
