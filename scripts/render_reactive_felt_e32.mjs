#!/usr/bin/env node
/** Reproducible 100%-physical E3.2 listening reference.
 * Same reactive felt/strings/bridge as E3.2 code, surface-only radiation:
 * deliberately never radiates the local bridge as a large-area panel.
 * 4 notes rendered one at a time with fresh 88-key shared modal network;
 * NOT simultaneously reactive polyphony, not calibrated real piano.
 * ZERO input recordings, recorded IR, samples, soundfonts or room effects.
 */
import {writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {ReactiveFeltModalPiano} from '../research/reactive-felt-modal-piano-e32.mjs';
import {AnalyticSoundboardRadiator,encodeRelativeStereoWav16}
 from '../research/analytic-soundboard-radiation.mjs';

const sampleRate=48000,notes=[48,52,55,60];
const framesPerNote=Math.round(1.35*sampleRate),output=[];
for(const geometry of [null,{lengthM:.85,radiusM:.0006,densityKgM3:7850}]){
 const left=new Float64Array(framesPerNote*notes.length);
 const right=new Float64Array(left.length);
 const diagnostics=[];
 for(let k=0;k<notes.length;k++){
  const midiRoot=notes[k];
  const piano=new ReactiveFeltModalPiano({
   sampleRate,key:midiRoot,velocityMps:2,
   stringGeometry:geometry,partialsBass:5,partialsTreble:2,sustain:127
  });
  const surface=new AnalyticSoundboardRadiator({
   sampleRate,columns:8,rows:6
  });
  for(let i=0;i<framesPerNote;i++){
   if(i===Math.round(.57*sampleRate))piano.noteOff();
   piano.step();
   // The second passive mode represents a surface coordinate; bridge local
   // velocity is NOT mapped to a large-area radiator.
   surface.step(piano.piano.boardPanelVelocity,0);
   left[k*framesPerNote+i]=surface.left;
   right[k*framesPerNote+i]=surface.right;
  }
  const residual=piano.balanceRelativeError();
  if(!Number.isFinite(residual)||Math.abs(residual)>1e-7)
   throw new RangeError('energy balance failed for isolated reactive note');
  diagnostics.push({
   midiRoot,peakForce:piano.maxForce,
   contactSamples:piano.contactSamples,relativeEnergyResidual:residual
  });
 }
 const {wav,gain,peakRelativePressure}=encodeRelativeStereoWav16(left,right,sampleRate);
 const file=geometry===null?'e32-reactive-old-mass-physical.wav':
  'e32-reactive-geometry-mass-physical.wav';
 await writeFile(file,wav);
 output.push({
  file,bytes:wav.length,sha256:createHash('sha256').update(wav).digest('hex'),
  massSource:geometry===null?'legacy uncalibrated':'idealized 0.85m steel string',
  perVersionListeningGain:gain,rawRelativePeak:peakRelativePressure,
  noteDurationSeconds:1.35,notes:['C3','E3','G3','C4'],
  physicallyMeasuredParameters:false,
  diagnostics
 });
}
const report={
 stage:'E3.2 standalone sequential reactive felt + shared 88-key modes',
 format:'PCM16 stereo 48 kHz 5.4 seconds per candidate',
 sampleFree:true,acousticallyCalibrated:false,perceptualPianoApproval:false,
 simultaneousReactiveHammers:1,
 soundOutput:'analytic Rayleigh from E2.3 panel coordinate, NOT point bridge',
 output
};
await writeFile('e32-listening-audit.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
