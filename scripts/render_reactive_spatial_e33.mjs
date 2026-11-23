#!/usr/bin/env node
/** Stage E3.3 research audition: one reactive hammer per successive note,
 * physically shared 88-key bridge and 2/8 panel modes. Each note is rendered
 * from a fresh initial state to keep the single-hammer energy experiment
 * valid. This is NOT a 32-note/64-note live polyphonic piano.
 *
 * The sound is computed from nonlinear felt → strings → local bridge →
 * distributed surface coordinates → analytic Rayleigh radiation.
 * No recorded piano notes, sample attack, soundfonts, PCM input or IR.
 */
import {writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {ReactiveFeltDistributedPianoE33}
 from '../research/reactive-felt-distributed-e33.mjs';
import {AnalyticSpatialPlateRadiatorE33}
 from '../research/analytic-spatial-plate-radiation-e33.mjs';
import {encodeRelativeStereoWav16}
 from '../research/analytic-soundboard-radiation.mjs';

const sampleRate=48000,notes=[48,52,55,60];
const length=Math.round(.95*sampleRate);
const outputs=[],rawResults=[];
for(const panelModes of [2,8]){
 const left=new Float64Array(length*notes.length);
 const right=new Float64Array(left.length);
 const diagnostics=[];
 for(let index=0;index<notes.length;index++){
  const key=notes[index];
  const m=new ReactiveFeltDistributedPianoE33({
   sampleRate,key,hammerVelocityMps:2,panelModes,sustain:127
  });
  const rad=new AnalyticSpatialPlateRadiatorE33({
   sampleRate,shapes:m.piano.panelShapes,columns:8,rows:6
  });
  for(let i=0;i<length;i++){
   if(i===Math.round(.6*sampleRate))m.noteOff();
   if(i===Math.round(.73*sampleRate))m.setSustain(0);
   const modeV=m.step();
   rad.step(modeV);
   left[index*length+i]=rad.left;
   right[index*length+i]=rad.right;
  }
  const error=m.relativeEnergyResidual();
  if(!(Math.abs(error)<1e-7))
   throw new Error('unbalanced physical energy: '+error);
  diagnostics.push({midi:key,peakForce:m.peakForce,
   contactDurationMs:m.contactSamples*1000/sampleRate,
   relativeEnergyError:error,
   emittedPlateModes:panelModes});
 }
 const rawPeak=Math.max(
  ...[left,right].map(arr=>arr.reduce((peak,x)=>Math.max(peak,Math.abs(x)),0)));
 const {wav,gain}=encodeRelativeStereoWav16(left,right,sampleRate);
 const file='e33-reactive-spatial-'+panelModes+'-plate-modes.wav';
 await writeFile(file,wav);
 outputs.push({
  file,bytes:wav.length,
  sha256:createHash('sha256').update(wav).digest('hex'),
  panelModes,rawPeak,globalGainForAudibility:gain,
  diagnostics
 });
 rawResults.push({left,right});
}
const report={
 stage:'E3.3 physical-only 88 string network plus reactive felt and 2/8 distributed plate modes',
 format:'48000 Hz stereo PCM16',seconds:notes.length*length/sampleRate,
 notes:['C3','E3','G3','C4'],sampleFree:true,
 physicallyCalibrated:false,audiblePianoTimbreApproved:false,
 mechanicalHammerPolyphony:1,
 acousticRadiation:'Rayleigh from actual distributed plate modes, not point bridge',
 note:'Sequential one-hammer, note-by-note initial-condition renders; separate normalized listening gains per model. No 88-key simultaneous reactive piano, no room or reverb.',
 outputs
};
await writeFile('e33-reactive-plate-audition.json',
 JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
