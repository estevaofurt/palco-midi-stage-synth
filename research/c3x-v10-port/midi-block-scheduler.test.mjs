import test from 'node:test';
import assert from 'node:assert/strict';
import { MidiBlockScheduler } from './midi-block-scheduler.mjs';

test('mesmos eventos com blocos 64/128/256, tempos absolutos iguais', () => {
  const sequence = [
    { frame: 0, type: 'note-on', note: 60, velocity: 88 },
    { frame: 127, type: 'cc64', value: 127 },
    { frame: 128, type: 'note-off', note: 60 },
    { frame: 255, type: 'note-on', note: 64, velocity: 72 },
    { frame: 256, type: 'note-off', note: 64 },
    { frame: 511, type: 'cc64', value: 0 },
  ];
  for (const frames of [64, 128, 256]) {
    const scheduler = new MidiBlockScheduler();
    sequence.forEach(e => scheduler.enqueue(e));
    const actual = [];
    for (let i = 0; i < 512 / frames; i++) {
      const block = scheduler.drain(frames);
      block.events.forEach(e => actual.push({ frame: block.startFrame + e.sampleOffset, type: e.type, note: e.note, velocity: e.velocity, value: e.value }));
    }
    const expected = sequence.map(e => ({ frame: e.frame, type: e.type, note: e.note ?? null, velocity: e.velocity ?? 0, value: e.value ?? 0 }));
    assert.deepEqual(actual, expected);
  }
});

test('eventos no limite pertencem ao próximo bloco', () => {
  const s = new MidiBlockScheduler();
  s.enqueue({ frame: 64, type: 'note-on', note: 69, velocity: 90 });
  assert.equal(s.drain(64).events.length, 0);
  assert.equal(s.drain(64).events[0].sampleOffset, 0);
});

test('eventos simultâneos preservam a ordem de chegada', () => {
  const s = new MidiBlockScheduler();
  s.enqueue({ frame: 4, type: 'note-off', note: 60 });
  s.enqueue({ frame: 4, type: 'note-on', note: 60, velocity: 60 });
  assert.deepEqual(s.drain(16).events.map(e => e.type), ['note-off', 'note-on']);
  assert.equal(s.heldNotes.has(60), true);
});

test('note-on com velocity zero vira note-off', () => {
  const s = new MidiBlockScheduler();
  s.enqueue({ frame: 0, type: 'note-on', note: 60, velocity: 0 });
  assert.equal(s.drain(128).events[0].type, 'note-off');
});

test('segundos são convertidos em frames determinísticos em 44,1/48k', () => {
  for (const sampleRate of [44100, 48000]) {
    const s = new MidiBlockScheduler({ sampleRate });
    s.enqueueAtSeconds({ seconds: 0.01, type: 'note-on', note: 69, velocity: 90 });
    const events = [];
    while (s.nextFrame <= Math.round(sampleRate * .01)) {
      const b = s.drain(64); events.push(...b.events.map(e => b.startFrame + e.sampleOffset));
    }
    assert.deepEqual(events, [Math.round(sampleRate * .01)]);
  }
});

test('pedal e estados são mantidos entre blocos', () => {
  const s = new MidiBlockScheduler();
  s.enqueue({ frame: 16, type: 'note-on', note: 69, velocity: 60 });
  s.enqueue({ frame: 200, type: 'cc64', value: 100 });
  assert.equal(s.drain(128).heldCount, 1);
  assert.equal(s.drain(128).pedal, 100);
  assert.equal(s.drain(128).heldCount, 1);
});

test('rejeita eventos atrasados e formatos inválidos explicitamente', () => {
  const s = new MidiBlockScheduler();
  s.drain(64);
  assert.throws(() => s.enqueue({ frame: 2, type: 'note-on', note: 60, velocity: 90 }), RangeError);
  assert.throws(() => s.enqueue({ frame: 65, type: 'note-on', note: 128 }), RangeError);
  assert.throws(() => s.enqueue({ frame: 65, type: 'cc64', value: -1 }), RangeError);
});
