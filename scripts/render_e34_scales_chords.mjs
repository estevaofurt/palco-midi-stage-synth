#!/usr/bin/env node
/**
 * Stage E3.4: physical-only off-line SCALES, ARPEGGIOS and CHORDS demo.
 *
 * Only nonlinear reactive felt/hammer -> 88 string key network -> bridge ->
 * 16 distributed panel modes -> analytic Rayleigh air radiation.
 * No piano recordings, no SF2, no sampled transients, no impulse responses,
 * no post-hoc oscillators, no reverb and no PCM files READ into this generator.
 *
 * CAUTION: current E3.4 has ONE reactive hammer per physical instance. Chords
 * are therefore LINEAR MIXES OF SEPARATELY PHYSICALLY SYNTHESIZED NOTE VOICES.
 * The note waves were NOT copied from a piano recording and their pitch is NOT
 * resampled. Full multi-hammer nonlinear interaction on one shared board is
 * NOT solved by this demonstration. Auditory fidelity is NOT yet approved.
 */
import {writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {ReactiveFeltDistributedPianoE33}
 from '../research/reactive-felt-distributed-e33.mjs';
import {AnalyticSpatialPlateRadiatorE33}
 from '../research/analytic-spatial-plate-radiation-e33.mjs';

const SR=48000;
const voices=new Map();
const notes=[],sections=[];
let t=0;
function add(key,at,speed=1.75,duration=1.12,gate=.34,group=''){
 if(!Number.isInteger(key)||key<21||key>108||!Number.isFinite(at)||
    at<0||duration<=0||gate<=0||gate>=duration)
  throw new RangeError('invalid physical score note');
 notes.push({key,at,speed,duration,gate,group});
}
function scale(label,sequence,at,speed,spacing=.295){
 sections.push({label,start:at});
 sequence.forEach((key,i)=>add(key,at+i*spacing,speed,.79,.25,label));
 return at+sequence.length*spacing;
}
function arpeggio(label,sequence,at,speed,spacing=.235){
 sections.push({label,start:at});
 sequence.forEach((key,i)=>add(key,at+i*spacing,speed,1.12,.42,label));
 return at+sequence.length*spacing;
}
function chord(label,keys,at,speed=2.75){
 sections.push({label,start:at});
 keys.forEach((key,i)=>add(key,at+i*.012,speed,2.25,1.4,label));
 return at+2.44;
}
// As requested: both ascending and descending scales, arpeggios, and chords.
t=scale('Escala Do maior subindo e descendo',
 [48,50,52,53,55,57,59,60,59,57,55,53,52,50,48],.22,1.45);
t=scale('Escala Sol maior subindo e descendo',
 [55,57,59,60,62,64,66,67,66,64,62,60,59,57,55],t+.40,1.70);
t=arpeggio('Arpejo Do maior',
 [48,52,55,60,64,67,72,67,64,60,55,52],t+.52,1.95);
t=arpeggio('Arpejo La menor',
 [45,48,52,57,60,64,69,64,60,57,52,48],t+.32,1.85);
t=chord('Acorde Do maior',[48,52,55,60],t+.48,2.80);
t=chord('Acorde La menor',[45,48,52,57],t,2.55);
t=chord('Acorde Fa maior',[41,48,53,57],t,2.65);
t=chord('Acorde Sol7',[43,47,50,53],t,2.72);
t=chord('Acorde Do maior final',[48,55,60,64],t,2.95);
const totalSeconds=t+.45;
const count=Math.ceil(totalSeconds*SR);
const outLeft=new Float64Array(count),outRight=new Float64Array(count);
const cacheStats=[];
let energyMax=0,forcePeak=0;
async function physicalVoice({key,speed,duration,gate}){
 const cacheKey=[key,speed.toFixed(3),duration.toFixed(3),gate.toFixed(3)].join(':');
 if(voices.has(cacheKey))return voices.get(cacheKey);
 const physics=new ReactiveFeltDistributedPianoE33({
  sampleRate:SR,key,hammerVelocityMps:speed,
  panelModes:16,feltHardeningRatio:12,
  feltHardeningThresholdM:.00016,sustain:127
 });
 const radiator=new AnalyticSpatialPlateRadiatorE33({
  sampleRate:SR,shapes:physics.piano.panelShapes,columns:8,rows:6
 });
 const n=Math.ceil(duration*SR),left=new Float32Array(n),right=new Float32Array(n);
 const gateFrame=Math.round(gate*SR);
 const pedalFrame=Math.round(Math.min(duration-.12,gate+.22)*SR);
 for(let i=0;i<n;i++){
  if(i===gateFrame)physics.noteOff();
  if(i===pedalFrame)physics.setSustain(0);
  radiator.step(physics.step());
  left[i]=radiator.left;right[i]=radiator.right;
  if(!Number.isFinite(left[i])||!Number.isFinite(right[i]))
   throw new RangeError('nonfinite sample-free physical radiation');
 }
 const error=Math.abs(physics.relativeEnergyResidual());
 if(error>1e-7)throw new Error('nonpassive reactive hammer '+key+' '+error);
 forcePeak=Math.max(forcePeak,physics.peakForce);
 energyMax=Math.max(energyMax,error);
 const result={left,right,key,speed,duration,gate,energyError:error,
  peakContactForce:physics.peakForce};
 voices.set(cacheKey,result);
 cacheStats.push({key,speed,duration,gate,
  energyResidual:error,peakContactForce:physics.peakForce});
 return result;
}
for(const note of notes){
 const sound=await physicalVoice(note);
 const offset=Math.round(note.at*SR),len=sound.left.length;
 // Energy is introduced only in each physical single-hammer solve. Here the
 // air pressures of independently modeled voices superpose linearly.
 for(let i=0;i<len&&i+offset<count;i++){
  const fadeEnd=Math.min(1,(len-i)/(SR*.085));
  outLeft[offset+i]+=sound.left[i]*fadeEnd;
  outRight[offset+i]+=sound.right[i]*fadeEnd;
 }
}
let peak=0;
for(let i=0;i<count;i++)
 peak=Math.max(peak,Math.abs(outLeft[i]),Math.abs(outRight[i]));
if(!(peak>0))throw Error('empty modeled piano demo');
const gain=.78/peak;
function pcm16(begin,end){
 const n=end-begin,wav=Buffer.alloc(44+4*n);
 wav.write('RIFF',0);wav.writeUInt32LE(wav.length-8,4);
 wav.write('WAVE',8);wav.write('fmt ',12);
 wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);
 wav.writeUInt16LE(2,22);wav.writeUInt32LE(SR,24);
 wav.writeUInt32LE(SR*4,28);wav.writeUInt16LE(4,32);
 wav.writeUInt16LE(16,34);wav.write('data',36);
 wav.writeUInt32LE(4*n,40);
 for(let i=0;i<n;i++){
  const j=begin+i;
  const fade=Math.min(1,(i+1)/(SR*.002),(n-i)/(SR*.12));
  const l=outLeft[j]*gain*fade,r=outRight[j]*gain*fade;
  if(!Number.isFinite(l)||!Number.isFinite(r)||Math.abs(l)>1||Math.abs(r)>1)
   throw new RangeError('invalid PCM level');
  wav.writeInt16LE(Math.round(l*32767),44+i*4);
  wav.writeInt16LE(Math.round(r*32767),46+i*4);
 }
 return wav;
}
const scaleEnd=sections[2].start-.12;
const chordStart=sections.find(s=>s.label==='Acorde Do maior').start;
const intervals=[
 {file:'Stage_Synth_E34_Escalas_Arpejos_Acordes_Fisica_Pura.wav',start:0,end:totalSeconds},
 {file:'Stage_Synth_E34_Escalas_Fisica_Pura.wav',start:0,end:scaleEnd},
 {file:'Stage_Synth_E34_Acordes_Fisica_Pura.wav',start:chordStart-.12,end:totalSeconds}
];
const files=[];
for(const iv of intervals){
 const start=Math.floor(iv.start*SR),
  end=Math.min(count,Math.ceil(iv.end*SR));
 const wav=pcm16(start,end);
 await writeFile(iv.file,wav);
 files.push({file:iv.file,bytes:wav.length,
  sha256:createHash('sha256').update(wav).digest('hex'),
  seconds:(end-start)/SR});
}
const report={
 stage:'E3.4 physical-only scale, arpeggio and chord audition',
 format:'WAV PCM16 stereo 48kHz',
 noInputPcmSamples:true,noRecordedImpulseResponse:true,
 physics:'reactive nonlinear felt compression + 88 coupled strings + one local bridge + 16 spatial soundboard DOFs + causal Rayleigh air',
 chordApproximation:'sum of independently nonlinear physical-note instances: no common simultaneous hammer/board solve',
 noteCount:notes.length,distinctSimulatedNotes:voices.size,
 totalSeconds,sections,files,sharedGlobalGain:gain,
 maxContactForce:forcePeak,maxMechanicalRelativeEnergyError:energyMax,
 notes:notes.map(({key,at,speed,group})=>({key,at,speed,group})),
 perNoteEnergyDiagnostics:cacheStats,
 fidelityApproved:false,commercialReady:false,
 warning:'Physical equations not calibrated; no validated acoustic piano tone or 32-64 real-time simultaneous shared-board hammers.'
};
await writeFile('stage-e34-scales-chords-report.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({
 stage:report.stage,noteCount:notes.length,
 distinctSimulatedNotes:voices.size,totalSeconds,sections,files,
 maxContactForce:forcePeak,energyError:energyMax,
 sampleFree:true,chordsIndependentPhysicalVoices:true
},null,2));
