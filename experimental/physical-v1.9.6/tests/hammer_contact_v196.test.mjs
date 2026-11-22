import test from 'node:test';
import assert from 'node:assert/strict';
import {HammerContactBank,simulateHammerContact} from '../hammer-contact.js';
import {PhysicalPianoEngine,PHYSICAL_PRESETS} from '../physical-piano.js';

function render(engine,s=.2){
  const n=Math.round(s*engine.sr),pcm=new Float32Array(n);
  const l=new Float32Array(128),r=new Float32Array(128),aux=new Float32Array(128);
  let peak=0;
  for(let i=0;i<n;i+=128){const m=Math.min(128,n-i);engine.render(l,r,aux,m);pcm.set(l.subarray(0,m),i);
    for(let j=0;j<m;j++){assert.ok(Number.isFinite(l[j]));peak=Math.max(peak,Math.abs(l[j]),Math.abs(r[j]));}}
  return {pcm,peak};
}

test('nonlinear hammer rebound: low strings contact longer than treble',()=>{
  const bass=simulateHammerContact(48000,36,.75,.55);
  const mid=simulateHammerContact(48000,60,.75,.55);
  const high=simulateHammerContact(48000,96,.75,.55);
  assert.ok(bass.durationMs>mid.durationMs&&mid.durationMs>high.durationMs,`${bass.durationMs}, ${mid.durationMs}, ${high.durationMs}`);
  for(const x of [bass,mid,high]){
    assert.ok(x.peakForce>0&&x.peakForce<1000);
    assert.ok(x.durationMs>.3&&x.durationMs<9);
    assert.ok(x.wave.slice(0,x.count).every(y=>Number.isFinite(y)&&y>=0));
    const total=x.wave.slice(0,x.count).reduce((a,b)=>a+b,0);
    assert.ok(Math.abs(total-1)<.001);
  }
});

test('increasing hammer velocity changes strike duration and force',()=>{
  const soft=simulateHammerContact(48000,60,.2,.55);
  const hard=simulateHammerContact(48000,60,.9,.55);
  assert.ok(hard.peakForce>soft.peakForce*2);
  assert.ok(hard.durationMs<soft.durationMs);
});

test('physical attack bank is a bounded set of mathematical waveforms, not samples',()=>{
  const bank=new HammerContactBank(48000);
  assert.equal(bank.grid.size,4);
  const a=bank.select(60,.7,.5,'japanese');
  assert.ok(a.first.count>10&&a.first.wave instanceof Float32Array);
  const b=bank.select(66,.7,.5,'japanese');
  assert.ok(b.blend>0&&b.blend<1);
  assert.notEqual(bank.select(60,.7,.5,'japanese').first,bank.select(60,.7,.5,'felt').first);
});

test('physical force pulse is actually injected into each new voice',()=>{
  const engine=new PhysicalPianoEngine(48000,'eco');
  engine.noteOn({id:7,key:60,speed:.85,hardness:.65});
  const voice=engine.find(7);
  assert.ok(voice.hammerWaveA&&voice.hammerWaveB&&voice.hammerLength>25);
  assert.equal(voice.hammerIndex,voice.hammerLength); // force was folded before rendering
  const audio=render(engine,.16);
  assert.ok(audio.peak>.002&&audio.peak<.98,`peak ${audio.peak}`);
  assert.equal(voice.hammerIndex,voice.hammerLength);
});

test('new hammer leaves 32- and 64-note polyphony uncut and avoids clipping',()=>{
  for(const [mode,count] of [['eco',32],['studio',64]]){
    const engine=new PhysicalPianoEngine(48000,mode);
    for(let i=0;i<count;i++)engine.noteOn({id:i+1,key:28+i,speed:.76,hardness:.6,character:'japanese'});
    assert.equal(engine.voices.filter(v=>v.active).length,PHYSICAL_PRESETS[mode].voices);
    const {peak}=render(engine,.18);
    assert.ok(peak<.98,`${mode} peak ${peak}`);
  }
});
