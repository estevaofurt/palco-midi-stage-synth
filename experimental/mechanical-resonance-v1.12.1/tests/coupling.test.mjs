import test from 'node:test';
import assert from 'node:assert/strict';
import {CoupledPianoBus} from '../coupled-piano-bus.js';
import {PianoResonanceBody} from '../piano-resonance.js';

class WaveguideProbe {
  constructor(){this.buffer=new Float64Array(183);this.index=0;this.bridgeL=this.bridgeR=this.dryL=this.dryR=0;this.injection=0;this.injectedCount=0;this.reset()}
  reset(){this.buffer.fill(0);this.buffer[7]=0.85;this.index=0;this.injection=0;this.injectedCount=0}
  sample(){
    const i=this.index,v=this.buffer[i];
    this.buffer[i]=0.9993*v+this.injection;
    this.index=(i+1)%this.buffer.length;
    this.dryL=this.dryR=this.bridgeL=this.bridgeR=v;
  }
  pushBridge(v){this.injection=Math.max(-.1,Math.min(.1,v));if(v!==0)this.injectedCount++}
}
const N=128;
function run(gain=0,seconds=2){
  const source=new WaveguideProbe(),body=new PianoResonanceBody({bridgeLoad:.3,sympathetic:.20,body:.20}),bus=new CoupledPianoBus(source,{body,feedbackGain:gain,wetMix:.15});
  const l=new Float32Array(N),r=new Float32Array(N);
  bus.noteOn(60,100);
  let energy=0, max=0;
  for(let b=0;b<Math.ceil(seconds*48000/N);b++){
    bus.render(l,r);
    for(let i=0;i<N;i++){assert.ok(Number.isFinite(l[i])&&Number.isFinite(r[i]));max=Math.max(max,Math.abs(l[i]),Math.abs(r[i]));energy+=l[i]*l[i]+r[i]*r[i];}
  }
  return {energy,max,source};
}
test('bridge reaction is zero before excitation, and finite after excitation',()=>{
  const res=new PianoResonanceBody({bridgeLoad:.4});
  assert.equal(res.reaction,0);let max=0;
  for(let i=0;i<20000;i++){res.step(i<3000?Math.sin(i*.08)*.3:0);max=Math.max(max,Math.abs(res.reaction));}
  assert.ok(max>0,'expected nonzero mechanical reaction');assert.ok(max<=.08,'bridge reaction cap');
});
test('same-sample core routes soundboard reaction BACK into the waveguide',()=>{
  const passive=run(0),coupled=run(.9);
  assert.equal(passive.source.injectedCount,0);
  assert.ok(coupled.source.injectedCount>0);
  assert.ok(Math.abs(passive.energy-coupled.energy)>1e-11,'dry string waveform should change under coupling');
});
test('wet mix and return path can be bypassed independently',()=>{
  const source=new WaveguideProbe(),body=new PianoResonanceBody(),bus=new CoupledPianoBus(source,{body,wetMix:0,feedbackGain:0});
  const l=new Float32Array(128),r=new Float32Array(128);bus.render(l,r);
  assert.equal(source.injectedCount,0);
  assert.ok(l.some(x=>x!==0));
});
test('damper lift through MIDI affects symmetric resonance',()=>{
  const make=cc=>{const x=new PianoResonanceBody({body:0,sympathetic:1});x.setSustain(cc);let energy=0;for(let i=0;i<48000;i++){x.step(i<9000?Math.sin(i*261.63*2*Math.PI/48000)*.3:0);if(i>12000)energy+=x.wetL*x.wetL;}return energy;};
  assert.ok(make(127)>make(0)*2+1e-16);
});
test('feedback stays bounded with 64 open sympathetic-string dampers (one source waveguide)',()=>{
  const source=new WaveguideProbe(),res=new PianoResonanceBody({bridgeLoad:.4}),bus=new CoupledPianoBus(source,{body:res,feedbackGain:1});
  for(let n=24;n<88;n++)bus.noteOn(n,127);
  bus.setSustain(127);const l=new Float32Array(128),r=new Float32Array(128);
  let max=0;
  for(let j=0;j<1100;j++){bus.render(l,r);for(let i=0;i<128;i++){max=Math.max(max,Math.abs(l[i]),Math.abs(r[i]));assert.ok(Number.isFinite(l[i]));}}
  assert.ok(max<4,`runaway: ${max}`);
});
test('wet body does not disappear in mono sum',()=>{
  const body=new PianoResonanceBody({body:1,sympathetic:.5});
  body.noteOn(60,95);body.setSustain(127);
  let stereo=0,mono=0;
  for(let i=0;i<48000;i++){
    body.step(i<12000?.2*Math.sin(i*261.63*2*Math.PI/48000):0);
    stereo+=(body.wetL*body.wetL+body.wetR*body.wetR)/2;
    mono+=((body.wetL+body.wetR)*.5)**2;
  }
  assert.ok(stereo>0);
  assert.ok(mono/stereo>.03,`mono collapse ratio: ${mono/stereo}`);
});
