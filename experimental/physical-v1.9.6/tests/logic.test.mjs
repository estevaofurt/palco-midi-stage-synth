import test from 'node:test';
import assert from 'node:assert/strict';
import {engines, scenes, fromPreset, loadState, rememberPatch, maskForChannel, normalise, saveState} from '../patches.js';

const memoryStorage=()=>{
 const m=new Map();return {getItem:k=>m.get(k)||null,setItem:(k,v)=>m.set(k,v)};
};

test('cinco motores e um rack de efeitos independente',()=>{
 assert.deepEqual(Object.keys(engines),['piano','electric','organ','synth','sf']);
 const bits=Object.values(engines).map(e=>e.bit);
 assert.deepEqual(bits.sort((a,b)=>a-b),[1,2,4,8,16]);
 for(const scene of scenes)assert.ok((scene.mask&~31)===0);
});

test('presets completos com valores válidos',()=>{
 for(const [name,engine] of Object.entries(engines)){
  for(const preset of engine.presets){
   const patch=fromPreset(name,preset.id);
   assert.equal(patch.preset,preset.id);
   for(const group of engine.groups)for(const control of group.controls){
    if(['soundfont','samplepack'].includes(control.type))continue;
    assert.ok(Object.hasOwn(patch.values,control.id),`${name}/${preset.id}/${control.id}`);
    const v=patch.values[control.id];
    assert.deepEqual(normalise(control,v,control.initial),v);
   }
  }
 }
});

test('estado inválido não destrói timbres nem cenas',()=>{
 const s=memoryStorage();s.setItem('palco-stage-panel-v1',JSON.stringify({mask:99,editor:'missing',duo:true,patches:{organ:{preset:'bad',values:{bars:[100]}},synth:{values:{cutoff:-90}}}}));
 const state=loadState(s);
 assert.equal(state.mask,1);assert.equal(state.editor,'piano');
 assert.equal(state.patches.organ.values.bars.length,9);
 assert.ok(state.patches.synth.values.cutoff>=90);
});

test('cenas e separação de canais MIDI',()=>{
 const state=loadState(memoryStorage());state.mask=7;state.duo=true;
 assert.equal(maskForChannel(state,0),5);
 assert.equal(maskForChannel(state,1),2);
 assert.equal(maskForChannel(state,5),5);
 state.duo=false;assert.equal(maskForChannel(state,1),7);
});

test('edição, restauração e persistência de presets',()=>{
 const storage=memoryStorage();const state=loadState(storage);
 state.patches.piano.values.brightness=65;
 rememberPatch(state,'piano');
 assert.equal(state.edits.piano.japanese.brightness,65);
 saveState(storage,state);
 const loaded=loadState(storage);
 assert.equal(loaded.patches.piano.values.brightness,65);
 assert.equal(loaded.edits.piano.japanese.brightness,65);
 loaded.patches.piano.values=fromPreset('piano','japanese').values;
 rememberPatch(loaded,'piano');
 assert.equal(loaded.edits.piano.japanese,undefined);
});
