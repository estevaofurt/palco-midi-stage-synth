import test from 'node:test';
import assert from 'node:assert/strict';
import {engines,fromPreset,loadState,instrumentField,presetsForInstrument,presetForInstrument,instrumentName} from '../patches.js';
import {sampleDescriptor,SampleLibrary} from '../sample-library.js';

test('preset de fábrica é distinto do instrumento selecionado',()=>{
  assert.equal(instrumentField.electric,'model');
  assert.equal(instrumentName('electric',fromPreset('electric','mark1').values),'Rhodes Tine · Mark I');
  const mark1=presetsForInstrument('electric',fromPreset('electric','mark1').values);
  assert.equal(mark1.length,3);
  assert.deepEqual(mark1.map(p=>p.id),['mark1','mark1-soft','mark1-bright']);
  assert.equal(presetForInstrument('electric','fmballad').id,'fmballad');
  assert.equal(presetsForInstrument('piano',fromPreset('piano','felt').values).length,3);
});
test('Auto-Pan substitui o Pan estático dos elétricos',()=>{
  const ctrl=engines.electric.groups.flatMap(g=>g.controls);
  assert.equal(ctrl.some(c=>c.id==='pan'),false);
  assert.equal(ctrl.find(c=>c.id==='autoPan').label,'Auto-Pan');
  assert.equal(ctrl.find(c=>c.id==='autoPanRate').unit,' Hz');
  assert.equal(fromPreset('electric','mark1').values.autoPan,0);
});
test('migração mantém timbre antigo sem contradizer o instrumento escolhido',()=>{
  const storage={getItem:k=>k==='palco-stage-panel-v1'?JSON.stringify({patches:{electric:{preset:'mark1',values:{model:'fmballad',pan:30}}}}):null};
  const state=loadState(storage);
  assert.equal(state.patches.electric.values.model,'fmballad');
  assert.equal(state.patches.electric.preset,'fmballad');
  assert.equal(state.patches.electric.values.autoPan,0);
});
test('nomes dos samples são convertidos em MIDI e velocity',()=>{
  assert.deepEqual(sampleDescriptor('C4_v40.wav'),{root:60,velocity:40});
  assert.deepEqual(sampleDescriptor('Db4_v100.wav'),{root:61,velocity:100});
  assert.deepEqual(sampleDescriptor('MIDI64_v127.WAV'),{root:64,velocity:127});
  assert.equal(sampleDescriptor('piano_sem_nota.wav'),null);
});
test('amostras são isoladas por instrumento e respeitam velocidade',()=>{
  const library=new SampleLibrary({});
  library.banks.set('mark1',[{root:60,velocity:30},{root:60,velocity:100},{root:64,velocity:100}]);
  assert.equal(library.choose('mark1',61,34).velocity,30);
  assert.equal(library.choose('mark1',61,90).velocity,100);
  assert.equal(library.choose('mark2',61,90),null);
  assert.equal(library.choose('mark1',90,100),null);
});
