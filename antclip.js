// Estágio final de proteção: headroom seguido de saturação suave e limitada.
// A curva evita clipping digital mesmo quando vários módulos e retornos FX somam picos.
export const HEADROOM = 0.72;
export const CEILING = 0.94;
export function softClipCurve(ceiling = CEILING, size = 4097) {
  const curve = new Float32Array(size);
  for (let i = 0; i < size; i++) {
    const x = (i / (size - 1)) * 2 - 1;
    curve[i] = ceiling * Math.tanh(x / ceiling);
  }
  return curve;
}
export function installOutputProtection(ctx, upstream, destination = ctx.destination) {
  const trim = ctx.createGain();
  trim.gain.value = HEADROOM;
  const limiter = ctx.createWaveShaper();
  limiter.curve = softClipCurve();
  // O oversampling suaviza os harmônicos gerados pelo limitador.
  limiter.oversample = '2x';
  upstream.connect(trim).connect(limiter).connect(destination);
  return { trim, limiter };
}
