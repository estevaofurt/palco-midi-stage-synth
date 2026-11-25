import assert from 'node:assert/strict';
import {design,ModalCore,ExactControl,DelayCore,render} from './g2_arch_core.mjs';
let cases=0;
for(const sr of [48000,96000])for(const N of [368,184,46])for(const sigma of [0,2,8]){
 const d=design(sr,N*sr/48000,{sigma}),a=new ModalCore(d),b=new ExactControl(d),c=new DelayCore(d);
 for(let i=0;i<sr/2;i++){
  if(i===0||i===7001){for(const v of [a,b,c])v.strike(i===0?1:.3);}
  const e=b.energy(),na=a.norm(),nc=c.norm(),x=a.next(),y=b.next(),z=c.next();
  assert(Math.abs(x-y)<1e-8);assert(Math.abs(x-z)<1e-8);
  assert(b.energy()<=e+1e-10*Math.max(1,e));
  assert(a.norm()<=na+1e-12);assert(c.norm()<=nc+1e-12);
 }cases++;
}
const d=design(48000,184,{B:.000296440484}),a=new ModalCore(d),b=new ExactControl(d);
assert.throws(()=>new DelayCore(d),/dispersion/);
a.strike(1);b.strike(1);
for(let i=0;i<48000;i++)assert(Math.abs(a.next()-b.next())<1e-8);
const one=new ModalCore(d),two=new ModalCore(d);one.strike(.2);two.strike(.2);
const full=new Float64Array(513),split=new Float64Array(513);render([one],full);
render([two],split.subarray(0,127));render([two],split.subarray(127,255));render([two],split.subarray(255));assert.deepEqual(full,split);
console.log('G2_ARCH_CORE_PASS',cases+2);
