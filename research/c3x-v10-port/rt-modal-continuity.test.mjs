import test from 'node:test';
import assert from 'node:assert/strict';
import { RtMidiRing, EVENT_NOTE_ON, EVENT_NOTE_OFF, EVENT_PEDAL, EVENT_ALL_OFF } from './rt-midi-ring.mjs';
import { ModalContinuityProbe } from './modal-continuity-probe.mjs';

const score = [
  {frame: 0, type: EVENT_NOTE_ON, note: 69, value: 85},
  {frame: 127, type: EVENT_PEDAL, value: 127},
  {frame: 128, type: EVENT_NOTE_OFF, note: 69},
  {frame: 255, type: EVENT_NOTE_ON, note: 64, value: 106},
  {frame: 256, type: EVENT_NOTE_OFF, note: 64},
  {frame: 512, type: EVENT_NOTE_ON, note: 69, value: 115},
  {frame: 513, type: EVENT_NOTE_OFF, note: 69},
  {frame: 1024, type: EVENT_PEDAL, value: 0},
  {frame: 1536, type: EVENT_ALL_OFF},
];
function render(framesPerBlock, events=score, total=2048, sampleRate=48000) {
  const queue = new RtMidiRing({maxBlock: framesPerBlock, sampleRate});
  const synth = new ModalContinuityProbe({sampleRate});
  for (const e of events) queue.enqueue(e);
  const out = new Float32Array(total * 2);
  const l = new Float32Array(framesPerBlock), r = new Float32Array(framesPerBlock);
  for (let base = 0; base < total; base += framesPerBlock) {
    queue.processBlock(l, r, synth);
    for (let i = 0; i < framesPerBlock; i++) {
      out[(base+i)*2] = l[i]; out[(base+i)*2+1] = r[i];
    }
  }
  return {out, queue, synth};
}

function energy(arr, begin, end) {
  let sum = 0;
  for (let i = begin; i < end; i++) sum += arr[2*i] ** 2 + arr[2*i+1] ** 2;
  return sum;
}

test('partition invariance: 64, 128 e 256 frames produzem exatamente as mesmas amostras', () => {
  const ref = render(64);
  for (const size of [128, 256]) {
    const v = render(size);
    assert.deepEqual(v.out, ref.out);
    assert.equal(v.queue.cursor, 2048);
    assert.equal(v.queue.count, 0);
  }
  assert.ok(energy(ref.out, 10, 2048) > 1e-7);
});

test('eventos precisamente no limite pertencem ao bloco seguinte', () => {
  const q = new RtMidiRing({maxBlock: 64});
  const s = new ModalContinuityProbe();
  q.enqueue({frame: 64, type: EVENT_NOTE_ON, note: 69, value: 90});
  const l = new Float32Array(64), r = new Float32Array(64);
  q.processBlock(l, r, s);
  assert.equal(s.strikes, 0);
  q.processBlock(l, r, s);
  assert.equal(s.strikes, 1);
});

test('estado físico da nota sobrevive entre blocos e mesmo MIDI recebe outro martelo', () => {
  const s = new ModalContinuityProbe();
  const q = new RtMidiRing({maxBlock: 64});
  q.enqueue({frame: 0, type: EVENT_NOTE_ON, note: 69, value: 90});
  q.enqueue({frame: 64, type: EVENT_NOTE_ON, note: 69, value: 90});
  const l = new Float32Array(64), r = new Float32Array(64);
  q.processBlock(l, r, s);
  const before = s.q.slice(48*10, 49*10); // MIDI 69 - 21 = 48
  assert.ok(before.some(v => Math.abs(v)>1e-12));
  q.processBlock(l, r, s);
  assert.equal(s.strikes, 2);
  assert.ok(s.q.slice(48*10,49*10).some(v=>Math.abs(v)>1e-12));
  assert.equal(s.held[48], 1);
});

test('note-on com velocity 0 equivale a note-off', () => {
  const q = new RtMidiRing({maxBlock: 64});
  const s = new ModalContinuityProbe();
  q.enqueue({frame: 0, type: EVENT_NOTE_ON, note: 69, value: 80});
  q.enqueue({frame: 10, type: EVENT_NOTE_ON, note: 69, value: 0});
  q.processBlock(new Float32Array(64), new Float32Array(64), s);
  assert.equal(s.held[48], 0);
  assert.equal(s.strikes, 1);
});

