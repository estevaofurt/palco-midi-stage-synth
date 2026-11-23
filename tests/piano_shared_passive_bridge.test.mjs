import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {SharedPassivePianoBridge} from '../research/shared-passive-piano-bridge.mjs';

const almost=(x,y,rtol=5e-7,atol=5e-13)=>
 Math.abs(x-y)<=atol+rtol*Math.max(Math.abs(x),Math.abs(y));

test('string modes share TWO board modes rather than one radiator per note',()=>{
 for(const keys of [[36],[24,36,48],Array.from({length:64},(_,i)=>21+i)]){
   const p=new SharedPassivePianoBridge({keys});
   assert.equal(p.n,keys.length*2);
   assert.equal(p.bx.length,2);
   assert.equal(p.bv.length,2);
   assert.equal(p.coupling.length,keys.length*2);
   assert.ok(p.determinant>0);
 }
});

test('forced shared bridge satisfies E=E0+hammerWork-dissipated at 44.1/48/96 kHz',()=>{
 for(const sampleRate of [44100,48000,96000])
 for(const coupling of [0,.12,.8]){
   const p=new SharedPassivePianoBridge({sampleRate,keys:[24,36,43,48],coupling});
   const initial=p.energy();
   for(let i=0;i<Math.round(sampleRate*.075);i++){
     const t=i/sampleRate;
     p.forces[2]=t<.007?12*Math.sin(Math.PI*t/.007)**2:0;
     p.forces[3]=t<.005?5*Math.sin(Math.PI*t/.005)**2:0;
     p.step();
     const balance=initial+p.externalWork-p.dissipated;
     assert.ok(almost(p.energy(),balance),
       'shared energy mismatch sr='+sampleRate+' c='+coupling+' t='+t+
       ' E='+p.energy()+' balance='+balance);
   }
 }
});

test('shared spring coupling creates sympathetic motion and no response when decoupled',()=>{
 const a=new SharedPassivePianoBridge({keys:[36,43],coupling:0});
 const b=new SharedPassivePianoBridge({keys:[36,43],coupling:.9});
 a.setInitialStringDisplacement(0,.00015);
 b.setInitialStringDisplacement(0,.00015);
 let transmitted=0,decoupled=0,sympathetic=0;
 for(let i=0;i<48000;i++){
   decoupled+=a.step()**2;
   transmitted+=b.step()**2;
   sympathetic+=b.v[2]*b.v[2];
 }
 assert.equal(decoupled,0);
 assert.ok(transmitted>1e-10,'bridge must move');
 assert.ok(sympathetic>1e-14,'another string should receive energy through board');
});

test('energy always decreases without input across entire C1-C6 range',()=>{
 for(const keys of [[24,36,48],Array.from({length:56},(_,i)=>21+i)]){
   const p=new SharedPassivePianoBridge({keys,coupling:.5});
   for(let i=0;i<p.n;i+=5)p.setInitialStringDisplacement(i,1e-6);
   let previous=p.energy();
   for(let t=0;t<12000;t++){
     p.step();
     const next=p.energy();
     assert.ok(Number.isFinite(next)&&next>=0);
     assert.ok(next<=previous+1e-9,
       'energy increased for '+keys.length+' notes at '+t);
     previous=next;
   }
 }
});

test('silence, reset and valid parameter boundaries',()=>{
 const p=new SharedPassivePianoBridge({keys:[36]});
 for(let i=0;i<1000;i++){
  assert.equal(p.step(),0);
  assert.equal(p.energy(),0);
 }
 p.forces[0]=10;p.step();
 assert.ok(p.energy()>0);
 p.reset();
 assert.equal(p.energy(),0);
 assert.equal(p.externalWork,0);
 assert.equal(p.dissipated,0);
 assert.ok(p.forces.every(x=>x===0));
 assert.throws(()=>new SharedPassivePianoBridge({keys:[]}),/valid MIDI/);
 assert.throws(()=>new SharedPassivePianoBridge({keys:[500]}),/valid MIDI/);
 assert.throws(()=>new SharedPassivePianoBridge({coupling:3}),/coupling/);
});

test('research network does not import external PCM or touch published synth',()=>{
 const src=readFileSync(new URL('../research/shared-passive-piano-bridge.mjs',import.meta.url),'utf8');
 assert.match(src,/not radiated sound pressure/i);
 assert.match(src,/O\(N\)/);
 assert.doesNotMatch(src,/from ['"]\.\.\/physical-piano-hybrid|readFileSync|fetch\(|AudioWorkletProcessor|Buffer\.alloc|new AudioBuffer/);
});
