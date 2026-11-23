/**
 * Stage E3.0 — sample-free analytic radiator mesh convergence.
 *
 * Render the SAME deterministic hammer / strings / bridge / panel equations
 * with 8x6, 12x8, 16x12 surface quadrature. These are only spatial
 * integration refinements, NOT extra physical soundboard modes.
 * No piano recordings, SoundFonts, impulse responses, room simulation or FX.
 * Output remains relative/acoustically uncalibrated.
 */
import {renderAnalyticPhysicalPiano} from './pure-physical-radiation-e29.mjs';
import {makePurePhysicalScore} from './pure-physical-audition-e28.mjs';

export const RADIATION_MESHES_E30=Object.freeze([
 Object.freeze({columns:8,rows:6}),
 Object.freeze({columns:12,rows:8}),
 Object.freeze({columns:16,rows:12})
]);

function normError(a,b){
 let numerator=0,denominator=0;
 for(let i=0;i<a.left.length;i++){
  numerator+=(a.left[i]-b.left[i])**2+(a.right[i]-b.right[i])**2;
  denominator+=b.left[i]**2+b.right[i]**2;
 }
 if(!(denominator>0))throw new RangeError('silent reference mesh');
 return Math.sqrt(numerator/denominator);
}
export function comparePurePhysicalMeshes({
 sampleRate=48000,seconds=13,score=makePurePhysicalScore(),
 meshes=RADIATION_MESHES_E30
}={}){
 if(!Array.isArray(meshes)||meshes.length<2||meshes.length>3||
    meshes.some(m=>!m||!Number.isInteger(m.columns)||
     !Number.isInteger(m.rows)||m.columns*m.rows>256))
  throw new RangeError('expected 2..3 valid analytic quadrature meshes');
 const results=meshes.map(({columns,rows})=>
  renderAnalyticPhysicalPiano({sampleRate,seconds,score,
   radiation:{columns,rows}}));
 const reference=results[results.length-1],max={peak:0};
 for(const out of results)if(out.diagnostics.peakRelativePressure>max.peak)
  max.peak=out.diagnostics.peakRelativePressure;
 const relativeErrors=results.map((out,i)=>i===results.length-1?
  0:normError(out,reference));
 return {
  results,
  peak:max.peak,
  globalListeningGain:.82/max.peak,
  relativeErrors,
  labels:meshes.map(({columns,rows})=>columns+'x'+rows),
  diagnostics:{
   scoreEvents:reference.diagnostics.events,
   connectedKeys:88,stringCoordinates:reference.diagnostics.mechanicalStringCoordinates,
   boardCoordinates:2,
   patches:results.map(o=>o.diagnostics.platePatches),
   sampleFree:true,onlySurfaceQuadratureChanged:true,
   outputUnit:'relative pressure proxy, not calibrated Pa',
   humanPerceptualImprovementDemonstrated:false,
   validForProduction:false
  }
 };
}
export function encodeMeshStereoWav16(left,right,sampleRate,globalGain){
 if(!(left instanceof Float64Array||left instanceof Float32Array)||
    !(right instanceof Float64Array||right instanceof Float32Array)||
    left.length!==right.length||left.length<1||
    !Number.isInteger(sampleRate)||sampleRate<22050||sampleRate>96000||
    !Number.isFinite(globalGain)||globalGain<=0)
  throw new RangeError('invalid sample-free mesh WAV data');
 const len=left.length,out=Buffer.alloc(44+4*len);
 out.write('RIFF',0);out.writeUInt32LE(out.length-8,4);out.write('WAVE',8);
 out.write('fmt ',12);out.writeUInt32LE(16,16);out.writeUInt16LE(1,20);
 out.writeUInt16LE(2,22);out.writeUInt32LE(sampleRate,24);
 out.writeUInt32LE(sampleRate*4,28);out.writeUInt16LE(4,32);
 out.writeUInt16LE(16,34);out.write('data',36);out.writeUInt32LE(len*4,40);
 const fadeIn=Math.round(.006*sampleRate),fadeOut=Math.round(.18*sampleRate);
 for(let i=0;i<len;i++){
  const fade=Math.min(1,(i+1)/fadeIn,(len-i)/fadeOut);
  const l=left[i]*globalGain*fade,r=right[i]*globalGain*fade;
  if(!Number.isFinite(l)||!Number.isFinite(r)||
     Math.abs(l)>1||Math.abs(r)>1)throw new RangeError('invalid PCM amplitude');
  out.writeInt16LE(Math.round(l*32767),44+4*i);
  out.writeInt16LE(Math.round(r*32767),46+4*i);
 }
 return out;
}
