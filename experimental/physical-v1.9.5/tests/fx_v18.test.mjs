import test from 'node:test';
import assert from 'node:assert/strict';
import {effectsDefinition,loadState,reverbTypes,delayTypes,modulationTypes,eqTypes,defaultSlot,engines} from '../patches.js';

const saved=x=>({getItem:()=>JSON.stringify(x)});
test('rack mantém oito slots e admite seis reverbs, três delays e quatro modulações',()=>{
  assert.equal(effectsDefinition.length,8);
  assert.deepEqual(Object.keys(reverbTypes),['hall','room','plate','spring','church','shimmer']);
  assert.deepEqual(Object.keys(delayTypes),['tape','analog','digital']);
  assert.deepEqual(Object.keys(modulationTypes),['chorus','flanger','phaser','wah']);
  assert.deepEqual(Object.keys(eqTypes),['parametric','graphic']);
});
test('equalizador e compressor usam insert (100% por padrão)',()=>{
  assert.equal(defaultSlot('eq').mix,100);
  assert.equal(defaultSlot('comp').mix,100);
  assert.ok(defaultSlot('comp').attack>0);
  assert.ok(defaultSlot('comp').release>0);
  assert.equal(defaultSlot('comp').makeup,0);
});
test('configurações dos efeitos sobrevivem à persistência e à migração',()=>{
  const initial={fx:{enabled:{piano:true,organ:false},slots:{
    reverb1:{active:true,targets:['piano','organ'],reverbType:'shimmer',time:3.2},
    delay2:{active:true,targets:['synth'],delayType:'analog'},
    mod1:{active:true,targets:['piano','synth'],modType:'wah'},
    eq:{active:true,targets:['piano'],eqType:'graphic',eq500:-7},
    comp:{active:true,targets:['piano'],threshold:-25,ratio:6,attack:.016,release:.33,makeup:3.5}
  }}};
  const state=loadState(saved(initial));
  assert.deepEqual(state.fx.slots.reverb1.targets,['piano','organ']);
  assert.equal(state.fx.slots.reverb1.reverbType,'shimmer');
  assert.equal(state.fx.slots.delay2.delayType,'analog');
  assert.equal(state.fx.slots.mod1.modType,'wah');
  assert.equal(state.fx.slots.eq.eqType,'graphic');
  assert.equal(state.fx.slots.eq.eq500,-7);
  assert.equal(state.fx.slots.comp.ratio,6);
  assert.equal(state.fx.slots.comp.makeup,3.5);
  assert.equal(state.fx.enabled.organ,false);
  const old=loadState(saved({fx:{slots:{comp:{threshold:-20,ratio:4},mod1:{depth:70}}}}));
  assert.equal(old.fx.slots.comp.knee,6);
  assert.equal(old.fx.slots.mod1.modType,'chorus');
  assert.equal(old.fx.slots.eq.eqType,'parametric');
  assert.equal(Object.keys(engines).length,5);
});
