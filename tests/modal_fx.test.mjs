import test from 'node:test';
import assert from 'node:assert/strict';
import {loadState,engines,effectsDefinition,fromPreset} from '../patches.js';
import {PianoEngine,inharmonicity} from '../piano-worklet.js';

const storage=obj=>({getItem:key=>key==='palco-stage-panel-v1'?JSON.stringify(obj):null});
test('efeitos suportam vários destinos e mantêm o bypass por módulo',()=>{
 const state=loadState(null);
 assert.equal(effectsDefinition.length,8);
 assert.deepEqual(state.fx.slots.reverb1.targets,['piano']);
 for(const id of Object.keys(engines))assert.equal(state.fx.enabled[id],false);
 const changed=loadState(storage({fx:{enabled:{piano:true,synth:false},slots:{delay1:{active:true,targets:['piano','synth','piano','invalid']}}}}));
 assert.deepEqual(changed.fx.slots.delay1.targets,['piano','synth']);
 assert.equal(changed.fx.enabled.piano,true);
 assert.equal(changed.fx.enabled.synth,false);
});
test('migração do destino único não perde a sessão antiga',()=>{
 const state=loadState(storage({fx:{slots:{reverb2:{active:true,target:'organ',mix:35}}}}));
 assert.deepEqual(state.fx.slots.reverb2.targets,['organ']);
 assert.equal(state.fx.slots.reverb2.mix,35);
});
test('um módulo pode estar sem destino, mantendo som seco',()=>{
 const state=loadState(storage({fx:{slots:{mod1:{targets:[]}}}}));
 assert.deepEqual(state.fx.slots.mod1.targets,[]);
});
test('piano oferece motor modal e síntese clássica',()=>{
 const modes=engines.piano.groups.flatMap(g=>g.controls).find(c=>c.id==='soundEngine');
 assert.ok(modes);assert.equal(modes.options.physical,'B · Novo Stage (mecânico)');
 assert.equal(modes.options.modal,'A · Claude (modal)');
 assert.equal(fromPreset('piano','felt').values.soundEngine,'physical');
});
test('motor modal reage à força e termina após liberação',()=>{
 const engine=new PianoEngine(48000),L=new Float32Array(128),R=new Float32Array(128),S=new Float32Array(128);
 engine.noteOn({id:1,key:60,speed:.8,hardness:.5,character:'felt'});
 engine.render(L,R,S,128);
 assert.ok(L.some(x=>Math.abs(x)>1e-8));
 assert.ok(Number.isFinite(inharmonicity(60)));
 engine.noteOff(1,true,.08);
 for(let i=0;i<700;i++)engine.render(L,R,S,128);
 assert.equal(engine.find(1),null);
});
