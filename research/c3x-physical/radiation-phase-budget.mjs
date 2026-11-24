// F1.6 — offline acquisition planning, not synth DSP. All input uncertainties are nonnegative absolute bounds, not fitted piano values.
// Timing terms must be distinct residual bounds, measured independently after correction; do not include propagation delay in clock offset.
// Path uncertainty is only for geometric prediction, not H1 measured at a fixed microphone.
export function auditPhaseBudget(input) {
  if (!input || typeof input !== 'object') throw new TypeError('input required');
  const positive = ['frequencyHz','sampleRateHz','speedOfSoundMps','maxPhaseErrorDeg'];
  const nonnegative = ['elapsedSeconds','residualOffsetUs','relativeClockDriftPpm','relativeChannelDelayUs','pathLengthUncertaintyM'];
  for (const name of positive) if (!Number.isFinite(input[name]) || input[name] <= 0) throw new RangeError(name);
  for (const name of nonnegative) if (!Number.isFinite(input[name]) || input[name] < 0) throw new RangeError(name);
  if (input.frequencyHz >= input.sampleRateHz/2 || input.maxPhaseErrorDeg >= 180) throw new RangeError('frequency must be below Nyquist; tolerance below 180 deg');
  const maxTimeUs = input.maxPhaseErrorDeg / (360 * input.frequencyHz) * 1e6;
  const driftUs = input.relativeClockDriftPpm * input.elapsedSeconds;
  const timingUs = input.residualOffsetUs + driftUs + input.relativeChannelDelayUs;
  const geometryUs = input.pathLengthUncertaintyM / input.speedOfSoundMps * 1e6;
  const phase = us => 360 * input.frequencyHz * us / 1e6;
  const measuredPhaseDeg = phase(timingUs);
  const predictionPhaseDeg = phase(timingUs + geometryUs);
  if (![maxTimeUs, driftUs, timingUs, geometryUs, measuredPhaseDeg, predictionPhaseDeg].every(Number.isFinite)) throw new RangeError('numeric overflow');
  return {frequencyHz: input.frequencyHz, maxTimeUs, samplePeriodUs: 1e6/input.sampleRateHz,
    oneSamplePhaseDeg:360*input.frequencyHz/input.sampleRateHz, driftUs, timingUs, geometryUs,
    measuredPhaseDeg, predictionPhaseDeg, measuredWithinBudget: timingUs <= maxTimeUs,
    predictionWithinBudget: timingUs + geometryUs <= maxTimeUs,
    remainingPathUncertaintyM: Math.max(0, (maxTimeUs-timingUs)*1e-6*input.speedOfSoundMps),
    scope:'synthetic uncertainty bound; neither sensor evidence nor F1/F7 acceptance'};
}
