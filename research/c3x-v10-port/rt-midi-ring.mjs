/**
 * Stage Synth / C3X V10 — Etapa 11B (pesquisa).
 * Fila MIDI FIFO com memória pré-alocada. A PRODUÇÃO deve enfileirar na
 * ordem temporal; enqueue() não pertence ao callback AudioWorklet.
 * Não se pode inferir comportamento hard real-time apenas por ausência
 * de alocações explícitas em processBlock().
 */
export const EVENT_NOTE_ON = 1;
export const EVENT_NOTE_OFF = 2;
export const EVENT_PEDAL = 3;
export const EVENT_ALL_OFF = 4;

function integer(name, x, min, max) {
  if (!Number.isSafeInteger(x) || x < min || x > max) {
    throw new RangeError(`${name} fora da faixa`);
  }
}

export class RtMidiRing {
  constructor({capacity = 1024, maxBlock = 256, sampleRate = 48000} = {}) {
    integer('capacity', capacity, 2, 1 << 20);
    integer('maxBlock', maxBlock, 1, 8192);
    integer('sampleRate', sampleRate, 8000, 192000);
    this.capacity = capacity;
    this.maxBlock = maxBlock;
    this.sampleRate = sampleRate;
    this.frame = new Float64Array(capacity);
    this.type = new Uint8Array(capacity);
    this.note = new Uint8Array(capacity);
    this.value = new Uint8Array(capacity);
    this.read = 0;
    this.write = 0;
    this.count = 0;
    this.cursor = 0;
    this.lastFrame = -1;
    this.overruns = 0;
  }

  /** Somente thread de preparação: tempo monotônico, eventos simultâneos FIFO. */
  enqueue({frame, type, note = 0, value = 0}) {
    integer('frame', frame, 0, Number.MAX_SAFE_INTEGER);
    if (frame < this.cursor || frame < this.lastFrame) throw new RangeError('evento fora de ordem ou atrasado');
    integer('type', type, EVENT_NOTE_ON, EVENT_ALL_OFF);
    if (type === EVENT_NOTE_ON || type === EVENT_NOTE_OFF) {
      integer('note', note, 0, 127);
      integer('velocity', value, 0, 127);
      if (type === EVENT_NOTE_ON && value === 0) type = EVENT_NOTE_OFF;
    } else if (type === EVENT_PEDAL) {
      integer('pedal', value, 0, 127);
    }
    if (this.count === this.capacity) {
      this.overruns++;
      throw new RangeError('fila MIDI cheia; nenhum evento descartado silenciosamente');
    }
    const i = this.write;
    this.frame[i] = frame;
    this.type[i] = type;
    this.note[i] = note;
    this.value[i] = value;
    this.write = (i + 1) % this.capacity;
    this.count++;
    this.lastFrame = frame;
  }

  enqueueSeconds({seconds, ...rest}) {
    if (!Number.isFinite(seconds) || seconds < 0) throw new RangeError('segundos inválidos');
    this.enqueue({frame: Math.round(seconds * this.sampleRate), ...rest});
  }

  /**
   * O chamador fornece dois Float32Array pré-alocados.
   * A interface do sintetizador exige onNoteOn/off, onPedal, allNotesOff
   * e renderSample(), que escreve os escalares .left/.right.
   * Zero criação explícita de arrays/objetos dentro do loop por amostra.
   */
  processBlock(left, right, synth) {
    const n = left.length;
    if (!(left instanceof Float32Array) || !(right instanceof Float32Array) || right.length !== n ||
        n < 1 || n > this.maxBlock) throw new RangeError('buffers inválidos ou bloco grande');
    if (!synth || typeof synth.renderSample !== 'function' ||
        typeof synth.onNoteOn !== 'function' || typeof synth.onNoteOff !== 'function' ||
        typeof synth.onPedal !== 'function' || typeof synth.allNotesOff !== 'function') {
      throw new TypeError('sintetizador incompatível');
    }
    const end = this.cursor + n;
    if (!Number.isSafeInteger(end)) throw new RangeError('cursor excedeu inteiro seguro');
    for (let i = 0; i < n; i++) {
      const now = this.cursor + i;
      while (this.count > 0 && this.frame[this.read] === now) {
        const j = this.read;
        const t = this.type[j];
        if (t === EVENT_NOTE_ON) synth.onNoteOn(this.note[j], this.value[j]);
        else if (t === EVENT_NOTE_OFF) synth.onNoteOff(this.note[j]);
        else if (t === EVENT_PEDAL) synth.onPedal(this.value[j]);
        else synth.allNotesOff();
        this.read = (j + 1) % this.capacity;
        this.count--;
      }
      // Segurança: detecta inconsistências em vez de esconder eventos perdidos.
      if (this.count > 0 && this.frame[this.read] < now) throw new Error('evento MIDI perdido');
      synth.renderSample();
      left[i] = synth.left;
      right[i] = synth.right;
    }
    this.cursor = end;
    if (this.count === 0) this.lastFrame = -1;
    return n;
  }

  clear({resetClock = false} = {}) {
    this.read = 0;
    this.write = 0;
    this.count = 0;
    this.lastFrame = -1;
    if (resetClock) this.cursor = 0;
  }
}