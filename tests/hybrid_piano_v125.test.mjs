import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {HybridPianoEngine,HYBRID_QUALITY,hybridInharmonicity,hybridContactTime} from '../physical-piano-hybrid.js';
import {engines,loadState} from '../patches.js';
import {PhysicalPianoEngine as OldB} from '../physical-piano-legacy.js';
import {PhysicalPianoEngine as OldC} from '../physical-piano.js';
import {PianoEngine as ClaudeA} from '../piano-worklet.js';

const read=path=>readFileSync(new URL(path,import.meta.url),'utf8');
function render(engine,seconds){
  const n=Math.round(engine.sr*seconds);
  const L=new Float32Array(128),R=new Float32Array(128),S=new Float32Array(128);
  let peak=0,sum=0,hf=0,prior1=0,prior2=0,stereoDelta=0;
  for(let i=0;i<n;i+=128){
    const count=Math.min(128,n-i);
    engine.render(L,R,S,count);
    for(let j=0;j<count;j++){
      const x=L[j],y=R[j],h=x-2*prior1+prior2;
      assert.ok(Number.isFinite(x)&&Number.isFinite(y)&&Number.isFinite(S[j]),'hybrid PCM finite');
      peak=Math.max(peak,Math.abs(x),Math.abs(y));
      sum+=x*x;hf+=h*h;stereoDelta+=Math.abs(x-y);
      prior2=prior1;prior1=x;
    }
  }
  return {peak,rms:Math.sqrt(sum/n),hf:hf/n,stereoDelta};
}

test('D é seleção ADICIONAL dentro do piano, sem alterar A/B/C ou preset salvo',()=>{
  const c=engines.piano.groups.flatMap(g=>g.controls).find(x=>x.id==='soundEngine');
  assert.deepEqual(Object.keys(c.options),['modal','physicalLegacy','physical','hybrid','classic']);
  assert.match(c.options.hybrid,/Stage híbrido/);
  assert.equal(Object.keys(engines).length,5);
  assert.equal(loadState(null).patches.piano.values.soundEngine,'physical');
  const storage={getItem:k=>k==='palco-stage-panel-v1'?
    JSON.stringify({patches:{piano:{preset:'american',values:{soundEngine:'hybrid'}}}}):null};
  assert.equal(loadState(storage).patches.piano.values.soundEngine,'hybrid');
  assert.equal(typeof OldB,'function');assert.equal(typeof OldC,'function');assert.equal(typeof ClaudeA,'function');
  assert.match(read('../acoustic.js'),/prepareHybrid/);
  assert.match(read('../acoustic.js'),/playHybrid/);
  assert.match(read('../app.js'),/prepareHybrid/);
  assert.match(read('../index.html'),/physical-piano-hybrid\.js\?build=1\.12\.5/);
  assert.doesNotMatch(read('../index.html'),/enable-mechanical-piano|stage-mechanics-link/);
});

test('fórmulas têm inarmonicidade positiva e contato reduzido com dureza',()=>{
  assert.ok(hybridInharmonicity(21)>hybridInharmonicity(60));
  assert.ok(hybridInharmonicity(108)>hybridInharmonicity(60));
  assert.ok(hybridContactTime(60,.8,.9)<hybridContactTime(60,.8,.1));
  assert.ok(hybridContactTime(60,.8,.5,'felt')>hybridContactTime(60,.8,.5,'american'));
});

test('D produz áudio finito, estéreo e não-silencioso no teclado completo',()=>{
  for(const key of [21,36,48,60,72,84,108]){
    const e=new HybridPianoEngine(48000,'eco');
    e.noteOn({id:1,key,speed:.76,hardness:.5,character:'american'});
    const r=render(e,.18);
    assert.ok(r.peak>.0004,`key ${key} silent: ${r.peak}`);
    assert.ok(r.peak<.97,`key ${key} exceeds output protection ${r.peak}`);
  }
});

test('D diferencia forte/piano e martelo suave/duro em energia de agudos',()=>{
  const soft=new HybridPianoEngine(48000),hard=new HybridPianoEngine(48000);
  soft.noteOn({id:1,key:60,speed:.22,hardness:.45,brightness:.5});
  hard.noteOn({id:1,key:60,speed:.93,hardness:.45,brightness:.5});
  const a=render(soft,.18),b=render(hard,.18);
  assert.ok(b.rms>a.rms*2.2,`wrong velocity dynamics: ${a.rms} ${b.rms}`);
  const warm=new HybridPianoEngine(48000),bright=new HybridPianoEngine(48000);
  warm.noteOn({id:2,key:60,speed:.65,hardness:.1,brightness:.45});
  bright.noteOn({id:2,key:60,speed:.65,hardness:.95,brightness:.45});
  const w=render(warm,.15),h=render(bright,.15);
  assert.ok(h.hf>w.hf,`hard hammer should add attack brightness: ${w.hf}, ${h.hf}`);
});

