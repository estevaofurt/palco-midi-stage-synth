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
test('preview has independent V8 Web and E local WAV, no A/B/C/D motors',()=>{
 const controls=engines.piano.groups.flatMap(g=>g.controls);
 assert.deepEqual(engines.piano.presets.map(x=>x.id),['c3x','c3x-soft','c3x-bright']);
 assert.equal(engines.piano.presets[0].id,'c3x');
 const selector=controls.find(x=>x.id==='soundEngine');
 assert.deepEqual(Object.keys(selector.options),['v8','sampled']);
 assert.equal(controls.filter(x=>x.type==='samplepack').length,1);
 assert.deepEqual(Object.keys(controls.find(x=>x.id==='sampleModel').options),['american','japanese','felt','upright']);
 assert.equal(loadState(null).patches.piano.preset,'c3x');
 assert.equal(loadState(null).patches.piano.values.soundEngine,'v8');
 assert.deepEqual(Object.keys(engines),['piano','electric','organ','synth','sf']);
 const html=read('../v8-preview.html');
 const map=JSON.parse(html.match(/<script type="importmap">(.*?)<\/script>/s)[1]).imports;
 assert.equal(map['./acoustic.js'],'./acoustic-v8-web.js?build=1.13.1');
 assert.equal(map['./patches.js'],'./patches-v8-web.js?build=1.13.1');
 assert.match(html,/app-v8-web\.js\?build=1\.13\.1/);
 assert.doesNotMatch(html,/physical-piano-hybrid|physical-piano-legacy|piano-worklet/);
 assert.match(html,/id="sample-notice"/);
 assert.match(html,/id="sample-upload-shortcut"/);
 const app=read('../app-v8-web.js'),a=read('../acoustic-v8-web.js');
 assert.match(app,/prepareV8/);
 assert.doesNotMatch(app,/prepareHybrid|preparePhysical|prepareModal|sampleBankCount/);
 assert.match(app,/loadSamples/);
 assert.match(app,/syncSampleUI/);
 assert.match(app,/warnSample\(key,velocity\)/);
 assert.match(a,/stage-c3x-v8-web/);
 assert.match(a,/SampleLibrary/);
 assert.match(a,/p\.soundEngine==='sampled'/);
 assert.doesNotMatch(a,/PianoBank|playHybrid/);
});
test('provenance of the original Python V8 is not misstated',()=>{
 assert.match(read('../v8-preview.html'),/ainda não equivale ao V8 Python original/i);
 assert.match(read('../piano-c3x-v8-web.js'),/NOT THE PYTHON V8 REFERENCE/);
});


test('sample E plays its WAV bank without initializing the V8 AudioWorklet',async()=>{
 const {Acoustic}=await import('../acoustic-v8-web.js');
 let played=0,rate=0;
 const makeGain=()=>({gain:{value:1,setTargetAtTime(){}},connect(dest){return dest},disconnect(){}});
 const ctx={
  currentTime:0,sampleRate:48000,
  createGain:makeGain,
  createBiquadFilter:()=>({type:'lowpass',frequency:{value:1,setTargetAtTime(){}},Q:{value:1},gain:{value:0},connect(dest){return dest}}),
  decodeAudioData:async()=>({duration:2,sampleRate:48000}),
  createBufferSource:()=>({buffer:null,playbackRate:{set value(v){rate=v}},connect(dest){return dest}})
 };
 const acoustic=new Acoustic(ctx,makeGain());
 const fake=name=>({name,size:100,arrayBuffer:async()=>new ArrayBuffer(100)});
 await acoustic.samples.load('japanese',[fake('MIDI60_v60.wav'),fake('MIDI72_v110.wav')]);
 const part={
  gate:makeGain(),
  releaseSeconds:0,
  own(){},
  start(){played++}
 };
 acoustic.play(part,61,55,{soundEngine:'sampled',sampleModel:'japanese',release:.43,damping:30,touch:50});
 assert.equal(played,1);assert.ok(rate>1);
 assert.equal(acoustic.node,null,'sampler must never initialize the V8 worklet');
 assert.equal(acoustic.samples.count('american'),0,'separate sample bank per piano');
 acoustic.play(part,61,55,{soundEngine:'sampled',sampleModel:'american',release:.43,damping:30,touch:50});
 assert.equal(played,1,'missing WAV must never fall back to synthetic V8 sound');
});
test('E WAV import and selector are reachable and the virtual keyboard stays responsive',()=>{
 const panel=read('../panel.js'),app=read('../app-v8-web.js'),html=read('../v8-preview.html');
 assert.match(panel,/name==='sampleModel'/);
 assert.match(panel,/patch\.values\.sampleModel/);
 assert.match(app,/sampleCount\(\)/);
 assert.match(app,/async function loadSamples/);
 assert.match(app,/panel\.updateSamples\(id,model,count\)/);
 assert.match(app,/activePointers\.set\(pointer,slot\);paintKeys\(\)/);
 assert.match(app,/for\(const slot of activePointers\.values\(\)\)held\.add\(slot\.key\)/);
 assert.match(html,/Carregar notas WAV/);
});
