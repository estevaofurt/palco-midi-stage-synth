import test from 'node:test';
import assert from 'node:assert/strict';
import {fromPreset, engines, loadState, presetForInstrument, presetsForInstrument} from '../patches.js';
import {targetFrequency, unisonCount} from '../synth.js';

function store(value) {return {getItem:key=>key==='palco-stage-panel-v1'?JSON.stringify(value):null}}

test('B3 Jazz e B3 Gospel são instrumentos selecionáveis de modo independente',()=>{
 const selector=engines.organ.groups.flatMap(group=>group.controls).find(c=>c.id==='registration');
 assert.deepEqual(Object.keys(selector.options),['jazz','gospel','church']);
 for(const [model,id] of [['jazz','jazz'],['gospel','gospel'],['church','church']]){
  const patch=fromPreset('organ',id);
  assert.equal(patch.values.registration,model);
  assert.equal(presetForInstrument('organ',model).id,id);
  assert.equal(presetsForInstrument('organ',patch.values).length,3);
 }
 assert.notDeepEqual(fromPreset('organ','jazz').values.bars,fromPreset('organ','gospel').values.bars);
});

test('estado legado de B3 preserva jazz e gospel após migração',()=>{
 for(const id of ['jazz','gospel','church']){
  const state=loadState(store({patches:{organ:{preset:id,values:{type:id==='church'?'church':'b3'}}}}));
  assert.equal(state.patches.organ.values.registration,id);
 }
 // Uma seleção Church antiga sobre um preset B3 prevalece.
 const state=loadState(store({patches:{organ:{preset:'jazz',values:{type:'church'}}}}));
 assert.equal(state.patches.organ.values.registration,'church');
 assert.equal(state.patches.organ.preset,'church');
});

test('portamento calcula alturas para qualquer modo de voz',()=>{
 const p=fromPreset('synth','velvet').values;
 assert.equal(unisonCount({...p,unison:'3'}),3);
 assert.equal(unisonCount({...p,unison:'1'}),1);
 assert.ok(targetFrequency(72,p)>targetFrequency(60,p)*1.99);
});