test('32/48/64 vozes podem coexistir sem roubo prematuro, com saída limitada',()=>{
  for(const [quality,n] of [['eco',32],['balanced',48],['studio',64]]){
    const e=new HybridPianoEngine(48000,quality);
    for(let i=0;i<n;i++)e.noteOn({id:i+1,key:36+i,speed:.86,hardness:.67,character:'american'});
    assert.equal(e.voices.filter(v=>v.active).length,n);
    assert.equal(e.done.length,0);
    const r=render(e,.10);
    assert.ok(r.peak<.97,`clipping on ${quality}: ${r.peak}`);
    assert.ok(r.rms>.00001,`silence on ${quality}`);
    assert.equal(e.maxVoices,HYBRID_QUALITY[quality].voices);
    e.stopAll();
  }
});

test('dampers, CC64 and panic release notes without changing engine selection',()=>{
  const e=new HybridPianoEngine(48000,'eco');
  e.noteOn({id:33,key:60,speed:.75});
  render(e,.10);
  e.setSustain(127);
  e.noteOff(33,false,.15);
  assert.equal(e.find(33).released,true);
  assert.equal(e.find(33).damped,false,'pedal should retain string damping');
  e.setSustain(0);
  assert.equal(e.find(33).damped,true);
  render(e,2.2);
  assert.equal(e.find(33),null,'note must decay after pedal up');
  e.noteOn({id:34,key:48,speed:.7});
  e.stopAll();
  render(e,1);
  assert.equal(e.find(34),null,'panic must terminate the note');
});

test('same notes have deterministic output and new model is distinct from A/B/C',()=>{
  const a=new HybridPianoEngine(48000),b=new HybridPianoEngine(48000);
  for(const engine of [a,b])engine.noteOn({id:1,key:60,speed:.7,character:'american'});
  const l=new Float32Array(128),r=new Float32Array(128),l2=new Float32Array(128),r2=new Float32Array(128);
  for(let i=0;i<80;i++){
    a.render(l,r,null,128);b.render(l2,r2,null,128);
    assert.deepEqual(l,l2);
    assert.deepEqual(r,r2);
  }
  const c=new OldC(48000,'eco');
  c.noteOn({id:1,key:60,speed:.7,character:'american'});
  c.render(l2,r2,null,128);
  a.render(l,r,null,128);
  assert.notDeepEqual(l,l2);
});

test('registerProcessor D recebe notas, qualidade, pedal e confirmação de fim',async()=>{
  let Processor;
  globalThis.sampleRate=48000;
  globalThis.AudioWorkletProcessor=class {
    constructor(){this.port={messages:[],postMessage(x){this.messages.push(x)}}}
  };
  globalThis.registerProcessor=(name,ctor)=>{if(name==='palco-piano-hybrid')Processor=ctor};
  try{
    await import('../physical-piano-hybrid.js?worklet-probe');
    assert.equal(typeof Processor,'function');
    const p=new Processor();
    p.port.onmessage({data:{type:'quality',quality:'studio'}});
    assert.equal(p.engine.maxVoices,64);
    p.port.onmessage({data:{type:'on',id:99,key:60,speed:.8}});
    p.port.onmessage({data:{type:'pedal',value:0}});
    const L=new Float32Array(128),R=new Float32Array(128),S=new Float32Array(128);
    let heard=false;
    for(let i=0;i<15;i++){assert.equal(p.process([],[[L,R],[S]]),true);if(L.some(x=>Math.abs(x)>1e-6))heard=true;}
    assert.equal(heard,true);
    p.port.onmessage({data:{type:'off',id:99,fast:true,release:.03}});
    for(let i=0;i<500;i++)p.process([],[[L,R],[S]]);
    assert.equal(p.engine.find(99),null);
    assert.ok(p.port.messages.some(x=>x.type==='done'&&x.ids.includes(99)));
  }finally{
    delete globalThis.sampleRate;delete globalThis.registerProcessor;delete globalThis.AudioWorkletProcessor;
  }
});