test('FIFO de eventos simultâneos: último comando de tecla prevalece', () => {
  const exec = (a,b) => {
    const q = new RtMidiRing({maxBlock: 64});
    const s = new ModalContinuityProbe();
    q.enqueue({frame:0, type:a, note:69, value:90});
    q.enqueue({frame:0, type:b, note:69, value:90});
    q.processBlock(new Float32Array(64),new Float32Array(64),s);
    return s.held[48];
  };
  assert.equal(exec(EVENT_NOTE_ON,EVENT_NOTE_OFF),0);
  assert.equal(exec(EVENT_NOTE_OFF,EVENT_NOTE_ON),1);
});

test('pedal conserva mais energia depois da soltura, sem reverb', () => {
  function tail(pedal) {
    const ev = [
      {frame:0, type:EVENT_NOTE_ON, note:69, value:90},
      {frame:96, type:EVENT_PEDAL, value:pedal},
      {frame:128, type:EVENT_NOTE_OFF, note:69},
    ];
    const r=render(128,ev,8192);
    return energy(r.out,4096,8192);
  }
  const no = tail(0), yes=tail(127);
  assert.ok(yes > no * 3, `pedal on=${yes}, off=${no}`);
});

test('posição parcial do pedal resulta em decaimento intermediário', () => {
  function tail(pedal) {
    const ev = [
      {frame:0, type:EVENT_NOTE_ON, note:69, value:80},
      {frame:96, type:EVENT_PEDAL, value:pedal},
      {frame:128, type:EVENT_NOTE_OFF, note:69},
    ];
    return energy(render(128,ev,8192).out,4096,8192);
  }
  const a=tail(0), b=tail(64), c=tail(127);
  assert.ok(a<b&&b<c, `${a},${b},${c}`);
});

test('rejeita ordem temporal retroativa sem reordenar durante áudio', () => {
  const q=new RtMidiRing({capacity:2});
  q.enqueue({frame:128,type:EVENT_NOTE_ON,note:60,value:90});
  assert.throws(()=>q.enqueue({frame:127,type:EVENT_NOTE_OFF,note:60}),RangeError);
  assert.equal(q.count,1);
});

test('capacidade fixa: overflow explícito, sem perda silenciosa', () => {
  const q=new RtMidiRing({capacity:2});
  q.enqueue({frame:1,type:EVENT_NOTE_ON,note:60,value:80});
  q.enqueue({frame:2,type:EVENT_NOTE_OFF,note:60});
  assert.throws(()=>q.enqueue({frame:3,type:EVENT_NOTE_ON,note:61,value:80}),/cheia/);
  assert.equal(q.count,2);assert.equal(q.overruns,1);
});

test('inserção após processar um bloco aceita próximo cursor', () => {
  const q=new RtMidiRing({capacity:4,maxBlock:64});
  const s=new ModalContinuityProbe();
  const l=new Float32Array(64),r=new Float32Array(64);
  q.processBlock(l,r,s);
  q.enqueue({frame:64,type:EVENT_NOTE_ON,note:60,value:90});
  q.processBlock(l,r,s);
  assert.equal(s.strikes,1);
  assert.equal(q.cursor,128);
});

test('all-notes-off preserva o áudio de soltura e zera o pedal', () => {
  const q=new RtMidiRing({maxBlock:64});
  const s=new ModalContinuityProbe();
  q.enqueue({frame:0,type:EVENT_NOTE_ON,note:69,value:90});
  q.enqueue({frame:0,type:EVENT_PEDAL,value:127});
  q.enqueue({frame:32,type:EVENT_ALL_OFF});
  q.processBlock(new Float32Array(64),new Float32Array(64),s);
  assert.equal(s.held[48],0);assert.equal(s.pedal,0);
  assert.equal(s.strikes,1);
});

test('reprodutibilidade das mesmas notas em 44,1 e 48 kHz', () => {
  for(const rate of [44100,48000]){
    const a=render(64,score,2048,rate),b=render(256,score,2048,rate);
    assert.deepEqual(a.out,b.out);
    assert.ok(a.out.every(Number.isFinite));
  }
});

test('parâmetros inválidos e buffer incorreto são rejeitados', () => {
  assert.throws(()=>new RtMidiRing({capacity:0}),RangeError);
  assert.throws(()=>new ModalContinuityProbe({sampleRate:22050}),RangeError);
  const q=new RtMidiRing({maxBlock:64}),s=new ModalContinuityProbe();
  assert.throws(()=>q.processBlock(new Float32Array(64),new Float32Array(63),s),RangeError);
  assert.throws(()=>q.enqueue({frame:0,type:EVENT_PEDAL,value:128}),RangeError);
});

// Teste de não-alocação em processBlock() é somente inspeção de código.
// Não é prova de GC zero, ausência de jitter ou prontidão AudioWorklet.