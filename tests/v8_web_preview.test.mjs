import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {C3XV8Engine,V8_QUALITY,midiHz,c3xV8Config} from '../piano-c3x-v8-web.js';
import {engines,loadState} from '../patches-v8-web.js';
const read=p=>readFileSync(new URL(p,import.meta.url),'utf8');
function render(engine,seconds=.16){
 const n=Math.ceil(engine.sr*seconds),L=new Float32Array(128),R=new Float32Array(128);
 let peak=0,energy=0;
 for(let i=0;i<n;i+=128){
  let count=Math.min(128,n-i);engine.render(L,R,count);
  for(let j=0;j<count;j++){
   assert.ok(Number.isFinite(L[j])&&Number.isFinite(R[j]));
   peak=Math.max(peak,Math.abs(L[j]),Math.abs(R[j]));
   energy+=L[j]*L[j]+R[j]*R[j];
  }
 }
 return {peak,rms:Math.sqrt(energy/(2*n))};
}
test('88 keys have stable precomputed physical coefficients',()=>{
 assert.equal(midiHz(69),440);
 for(let key=21;key<=108;key++){
  const c=c3xV8Config(key,48000,'studio');
  assert.equal(c.key,key);assert.ok(c.count>0&&c.partials>0&&c.B>0);
  assert.ok(c.cos.every(Number.isFinite));
  assert.ok(c.decay.every(x=>x>0&&x<1));
 }
 assert.throws(()=>c3xV8Config(20),RangeError);
 assert.throws(()=>c3xV8Config(109),RangeError);
});
test('all registers render non-silent finite dry PCM without clipping',()=>{
 for(const key of [21,28,40,48,60,72,84,96,108]){
  const e=new C3XV8Engine(48000,'eco');
  assert.equal(e.noteOn({id:1,key,speed:.82,hardness:.55}),true);
  const a=render(e,.14);
  assert.ok(a.rms>1e-8,'silent key '+key+': '+JSON.stringify(a));
  assert.ok(a.peak<1,'clipped key '+key);
 }
});
test('hammer velocity controls energy; sustain delays damping',()=>{
 const s=new C3XV8Engine(48000),h=new C3XV8Engine(48000);
 s.noteOn({id:1,key:60,speed:.19,hardness:.45});
 h.noteOn({id:1,key:60,speed:.92,hardness:.45});
 const a=render(s,.19),b=render(h,.19);
 assert.ok(b.rms>a.rms*2,JSON.stringify({a,b}));
 h.setSustain(127);h.noteOff(1,false,.25);
 assert.equal(h.find(1).damped,false);
 h.setSustain(0);assert.equal(h.find(1).damped,true);
});
test('profiles enforce max 32/48/64 without infinite PCM',()=>{
 for(const [q,{voices}] of Object.entries(V8_QUALITY)){
  const e=new C3XV8Engine(48000,q);
  for(let i=0;i<voices;i++)e.noteOn({id:i+1,key:21+i,speed:.65});
  e.noteOn({id:900,key:72,speed:.5});
  assert.equal(e.voices.length,voices);
  assert.ok(render(e,.01).peak<1);
  e.stopAll();assert.equal(e.voices.length,0);
 }
});
test('preview includes ONLY one C3X piano engine, not A/B/C/D/E or samples',()=>{
 const controls=engines.piano.groups.flatMap(g=>g.controls);
 assert.equal(engines.piano.presets.length,1);
 assert.equal(engines.piano.presets[0].id,'c3x');
 assert.equal(controls.some(x=>x.id==='soundEngine'||x.type==='samplepack'),false);
 assert.equal(loadState(null).patches.piano.preset,'c3x');
 assert.deepEqual(Object.keys(engines),['piano','electric','organ','synth','sf']);
 const html=read('../v8-preview.html');
 const map=JSON.parse(html.match(/<script type="importmap">(.*?)<\/script>/s)[1]).imports;
 assert.equal(map['./acoustic.js'],'./acoustic-v8-web.js?build=1.13.0');
 assert.equal(map['./patches.js'],'./patches-v8-web.js?build=1.13.0');
 assert.match(html,/app-v8-web\.js\?build=1\.13\.0/);
 assert.doesNotMatch(html,/physical-piano-hybrid|physical-piano-legacy|piano-worklet|sample-notice/);
 const app=read('../app-v8-web.js'),a=read('../acoustic-v8-web.js');
 assert.match(app,/prepareV8/);
 assert.doesNotMatch(app,/prepareHybrid|preparePhysical|prepareModal|sampleBankCount|loadSamples/);
 assert.match(a,/stage-c3x-v8-web/);
 assert.doesNotMatch(a,/SampleLibrary|PianoBank|playHybrid/);
});
test('provenance of the original Python V8 is not misstated',()=>{
 assert.match(read('../v8-preview.html'),/não é a transposição validada do V8 Python original/i);
 assert.match(read('../piano-c3x-v8-web.js'),/NOT THE PYTHON V8 REFERENCE/);
});
