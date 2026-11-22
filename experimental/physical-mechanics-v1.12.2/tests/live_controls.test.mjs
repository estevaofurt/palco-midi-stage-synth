import test from 'node:test';
import assert from 'node:assert/strict';
import {PianoEngine} from '../piano-worklet.js';
import {engines} from '../patches.js';

test('todos os cinco instrumentos mantêm seus identificadores',()=>{
  assert.deepEqual(Object.keys(engines),['piano','electric','organ','synth','sf']);
});
test('abafamento modal alterado durante a nota atualiza os ressonadores',()=>{
  const engine=new PianoEngine(48000);
  engine.noteOn({id:97,key:64,speed:.8,decayScale:1});
  const voice=engine.find(97);
  assert.ok(voice);
  const before=Math.hypot(voice.cr[0],voice.ci[0]);
  engine.updateVoice(97,{decayScale:.42});
  assert.equal(voice.decayScale,.42);
  assert.ok(Math.hypot(voice.cr[0],voice.ci[0])<before);
  engine.updateVoice(97,{decayScale:1.5});
  assert.ok(Math.hypot(voice.cr[0],voice.ci[0])>before);
  engine.noteOff(97,true,.05);
  const r=voice.cr[0];
  engine.updateVoice(97,{decayScale:.5});
  assert.equal(voice.cr[0],r); // não reabrir um abafador já fechado
});
