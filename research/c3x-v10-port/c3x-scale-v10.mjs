/**
 * Tradução de pesquisa de stage_synth_c3x/parameters.py da V10.
 * Não se trata de dados medidos do Yamaha C3X: todas as dimensões internas,
 * propriedades da corda e martelo são ESTIMATIVAS para experimentação.
 * Somente preparação não-real-time: executar antes do callback de áudio.
 */
const E_STEEL_PA = 200e9;
const NOTE_NAMES = Object.freeze(['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']);

function interpolate(midi, points) {
  const pairs = Object.entries(points).map(([x, y])=>[Number(x),Number(y)]).sort((a,b)=>a[0]-b[0]);
  if (midi <= pairs[0][0]) return pairs[0][1];
  for (let i=1; i<pairs.length; i++) {
    const [x2,y2] = pairs[i];
    if (midi<=x2) {
      const [x1,y1] = pairs[i-1];
      return y1+(midi-x1)/(x2-x1)*(y2-y1);
    }
  }
  return pairs[pairs.length-1][1];
}

function logInterpolate(midi, points) {
  const mapped = {};
  for (const key of Object.keys(points)) mapped[key] = Math.log(points[key]);
  return Math.exp(interpolate(midi,mapped));
}

export function noteParamsV10(midi) {
  if (!Number.isInteger(midi) || midi<21 || midi>108) throw new RangeError('MIDI permitido: 21 a 108');
  const f = 440 * Math.pow(2, (midi-69)/12);
  let L;
  if (midi<=46) L=logInterpolate(midi,{21:1.36,33:1.10,45:0.86,46:0.83});
  else if (midi<=49) L=logInterpolate(midi,{47:1.03,49:0.985});
  else L=logInterpolate(midi,{50:0.963,57:0.620,60:0.545,69:0.399,81:0.208,93:0.105,108:0.050});
  const T=interpolate(midi,{21:1300,32:1050,46:675,47:790,49:760,50:720,69:687,81:672,108:650});
  const d=interpolate(midi,{21:1.5,33:1.18,46:0.95,47:0.98,49:0.97,50:1.125,69:0.95,81:0.9,108:0.78});
  const mu=T/(4*L*L*f*f);
  const B=Math.PI**3*E_STEEL_PA*(d/1000)**4/(64*T*L*L);
  const m=interpolate(midi,{21:0.014,45:0.012,69:0.009,108:0.005});
  const K=logInterpolate(midi,{21:7e8,49:1.5e10,69:2e10,108:3e11});
  const p=interpolate(midi,{21:2.2,69:2.8,108:3.5});
  const x=interpolate(midi,{21:0.14,69:0.125,108:0.105});
  const nstrings=midi<=32?1:midi<=49?2:3;
  return {
    midi, note:`${NOTE_NAMES[midi%12]}${Math.floor(midi/12)-1}`,
    frequencyHz:f, strings:nstrings, wound:midi<=49,
    lengthM:L, tensionN:T, diameterMm:d, densityKgM:mu,
    inharmonicityB:B, hammerMassKg:m, feltK:K, feltP:p,
    impactPosition:x,
    origin:'estimativa inicial; NAO medida do Yamaha C3X',
  };
}

/** Equação de corda rígida da V10, com fundamental preservada. */
export function modeFrequencyHz(p, partial) {
  if (!Number.isInteger(partial) || partial < 1) throw new RangeError('partial inválido');
  const B = p.inharmonicityB;
  return p.frequencyHz * partial * Math.sqrt((1 + B*partial*partial)/(1+B));
}