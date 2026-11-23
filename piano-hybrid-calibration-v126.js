/**
 * Stage D — effective radiated modal-spectral calibration, ORIGINAL Stage code.
 * 15 original Steinway B/Iowa AIFF recordings, C2..C6 x pp/mf/ff, verified
 * by original SHA256 against research/commercial_audio/iowa_steinway_b_verified_original_sha256.json
 * GitHub Actions 45115699255 (D v1.12.5 at nominal MIDI 32/80/120).
 * NO waveform, sample, third-party source code or directly measured physical
 * hammer/bridge parameters are included here.
 *
 * Two 8-bin dB spectra per anchor, both relative to the recorded/synth fundamental:
 * ref = mic/soundboard/room+strings observed at 18ms Hann-window;
 * old = uncalibrated Stage D v1.12.5 at nominal speeds and no FX.
 * pp/mf/ff -> 32/80/120 is NOT calibrated hammer velocity.
 * This is a bounded acoustic transfer correction, NOT a measured piano hammer law.
 * Source methodology: docs/DIAGNOSTICO_TIMBRE_D_IOWA_15_2026-11-23.md.
 */
export const SPECTRAL_SOURCE_RUN='45115699255';
export const HYBRID_CALIBRATION_STRENGTH=0.84;
const A=[
 {k:36,
  pp:{ref:[0,-.7,-2.9,-6.9,2,-3.5,-5.9,-10.8],old:[0,-4.8,-8.9,-15.1,-20.4,-27.5,-36.4,-60]},
  mf:{ref:[0,13.6,20.4,22.1,22.6,26.4,24.4,8.7],old:[0,-2.6,-6,-11.7,-16.5,-23.4,-32.1,-55.9]},
  ff:{ref:[0,12,19.1,22.7,21.7,26.2,25.6,11.8],old:[0,-1.6,-4.7,-10.1,-14.8,-21.5,-30.2,-54.8]}},
 {k:48,
  pp:{ref:[0,6,1.9,-1.8,-6.1,-13.1,-10.6,-8.3],old:[0,-8.4,-15,-20.9,-28.3,-34.6,-42.7,-56.2]},
  mf:{ref:[0,15.9,7.4,-2,4.7,.4,11.8,-8.4],old:[0,-5.6,-11.6,-17.2,-24.4,-30.6,-38.7,-52.1]},
  ff:{ref:[0,19.1,9.8,-.2,9.2,4,17.2,-2.3],old:[0,-4.3,-10,-15.3,-22.5,-28.6,-36.7,-50]}},
 {k:60,
  pp:{ref:[0,-4,-6.1,-9,-5.6,-15.2,-15.8,-16.4],old:[0,-12.3,-20.6,-27.2,-33,-41,-49,-59.5]},
  mf:{ref:[0,-10.3,-16.2,-20,-27.6,-20.1,-21.8,-35.8],old:[0,-9.8,-17.8,-24.3,-30.1,-38.1,-46,-56.5]},
  ff:{ref:[0,-5.4,-17.2,-16.8,-19.1,-17.4,-13.5,-20.7],old:[0,-8.5,-16.4,-22.8,-28.6,-36.5,-44.4,-54.9]}},
 {k:72,
  pp:{ref:[0,-5.2,-8.4,-14.3,-13.2,-15.3,-16.1,-14.5],old:[0,-13.3,-22,-29.1,-35.1,-41.8,-49.4,-59.1]},
  mf:{ref:[0,-20.5,-23.7,-37.5,-47.3,-63.6,-88.4,-91.9],old:[0,-11.8,-20.5,-27.6,-33.6,-40.4,-47.9,-57.6]},
  ff:{ref:[0,-19.6,-11.8,-19.1,-28.8,-40.9,-66.3,-65.8],old:[0,-11,-19.7,-26.8,-32.8,-39.5,-47.1,-56.8]}},
 {k:84,
  pp:{ref:[0,-10.3,-33.2,-45.1,-56.4,-53.4,-54.4,-57.1],old:[0,-14.9,-24.6,-30.7,-37.7,-46.6,-53.7,-63]},
  mf:{ref:[0,-26.2,-36,-51.4,-76.2,-80.4,-77.9,-81.9],old:[0,-13.4,-23.1,-29.2,-36.2,-45.1,-52.2,-61.6]},
  ff:{ref:[0,-25.7,-39.5,-49.7,-65.1,-85,-81.7,-90.2],old:[0,-12.6,-22.3,-28.4,-35.4,-44.3,-51.4,-60.7]}}
];
const VELOCITY=[32/127,80/127,120/127], LEVEL=['pp','mf','ff'];
const clamp=(x,a,b)=>Math.min(b,Math.max(a,x));
const smooth=t=>t*t*(3-2*t);
function anchorCorrection(source,partial){
  if(partial<=1)return 0;
  const index=partial-1;
  if(index>=8)return 0;
  const r=source.ref[index],b=source.old[index];
  if(!Number.isFinite(r)||!Number.isFinite(b))return 0;
  // Above 34dB below fundamental, spectral peaks are too weak to calibrate.
  // Only attenuate an existing audible excess to the conservative -34dB ceiling.
  if(r<=-34)return b>-34?clamp(-34-b,-30,0):0;
  return clamp(r-b,-36,68);
}
function correctionAt(anchor,levelIndex,partial){
  const source=anchor[LEVEL[levelIndex]];
  if(partial<=8)return anchorCorrection(source,partial);
  // We have no true source evidence for harmonics > 8. Gently taper the last
  // credible correction rather than extending an unmeasured spectral boost.
  if(partial>=14)return 0;
  const tail=anchorCorrection(source,8);
  return tail*clamp((14-partial)/6,0,1);
}
function betweenLevel(anchor,velocity,partial){
  const v=clamp(Number.isFinite(velocity)?velocity:VELOCITY[1],0,1);
  const low=v<=VELOCITY[1]?0:1,high=low+1;
  const t=smooth(clamp((v-VELOCITY[low])/(VELOCITY[high]-VELOCITY[low]),0,1));
  return correctionAt(anchor,low,partial)*(1-t)+correctionAt(anchor,high,partial)*t;
}
/** Bounded per-partial correction in dB at the modal excitation/radiation source. */
export function hybridRadiationCorrectionDb(key,speed,partial){
  if(!Number.isFinite(partial)||partial<=1)return 0;
  const n=Math.floor(partial);
  if(n>=14)return 0;
  const k=clamp(Number.isFinite(key)?key:60,21,108);
  let pos=0;
  while(pos<A.length-2&&k>A[pos+1].k)pos++;
  const low=A[pos],high=A[pos+1],t=smooth(clamp((k-low.k)/(high.k-low.k),0,1));
  const dB=betweenLevel(low,speed,n)*(1-t)+betweenLevel(high,speed,n)*t;
  const outside=k<36?(.65+.35*(k-21)/15):k>84?(.65+.35*(108-k)/24):1;
  return clamp(dB*HYBRID_CALIBRATION_STRENGTH*outside,-40,60);
}
/** Gain factor computed only on note-on; audio rendering never allocates here. */
export function hybridRadiationGain(key,speed,partial){
  return 10**(hybridRadiationCorrectionDb(key,speed,partial)/20);
}
