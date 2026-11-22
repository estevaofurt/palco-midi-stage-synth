import test from 'node:test';
import assert from 'node:assert/strict';
import {PhysicalPianoEngine} from '../physical-piano.js';

function make(mode='eco',mechanical=true){
  const e=new PhysicalPianoEngine(48000,mode);
  e.setMechanicalModel({enabled:mechanical,amount:.7,sympathy:true});
  return e;
}
function render(e,seconds){
  const L=new Float32Array(128),R=new Float32Array(128),S=new Float32Array(128);
  let peak=0,energy=0,mono=0,stereo=0,tail=0;
  for(let b=0;b<Math.ceil(seconds*e.sr/128);b++){
    e.render(L,R,S,128);
    for(let i=0;i<128;i++){
      assert.ok(Number.isFinite(L[i])&&Number.isFinite(R[i]));
      peak=Math.max(peak,Math.abs(L[i]),Math.abs(R[i]));
      energy+=L[i]*L[i]+R[i]*R[i];
      mono+=((L[i]+R[i])*.5)**2;
      stereo+=(L[i]*L[i]+R[i]*R[i])*.5;
      if(b*128/e.sr>seconds*.6)tail+=L[i]*L[i]+R[i]*R[i];
    }
  }
  return {peak,energy,mono,stereo,tail};
}
test('mechanical bypass is bit-identical to original physical engine at startup',()=>{
  const a=make('eco',false),b=new PhysicalPianoEngine(48000,'eco');
  for(const e of [a,b])e.noteOn({id:1,key:60,speed:.72});
  const AL=new Float32Array(128),AR=new Float32Array(128),BL=new Float32Array(128),BR=new Float32Array(128);
  for(let j=0;j<70;j++){
    a.render(AL,AR);b.render(BL,BR);
    for(let i=0;i<128;i++)assert.equal(AL[i],BL[i]);
  }
});
test('on mode physically changes string feedback and adds non-reverb sympathetic/body sound',()=>{
  const off=make('eco',false),on=make('eco',true);
  for(const e of [off,on])e.noteOn({id:1,key:60,speed:.72});
  const a=render(off,1.3),b=render(on,1.3);
  assert.ok(b.energy>0 && a.energy>0);
  assert.ok(Math.abs(b.energy-a.energy)>1e-6,'mechanical system must change output');
  assert.ok(on.mechanicalBlend>.8);
  assert.ok(on.mechanics.wetL!==0);
  assert.ok(Math.abs(on.bridgeReaction)>0);
});
test('MIDI damper bookkeeping handles overlapping identical notes and pedal',()=>{
  const e=make('eco',true);
  e.noteOn({id:1,key:60,speed:.6});e.noteOn({id:2,key:60,speed:.6});
  assert.equal(e.damperCounts[39],2);assert.equal(e.mechanics.keys[39],1);
  e.noteOff(1);assert.equal(e.damperCounts[39],1);assert.equal(e.mechanics.keys[39],1);
  e.setSustain(127);e.noteOff(2);
  assert.equal(e.damperCounts[39],0);assert.equal(e.mechanics.keys[39],0);
  assert.equal(e.mechanics.keyGate(39),1);
  e.setSustain(0);assert.equal(e.mechanics.keyGate(39),0);
});
test('32 eco and 64 studio notes with mechanical model remain finite without clipping',()=>{
  for(const [quality,count] of [['eco',32],['studio',64]]){
    const e=make(quality,true);
    for(let i=0;i<count;i++)e.noteOn({id:i+1,key:36+i,speed:.75});
    assert.equal(e.voices.filter(v=>v.active).length,count);
    e.setSustain(127);
    const r=render(e,.85);
    assert.ok(r.peak<1,`${quality}: ${r.peak}`);
    e.setSustain(0);e.stopAll();render(e,.45);
    assert.equal(e.mechanics.pedal,0);
    assert.equal(e.damperCounts.reduce((a,b)=>a+b,0),0);
  }
});
test('mechanical model can be disabled and enabled smoothly during held chord',()=>{
  const e=make('eco',true);
  [48,52,55,60].forEach((key,i)=>e.noteOn({id:i+1,key,speed:.8}));
  render(e,.4);
  e.setMechanicalModel({enabled:false});render(e,.4);
  assert.ok(e.mechanicalBlend<.01);
  e.setMechanicalModel({enabled:true,amount:.4});render(e,.2);
  assert.ok(e.mechanicalBlend>.9);
});
