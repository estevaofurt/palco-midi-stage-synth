/**
 * STAGE SYNTH C3X V10 -> Etapa 11 (pesquisa)
 * Agendador de eventos MIDI por frame. NÃO gera áudio ou executa Python.
 * Integração WebAudio/AudioWorklet e RT-safe ainda pendentes.
 */
const VALID_TYPES = new Set(['note-on', 'note-off', 'cc64', 'all-notes-off']);

export class MidiBlockScheduler {
  constructor({ sampleRate = 48000 } = {}) {
    if (!Number.isInteger(sampleRate) || sampleRate < 8000 || sampleRate > 192000)
      throw new RangeError('sampleRate inválido');
    this.sampleRate = sampleRate;
    this.nextFrame = 0;
    this.queue = [];
    this.serial = 0;
    this.pedal = 0;
    this.heldNotes = new Set();
  }

  enqueue({ frame, type, note = null, velocity = 0, value = 0 }) {
    if (!Number.isSafeInteger(frame) || frame < this.nextFrame) throw new RangeError('frame anterior ao cursor ou inválido');
    if (!VALID_TYPES.has(type)) throw new TypeError('evento MIDI inválido');
    if (type === 'note-on' || type === 'note-off') {
      if (!Number.isInteger(note) || note < 0 || note > 127) throw new RangeError('nota MIDI inválida');
      if (!Number.isInteger(velocity) || velocity < 0 || velocity > 127) throw new RangeError('velocidade inválida');
      if (type === 'note-on' && velocity === 0) type = 'note-off';
    }
    if (type === 'cc64' && (!Number.isInteger(value) || value < 0 || value > 127))
      throw new RangeError('valor do pedal inválido');
    this.queue.push({ frame, type, note, velocity, value, serial: this.serial++ });
  }

  enqueueAtSeconds({ seconds, ...event }) {
    if (!Number.isFinite(seconds) || seconds < 0) throw new RangeError('seconds inválido');
    this.enqueue({ ...event, frame: Math.round(seconds * this.sampleRate) });
  }

  /** Retorna eventos com sampleOffset em [0, frames), sem renderizar áudio. */
  drain(frames = 128) {
    if (!Number.isInteger(frames) || frames < 1 || frames > 8192) throw new RangeError('frames inválido');
    const end = this.nextFrame + frames;
    this.queue.sort((a, b) => a.frame - b.frame || a.serial - b.serial);
    let split = 0;
    while (split < this.queue.length && this.queue[split].frame < end) split++;
    const events = this.queue.slice(0, split).map(({ frame, type, note, velocity, value }) => {
      if (type === 'note-on') this.heldNotes.add(note);
      else if (type === 'note-off') this.heldNotes.delete(note);
      else if (type === 'cc64') this.pedal = value;
      else if (type === 'all-notes-off') this.heldNotes.clear();
      return { sampleOffset: frame - this.nextFrame, type, note, velocity, value };
    });
    this.queue = this.queue.slice(split);
    const block = { startFrame: this.nextFrame, frames, events, pedal: this.pedal, heldCount: this.heldNotes.size };
    this.nextFrame = end;
    return block;
  }
}