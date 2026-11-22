// Motor de piano por modelagem física modal (v0) — Palco MIDI.
//
// Cada nota é um conjunto de ressonadores (modos) que representam os parciais
// de uma corda rígida de piano:
//     f_n = n · f0 · √(1 + B·n²)            (inarmonicidade da corda)
// O martelo entra como um pulso de força em meio-seno cuja duração diminui com
// a velocidade e com a dureza do feltro. O espectro desse pulso define a
// amplitude inicial de cada modo: tocar mais forte deixa o timbre mais
// brilhante sem trocar de amostra. A posição de batida do martelo (β) apaga
// alguns parciais, como num piano real.
//
// Arquivo único, sem dependências e sem alocação no laço de áudio: o mesmo
// código roda no AudioWorklet (navegador) e no Node (tests/piano_model.test.mjs).

export const MAX_VOICES = 32;
const MAX_MODES = 96;
const BLOCK = 1024;          // maior bloco aceito por render()
const TARGET_RMS = .075;     // nível de uma nota ff (antes dos filtros do app)
const PAIRED = 6;            // parciais com duas "polarizações" (decaimento em 2 estágios)
const HF_DAMPING = .65;      // amortecimento extra por (kHz)² nos parciais agudos
const SILENCE = 1e-10;       // energia mínima de um modo (−100 dBFS)
const RAMP = 64;             // rampa de entrada (≈1,3 ms): evita clique quando os pulsos se sobrepõem
const TWO_PI = Math.PI * 2;

const clamp = (x, min, max) => Math.max(min, Math.min(max, x));
const frac = x => x - Math.floor(x);

export const hz = key => 440 * 2 ** ((key - 69) / 12);

// Coeficiente de inarmonicidade B: mínimo nas notas médias-graves, cresce nos agudos.
export function inharmonicity(key) {
  const B = 1.05e-4 * 2 ** ((key - 48) / 12 * 1.25) + 1.3e-4 * 2 ** ((45 - key) / 12 * .5);
  return clamp(B, 5e-5, .022);
}
export const partialHz = (f0, n, B) => n * f0 * Math.sqrt(1 + B * n * n);

// Tempo de decaimento (−60 dB) do fundamental, em segundos.
export const sustainSeconds = key => 24 * 2 ** (-(key - 21) * 2.5 / 87);

// Duração do contato martelo–corda (s). Pulso mais curto = mais brilho.
// Contato de Hertz com feltro (p≈3): T ∝ velocidade^−0,4 aproximadamente.
// Nunca passa de ~1 período da nota: acima disso o martelo "apagaria" o fundamental.
export function contactTime(key, speed, hardness) {
  const base = 1.25e-3 * 2 ** (-(key - 21) * 2 / 87);
  const felt = 1.5 - hardness * .9;
  return Math.min(1.2 / hz(key), base * felt * Math.max(.05, speed) ** -.4);
}

// Espectro complexo (P(0)=1) do pulso de força do martelo: função alfa t·e^(−t/τ), cuja
// transformada é 1/(1+jωτ)². Decai a −12 dB/oitava (como um piano real), não tem nulos
// espectrais (tocar mais forte = τ menor = SEMPRE mais brilhante) e já é causal:
// começa em zero, sem clique de ataque.
export function hammerSpectrum(f, T, out = [0, 0]) {
  const x = TWO_PI * f * .3 * T, q = (1 + x * x) ** 2;
  out[0] = (1 - x * x) / q; out[1] = -2 * x / q;
  return out;
}

class Voice {
  constructor() {
    this.re = new Float64Array(MAX_MODES); this.im = new Float64Array(MAX_MODES);
    this.cr = new Float64Array(MAX_MODES); this.ci = new Float64Array(MAX_MODES);
    this.tmp = new Float64Array(BLOCK);
    this.active = false; this.id = 0; this.count = 0; this.age = 0; this.released = false;
    this.gl = 1; this.gr = 1; this.send = 0; this.sendTarget = 0;
    this.noise = 0; this.key = 60; this.noiseDecay = 0; this.noiseLow = 0; this.fade = RAMP;
  }
}

