/**
 * PROVA DE CONTINUIDADE — NÃO É O MOTOR V10 E NÃO SUBSTITUI O V8 WEB.
 * Osciladores modais amortecidos com acoplamento simples de excitação.
 * Sintetiza do zero, sem samples, IR de sala ou convolução. Este bloco
 * demonstra preservação de q/v das cordas através de callbacks sucessivos.
 * Os parâmetros físicos NÃO são medições do Yamaha C3X.
 */
const MIDI_MIN = 21;
const MIDI_MAX = 108;
const NOTES = MIDI_MAX - MIDI_MIN + 1;

export class ModalContinuityProbe {
  constructor({sampleRate = 48000, partials = 10} = {}) {
    if (![44100, 48000].includes(sampleRate)) throw new RangeError('taxa de teste deve ser 44,1 ou 48 kHz');
    if (!Number.isInteger(partials) || partials < 1 || partials > 20) throw new RangeError('parciais inválidos');
    this.sampleRate = sampleRate;
    this.partials = partials;
    const count = NOTES * partials;
    this.q = new Float64Array(count);
    this.v = new Float64Array(count);
    this.cos = new Float64Array(count);
    this.sinOverOmega = new Float64Array(count);
    this.omegaSin = new Float64Array(count);
    this.decay = new Float64Array(count);
    this.shape = new Float64Array(count);
    this.held = new Uint8Array(NOTES);
    this.active = new Uint8Array(NOTES);
    this.pedal = 0;
    this.left = 0;
    this.right = 0;
    this.strikes = 0;
    this.damperStep = Math.exp(-42 / sampleRate);
    for (let note = MIDI_MIN; note <= MIDI_MAX; note++) {
      const f0 = 440 * Math.pow(2, (note - 69) / 12);
      // Curva artificial e aproximada; NÃO corresponde à escala C3X validada.
      const B = 0.0001;
      const t = (note - MIDI_MIN) / (NOTES - 1);
      const hammerPosition = 0.14 - 0.035 * t;
      for (let k = 1; k <= partials; k++) {
        const i = (note - MIDI_MIN) * partials + (k - 1);
        const f = f0 * k * Math.sqrt((1 + B * k * k) / (1 + B));
        const omega = 2 * Math.PI * f;
        this.shape[i] = Math.sin(Math.PI * k * hammerPosition) / (k * k);
        if (f >= sampleRate * 0.43) {
          this.shape[i] = 0;
          continue;
        }
        const theta = omega / sampleRate;
        this.cos[i] = Math.cos(theta);
        this.sinOverOmega[i] = Math.sin(theta) / omega;
        this.omegaSin[i] = omega * Math.sin(theta);
        this.decay[i] = Math.exp(-(0.7 + 0.18 * Math.pow(k, 1.3)) / sampleRate);
      }
    }
  }

  onNoteOn(note, velocity) {
    if (note < MIDI_MIN || note > MIDI_MAX) return;
    const n = note - MIDI_MIN;
    this.held[n] = 1;
    this.active[n] = 1;
    this.strikes++;
    const gain = 0.0018 * Math.pow(velocity / 127, 1.6);
    for (let k = 0; k < this.partials; k++) {
      const i = n * this.partials + k;
      // Reinjetar energia do martelo SEM reinicializar q e v da corda.
      // A amplitude modal nasce de um impulso à velocidade; usar a escala
      // de 1/(k+1) limita o crescimento de energia nos agudos.
      this.v[i] += gain * this.shape[i] * (k + 1) * 440;
    }
  }

  onNoteOff(note) {
    if (note >= MIDI_MIN && note <= MIDI_MAX) this.held[note - MIDI_MIN] = 0;
  }

  onPedal(value) {
    this.pedal = value / 127;
    this.damperStep = Math.exp(-42 * (1 - this.pedal) / this.sampleRate);
  }
  allNotesOff() { this.held.fill(0); this.onPedal(0); }

  renderSample() {
    let left = 0;
    let right = 0;
    for (let n = 0; n < NOTES; n++) {
      if (!this.active[n]) continue;
      const damp = this.held[n] ? 1 : this.damperStep;
      const base = n * this.partials;
      let noteOutput = 0;
      let energy = 0;
      for (let k = 0; k < this.partials; k++) {
        const i = base + k;
        const q = this.q[i], v = this.v[i], c = this.cos[i];
        const d = this.decay[i] * damp;
        const nextQ = d * (q * c + v * this.sinOverOmega[i]);
        const nextV = d * (v * c - q * this.omegaSin[i]);
        this.q[i] = nextQ;
        this.v[i] = nextV;
        noteOutput += nextQ * this.shape[i];
        energy += Math.abs(nextQ) + Math.abs(nextV) * 0.00003;
      }
      if (energy < 1e-10 && !this.held[n]) this.active[n] = 0;
      const pan = n / (NOTES - 1);
      left += noteOutput * (0.85 - 0.25 * pan);
      right += noteOutput * (0.60 + 0.25 * pan);
    }
    this.left = left;
    this.right = right;
  }
}