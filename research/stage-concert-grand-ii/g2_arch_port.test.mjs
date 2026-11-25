import assert from 'node:assert/strict';
import {fitDelay,DispersiveDelay} from './g2_arch_dispersion.mjs';
import {CoupledCore} from './g2_arch_port.mjs';
import {coupledPair} from '../stage-concert-grand/exact-modal.mjs';
let count=0;
for(const sr of [48000,96000])for(const n of [368,184,46]){
 const d=fitDelay(sr,n*sr/48000,.000296440484);
 assert(Math.abs(d.errors[0])<1e-7);assert(Math.abs(d.a)<1);
 for(const sigma of [0,2]){
  const loop=new DispersiveDelay(d,sigma);loop.next(1);
  for(let i=0;i<sr/2;i++){const e=loop.norm(),x=loop.next();assert(Number.isFinite(x));assert(loop.norm()<=e+1e-12);}
  if(sigma===0)assert(Math.abs(loop.norm()-1)<1e-9);
 }
 console.log('G2_DISPERSION '+JSON.stringify(d));count++;
}
for(const sr of [44100,48000,96000]){
 const c=new CoupledCore(sr);let ref={xa:0,va:0,xb:0,vb:0};
 let max=0,negative=0,peak=0;
 for(let i=0;i<sr/2;i++){
  const F=i<64?Math.sin(Math.PI*i/64):i>=1234&&i<1298?.5*Math.sin(Math.PI*(i-1234)/64):0;
  const before=c.energy(),work0=c.work;
  c.step(F);ref=coupledPair(c.a.p,c.b.p,ref,{springNPerM:c.k,dampingNsM:c.c,forceA:F});
  max=Math.max(max,Math.abs(c.a.x-ref.xa),Math.abs(c.a.velocity()-ref.va),Math.abs(c.b.x-ref.xb),Math.abs(c.b.velocity()-ref.vb));
  negative=Math.min(negative,c.work-work0+before-c.energy());
  peak=Math.max(peak,Math.abs(c.observer.left));
 }
 assert(max<1e-9);assert(negative>=-1e-12);assert(c.loss>=0&&peak>0);assert(Math.abs(c.work-c.loss-c.energy())<1e-10);
 console.log('G2_PORT '+JSON.stringify({sr,maxStateError:max,minStepLoss:negative,workJ:c.work,lossJ:c.loss,remainingJ:c.energy(),observerPeak:peak}));count++;
}
globalThis.sampleRate=48000;globalThis.AudioWorkletProcessor=class{};let Processor;globalThis.registerProcessor=(name,C)=>{assert.equal(name,'g2-port-proof');Processor=C;};
await import('./g2_arch_worklet.mjs');
const w=new Processor(),offline=new CoupledCore(48000),input=Float32Array.from({length:513},(_,i)=>i<64?Math.sin(Math.PI*i/64):0),L=new Float32Array(513),R=new Float32Array(513),l=new Float32Array(513),r=new Float32Array(513);
offline.render(input,L,R);
for(const [a,b] of [[0,128],[128,255],[255,513]])assert(w.process([[input.subarray(a,b)]],[[l.subarray(a,b),r.subarray(a,b)]]));
assert.deepEqual(l,L);assert.deepEqual(r,R);
console.log('G2_ARCH_PORT_PASS',count+1);