export class PianoEngine {
  constructor(sampleRate) {
    this.sr = sampleRate;
    this.voices = Array.from({ length: MAX_VOICES }, () => new Voice());
    this.maxPartials = 28;
    this.done = [];           // ids de vozes que terminaram (lidos pelo processador)
    this.seed = 0x9e3779b9;
    this.pulse = [0, 0];      // área de trabalho (evita alocação em noteOn)
  }
  random() {                  // xorshift32 em [-1, 1)
    let s = this.seed; s ^= s << 13; s ^= s >>> 17; s ^= s << 5; this.seed = s;
    return (s >>> 0) / 2147483648 - 1;
  }
  find(id) { for (const v of this.voices) if (v.active && v.id === id) return v; return null }
  acquire() {
    let pick = null, best = -1;
    for (const v of this.voices) {
      if (!v.active) return v;
      const score = v.age + (v.released ? 1000 : 0);
      if (score > best) { best = score; pick = v }
    }
    this.done.push(pick.id);  // roubo de voz: avisa quem controlava a nota
    return pick;
  }
  addMode(v, m, f, sigma, re, im) {
    const r = Math.exp(-sigma / this.sr), theta = TWO_PI * f / this.sr;
    v.cr[m] = r * Math.cos(theta); v.ci[m] = r * Math.sin(theta);
    v.re[m] = re; v.im[m] = im;
    return m + 1;
  }
  // speed: velocidade do martelo normalizada (0–1). hardness: 0–1. send: envio à ressonância.
  noteOn({ id, key, speed = .7, hardness = .5, send = .12, character = 'japanese', decayScale = 1, brightness = .5 }) {
    key = clamp(Math.round(key), 0, 127);
    speed = clamp(speed, .001, 1); hardness = clamp(hardness, 0, 1);
    const profiles={japanese:{b:1.00,soft:1.00,t:1},american:{b:.82,soft:.89,t:1.12},felt:{b:.78,soft:.38,t:.84},upright:{b:1.32,soft:.90,t:.80}};
    const profile=profiles[character]||profiles.japanese;
    const sr = this.sr, f0 = hz(key), B = inharmonicity(key)*profile.b;
    const T = contactTime(key, speed, hardness)*(character==='felt'?2.0:1);
    const beta = .14 - .05 * clamp((key - 21) / 87, 0, 1);
    const sigma1 = 6.91 / (sustainSeconds(key)*profile.t*clamp(decayScale,.3,2));
    const limit = sr * .45;
    // Desafinação determinística das "cordas em uníssono" (gera batimentos).
    const spread = (.3 + .9 * frac(key * .618)) * (frac(key * .377) < .5 ? -1 : 1);
    const v = this.acquire();
    let m = 0, ref = 0; const P = this.pulse;
    for (let n = 1; n <= this.maxPartials && m < MAX_MODES - 1; n++) {
      const f = partialHz(f0, n, B);
      if (f >= limit) break;
      // Ao cavalete chegam dois pulsos: o direto (+) e o refletido na ponta da corda (−),
      // defasados de β·T0. O fator (1 − e^{−jφ}) dá o "pente" sin(nπβ) com a fase correta.
      hammerSpectrum(f, T, P);
      const phi = TWO_PI * f * beta / f0, kr = 1 - Math.cos(phi), ki = Math.sin(phi);
      const ar = P[0] * kr - P[1] * ki, ai = P[0] * ki + P[1] * kr;
      ref += ar * ar + ai * ai;
      const sigma = sigma1 + HF_DAMPING * (f / 1000) ** 2;
      if (n <= PAIRED) {
        m = this.addMode(v, m, f, sigma, ar * .65, ai * .65);
        m = this.addMode(v, m, f * 2 ** (spread * (1 + .15 * n) / 1200), sigma * .3, ar * .35, ai * .35);
      } else m = this.addMode(v, m, f, sigma, ar, ai);
    }
    // Leve reforço nos extremos do teclado (graves e agudíssimos soam mais baixos).
    const tilt = 1 + .5 * clamp((48 - key) / 27, 0, 1) + .8 * clamp((key - 96) / 12, 0, 1);
    // Normaliza o timbre desta nota e aplica a dinâmica (≈ 28 dB entre pp e ff).
    const scale = TARGET_RMS * speed ** 1.4 * tilt * profile.soft * (.75+.5*clamp(brightness,0,1)) / Math.sqrt(Math.max(1e-9, ref / 2));
    for (let i = 0; i < m; i++) { v.re[i] *= scale; v.im[i] *= scale }
    v.decayScale=clamp(decayScale,.3,2);v.key = key; v.count = m; v.id = id; v.active = true; v.released = false; v.age = 0; v.fade = 0;
    const angle = (clamp((key - 64.5) / 43.5, -1, 1) * .4 + 1) * Math.PI / 4;
    v.gl = Math.SQRT2 * Math.cos(angle); v.gr = Math.SQRT2 * Math.sin(angle);
    v.send = v.sendTarget = send;
    // "Toc" do martelo: só aparece em notas fortes e graves/médias.
    v.noise = TARGET_RMS * speed ** 2.5 * (.5 + hardness) * (character==='felt'?.18:.55) * clamp((96 - key) / 48, 0, 1);
    v.noiseDecay = Math.exp(-1 / (sr * .006)); v.noiseLow = 0;
  }
  // Solta a tecla: o abafador aumenta o amortecimento (mais nos parciais agudos).
  noteOff(id, fast = false, release = .4) {
    const v = this.find(id); if (!v) return;
    const T = fast ? .024 : Math.max(.02, release), sr = this.sr;
    for (let m = 0; m < v.count; m++) {
      const f = Math.atan2(v.ci[m], v.cr[m]) * sr / TWO_PI;
      const g = Math.exp(-(6.91 / T) * (1 + f / 1800) / sr);
      v.cr[m] *= g; v.ci[m] *= g;
    }
    v.released = true;
  }
  setSend(id, value) { const v = this.find(id); if (v) v.sendTarget = clamp(value,0,1) }
  // Retune decay coefficients of an already-ringing modal string without a re-strike.
  updateVoice(id,{decayScale}){
    const v=this.find(id);if(!v||v.released||!Number.isFinite(decayScale))return;
    const scale=clamp(decayScale,.3,2),ratio=v.decayScale/scale;
    for(let m=0;m<v.count;m++){
      const c=v.cr[m],s=v.ci[m],old=Math.hypot(c,s);
      if(old<=0)continue;
      const next=old**ratio,adjust=next/old;
      v.cr[m]=c*adjust;v.ci[m]=s*adjust;
    }
    v.decayScale=scale;
  }
  // Escreve o piano em L/R e o envio de ressonância (mono) em S.
  render(L, R, S, n) {
    n = Math.min(n, BLOCK);
    L.fill(0); if (R !== L) R.fill(0); if (S) S.fill(0);
    const mono = R === L;
    for (const v of this.voices) {
      if (!v.active) continue;
      const tmp = v.tmp; tmp.fill(0, 0, n);
      const { re, im, cr, ci } = v;
      for (let m = 0; m < v.count; m++) {
        let a = re[m], b = im[m]; const c = cr[m], s = ci[m];
        for (let i = 0; i < n; i++) { tmp[i] += a; const t = a * c - b * s; b = a * s + b * c; a = t }
        re[m] = a; im[m] = b;
      }
      if (v.noise > 1e-7) {
        let low = v.noiseLow, env = v.noise;
        for (let i = 0; i < n; i++) { low += .12 * (this.random() - low); tmp[i] += low * env; env *= v.noiseDecay }
        v.noiseLow = low; v.noise = env;
      }
      v.send += (v.sendTarget - v.send) * Math.min(1, n / 2400);
      if (v.fade < RAMP) {
        for (let i = 0; i < n && v.fade < RAMP; i++) tmp[i] *= .5 - .5 * Math.cos(Math.PI * v.fade++ / RAMP);
      }
      const gl = mono ? (v.gl + v.gr) / 2 : v.gl, gr = v.gr, gs = v.send;
      for (let i = 0; i < n; i++) {
        const y = tmp[i]; L[i] += y * gl;
        if (!mono) R[i] += y * gr;
        if (S) S[i] += y * gs;
      }
      this.prune(v, n);
    }
  }
  prune(v, n) {
    for (let m = 0; m < v.count;) {
      if (v.re[m] * v.re[m] + v.im[m] * v.im[m] < SILENCE) {
        const last = --v.count;
        v.re[m] = v.re[last]; v.im[m] = v.im[last]; v.cr[m] = v.cr[last]; v.ci[m] = v.ci[last];
      } else m++;
    }
    v.age += n / this.sr;
    if ((!v.count && v.noise <= 1e-7) || v.age > 90) { v.active = false; v.count = 0; this.done.push(v.id) }
  }
  stopAll() { for (const v of this.voices) if (v.active) this.noteOff(v.id, true) }
}

// Registro do processador (somente dentro do AudioWorkletGlobalScope).
if (typeof registerProcessor === 'function') {
  registerProcessor('palco-piano', class extends AudioWorkletProcessor {
    constructor() {
      super();
      this.engine = new PianoEngine(sampleRate);
      this.port.onmessage = ({ data: m }) => {
        if (m.type === 'on') this.engine.noteOn(m);
        else if (m.type === 'off') this.engine.noteOff(m.id, m.fast, m.release);
        else if (m.type === 'send') this.engine.setSend(m.id, m.value);
        else if (m.type === 'param') this.engine.updateVoice(m.id,m);
        else if (m.type === 'quality') this.engine.maxPartials = clamp(m.partials | 0, 8, 64);
        else if (m.type === 'stop') this.engine.stopAll();
      };
    }
    process(_inputs, outputs) {
      const [dry, aux] = outputs;
      this.engine.render(dry[0], dry[1] || dry[0], aux?.[0], dry[0].length);
      if (this.engine.done.length) this.port.postMessage({ type: 'done', ids: this.engine.done.splice(0) });
      return true;
    }
  });
}
