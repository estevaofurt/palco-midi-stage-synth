import test from 'node:test';
import assert from 'node:assert/strict';
import {PhysicalPianoEngine,midiHz} from '../physical-piano.js';

function capture(key,speed=.8,seconds=.35){
  const e=new PhysicalPianoEngine(48000,'eco'),l=new Float32Array(128),r=new Float32Array(128),s=new Float32Array(128),out=new Float32Array(Math.ceil(seconds*48000));
  e.noteOn({id:1,key,speed,hardness:.6,character:'japanese'});
  for(let pos=0;pos<out.length;pos+=128){const n=Math.min(128,out.length-pos);e.render(l,r,s,n);out.set(l.subarray(0,n),pos)}
  return {samples:out,voice:e.find(1)};
}
function energy(x,f,at=.04){
  const sr=48000,atSample=Math.floor(at*sr),N=8192;
  let c=0,s=0;
  for(let j=0;j<N;j++){
    const w=.5-.5*Math.cos(2*Math.PI*j/(N-1));const a=2*Math.PI*f*j/sr;
    c+=x[atSample+j]*w*Math.cos(a);s+=x[atSample+j]*w*Math.sin(a);
  }
  return Math.hypot(c,s);
}
test('Japanese Grand calibrates hammer-contact duration by piano register',()=>{
  const bass=capture(36),middle=capture(60),treble=capture(96);
  assert.ok(bass.voice.hammerContactMs>middle.voice.hammerContactMs);
  assert.ok(middle.voice.hammerContactMs>treble.voice.hammerContactMs);
  assert.ok(treble.voice.hammerContactMs>=.27);
});
test('CFX treble retains audible second harmonic without adding audio samples',()=>{
  for(const key of [84,96]){
    const pcm=capture(key).samples,f=midiHz(key);
    const fundamental=energy(pcm,f),second=energy(pcm,f*2);
    assert.ok(second/fundamental>.23,`C treble key ${key}: H2/H1 = ${second/fundamental}`);
  }
});
test('CFX bass remains fuller than a sawtooth-like synthesized spectrum',()=>{
  const pcm=capture(36).samples,f=midiHz(36);
  const fundamental=energy(pcm,f),third=energy(pcm,f*3);
  assert.ok(fundamental>third*1.4,`bass ${fundamental} ${third}`);
});
test('Japanese low and high keys remain finite and within digital headroom',()=>{
  for(const key of [21,36,60,84,96,108]){
    const pcm=capture(key,.96).samples;
    assert.ok(pcm.every(Number.isFinite));
    assert.ok(Math.max(...pcm.subarray(0,2048).map(Math.abs))<1);
  }
});
