import test from 'node:test';
import assert from 'node:assert/strict';
import {engines,loadState,fromPreset,presetsForInstrument,instrumentName,presetForInstrument} from '../patches.js';

test('CP70 replaces CP80 and has independent Natural / Suave / Brilhante presets',()=>{
  const opts=engines.electric.groups.flatMap(g=>g.controls).find(c=>c.id==='model').options;
  assert.equal(opts.cp70,'CP70');assert.equal('cp80' in opts,false);
  assert.equal(fromPreset('electric','cp70').values.model,'cp70');
  assert.deepEqual(presetsForInstrument('electric',{model:'cp70'}).map(p=>p.id),['cp70','cp70-soft','cp70-bright']);
  assert.equal(presetForInstrument('electric','cp70').id,'cp70');
});

test('E. Piano 1/2/3 names correspond exactly to Full Tines, Dino EP, Ballad Keys',()=>{
  assert.equal(instrumentName('electric',fromPreset('electric','fmfull').values),'E. Piano 1 · Full Tines');
  assert.equal(instrumentName('electric',fromPreset('electric','fmdino').values),'E. Piano 2 · Dino EP');
  assert.equal(instrumentName('electric',fromPreset('electric','fmballad').values),'E. Piano 3 · Ballad Keys');
});

test('old CP80 save migrates selection and user edits to CP70 (Natural and variations)',()=>{
  const old={patches:{electric:{preset:'cp80-soft',level:61,values:{model:'cp80',hammer:31,decay:45}}},
    edits:{electric:{'cp80-soft':{model:'cp80',hammer:31,pickup:29},'cp80-bright':{model:'cp80',hammer:93}}}};
  const storage={getItem:k=>k==='palco-stage-panel-v1'?JSON.stringify(old):null};
  const state=loadState(storage);
  assert.equal(state.patches.electric.values.model,'cp70');
  assert.equal(state.patches.electric.preset,'cp70-soft');
  assert.equal(state.patches.electric.level,61);
  assert.equal(state.patches.electric.values.hammer,31);
  assert.equal(state.edits.electric['cp70-soft'].hammer,31);
  assert.equal(state.edits.electric['cp70-soft'].model,'cp70');
  assert.equal(state.edits.electric['cp70-bright'].hammer,93);
  assert.equal(state.edits.electric['cp70-bright'].model,'cp70');
});

test('old CP80 legacy model with no modern electric patch migrates safely',()=>{
  const storage={getItem:k=>k==='palco-electric-v1'?JSON.stringify({model:'cp80',hammer:79}):null};
  const state=loadState(storage);
  assert.equal(state.patches.electric.values.model,'cp70');
  assert.equal(state.patches.electric.preset,'cp70');
  assert.equal(state.patches.electric.values.hammer,79);
});
