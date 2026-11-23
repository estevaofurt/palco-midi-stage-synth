#!/usr/bin/env node
/** Offline E3.0: three stereo WAVs from purely mathematical mechanics and air.
 * No samples, captured attacks, SF2, prerecorded IR or EQ. Research only.
 */
import {writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {comparePurePhysicalMeshes,encodeMeshStereoWav16}
 from '../research/compare-analytic-mesh-e30.mjs';

const rate=48000;
const results=comparePurePhysicalMeshes({sampleRate:rate,seconds:13});
const names=[
 'e30-physical-48-patches.wav',
 'e30-physical-96-patches.wav',
 'e30-physical-192-patches.wav'
];
const output=[];
for(let j=0;j<results.results.length;j++){
 const x=results.results[j];
 const wav=encodeMeshStereoWav16(x.left,x.right,rate,results.globalListeningGain);
 await writeFile(names[j],wav);
 output.push({
  name:names[j],bytes:wav.length,
  sha256:createHash('sha256').update(wav).digest('hex'),
  panels:results.diagnostics.patches[j]
 });
}
const report={
 method:'E2.3 88-key coupled passive mechanics + E2.9 Rayleigh',
 source:'100% calculated, no WAV input/no sample libraries/no impulse response',
 globalListeningGain:results.globalListeningGain,
 relativeL2To192:{
  mesh48:results.relativeErrors[0],mesh96:results.relativeErrors[1]
 },
 diagnostic:results.diagnostics,
 output,
 evidence:'numerical quadrature convergence only; NOT improved timbre or acoustic calibration'
};
await writeFile('e30-mesh-comparison.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
