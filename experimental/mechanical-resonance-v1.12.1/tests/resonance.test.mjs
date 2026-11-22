import test from 'node:test';
import assert from 'node:assert/strict';
import { PianoResonanceBody } from '../piano-resonance.js';

const SR=48000;
const N=128;
function run(eng, withNote=false, sustain=0, duration=1.2) {
  eng.setSustain(sustain);
  if(withNote)eng.noteOn(60,100);
  const l=new Float32Array(N),r=new Float32Array(N),wl=new Float32Array(N),wr=new Float32Array(N);
  let energy=0,last=0;
  const blocks=Math.ceil(duration*SR/N);
  for(let b=0;b<blocks;b++){
    for(let i=0;i<N;i++){
      const t=(b*N+i)/SR;
      const active=t<0.25;
      const v=active?0.2*Math.sin(2*Math.PI*261.63*t):0;
      l[i]=r[i]=v;
    }
    if(b===Math.ceil(.25*SR/N) && withNote)eng.noteOff(60);
    eng.process(l,r,wl,wr);
    for(let i=0;i<N;i++){
      assert.ok(Number.isFinite(wl[i])&&Number.isFinite(wr[i]));
      assert.ok(Math.abs(wl[i])<2&&Math.abs(wr[i])<2,'unbounded resonance');
      if(b*N+i>0.35*SR)energy+=wl[i]*wl[i]+wr[i]*wr[i];
    }
    last=wl[N-1];
  }
  return {energy,last};
}
test('88 piano key states and CC64 damper controls',()=>{
  let x=new PianoResonanceBody();
  assert.equal(x.keys.length,88);
  assert.equal(x.keyGate(39),0);
  x.noteOn(60,90);assert.equal(x.keyGate(39),1);
  x.noteOff(60);assert.equal(x.keyGate(39),0);
  x.setSustain(127);assert.equal(x.keyGate(39),1);
  x.setSustain(0);assert.equal(x.keyGate(39),0);
});
test('silent held key activates resonance without a note attack',()=>{
  const idle=new PianoResonanceBody({body:0,sympathetic:.4});
  const open=new PianoResonanceBody({body:0,sympathetic:.4});
  assert.ok(run(open,true,0).energy>run(idle,false,0).energy*4+1e-12);
});
test('sustain pedal releases otherwise damped strings',()=>{
  const closed=new PianoResonanceBody({body:0,sympathetic:.4});
  const pedal=new PianoResonanceBody({body:0,sympathetic:.4});
  assert.ok(run(pedal,false,127).energy>run(closed,false,0).energy+1e-14);
});
test('allKeysUp clears held states and sustain',()=>{
  const e=new PianoResonanceBody();e.noteOn(60);e.setSustain(127);e.allKeysUp();
  assert.equal(e.keys.reduce((a,b)=>a+b,0),0);assert.equal(e.pedal,0);
});
test('resonances remain finite with dense input (stability regression)',()=>{
  const e=new PianoResonanceBody();
  const l=new Float32Array(N),r=new Float32Array(N),wl=new Float32Array(N),wr=new Float32Array(N);
  e.setSustain(127);
  for(let b=0;b<1500;b++){
    for(let i=0;i<N;i++){l[i]=r[i]=0.22*(Math.sin((b*N+i)*.019)+Math.sin((b*N+i)*.043));}
    e.process(l,r,wl,wr);
    for(let i=0;i<N;i++)assert.ok(Math.abs(wl[i])<2&&Math.abs(wr[i])<2,'runaway');
  }
});
