#!/usr/bin/env node
/**
 * E3.4 user-rejected timbre: matched E3.3-vs-E3.4 CONTROL audition.
 * Both render the exact same four note/velocity conditions from mechanical
 * hammer/felt/strings/bridge/plate equations, no sampled attacks, IR or PCM
 * imports. Same microphone geometry and one gain across BOTH candidates.
 *
 * E3.3 = 8 real plate DOFs, default nonlinear felt (hardening ratio 0).
 * E3.4 = 16 real plate DOFs, hypothetical hard core ratio 12.
 *
 * User explicitly heard E3.4 as FURTHER from acoustic piano; this audition
 * is diagnostic ONLY, never proof that E3.3 was a realistic piano.
 * Same limitation: each note is physically integrated independently,
 * no multi-hammer shared-board solver.
 */
import {writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {ReactiveFeltDistributedPianoE33}
 from '../research/reactive-felt-distributed-e33.mjs';
import {AnalyticSpatialPlateRadiatorE33}
 from '../research/analytic-spatial-plate-radiation-e33.mjs';

const SR=48000,LENGTH=.8,FRAMES=Math.round(LENGTH*SR);
const scenarios=[
 {key:48,speed:.7,label:'C3 suave'},
 {key:48,speed:2.8,label:'C3 forte'},
 {key:60,speed:.7,label:'C4 suave'},
 {key:60,speed:2.8,label:'C4 forte'}
];
const configs=[
 {name:'E33_baseline',panelModes:8,feltHardeningRatio:0},
 {name:'E34_rejected',panelModes:16,feltHardeningRatio:12}
];
function rms(x,start,end){
 let energy=0,frames=0;
 for(let i=Math.round(start*SR);i<Math.round(end*SR);i++){
  energy+=x[i]*x[i];frames++;
 }
 return Math.sqrt(energy/frames);
}
function goertzelMagnitude(x,start,length,frequency){
 const angle=2*Math.PI*frequency/SR,coeff=2*Math.cos(angle);
 let a=0,b=0;
 for(let n=0;n<length;n++){
  const pos=start+n,value=x[pos]*(.5-.5*Math.cos(2*Math.PI*n/(length-1)));
  const next=value+coeff*a-b;
  b=a;a=next;
 }
 return Math.sqrt(Math.max(0,a*a+b*b-coeff*a*b));
}
function spectrum(x,root){
 const start=Math.round(.024*SR),count=Math.round(.18*SR);
 const magnitudes=[];
 for(let k=1;k<=8;k++){
  const f=root*k;
  let max=0;
  for(const detune of [-2.5,0,2.5]){
   max=Math.max(max,goertzelMagnitude(x,start,count,f+detune));
  }
  magnitudes.push(max);
 }
 return magnitudes.map((v,i)=>i===0?0:
  +(20*Math.log10(Math.max(v,1e-16)/Math.max(magnitudes[0],1e-16))).toFixed(2));
}
function render(cfg){
 const outputL=new Float64Array(FRAMES*scenarios.length);
 const outputR=new Float64Array(outputL.length);
 const report=[];
 for(let s=0;s<scenarios.length;s++){
  const spec=scenarios[s];
  const piano=new ReactiveFeltDistributedPianoE33({
   sampleRate:SR,key:spec.key,hammerVelocityMps:spec.speed,
   panelModes:cfg.panelModes,feltHardeningRatio:cfg.feltHardeningRatio,
   sustain:127
  });
  const radiator=new AnalyticSpatialPlateRadiatorE33({
   sampleRate:SR,shapes:piano.piano.panelShapes,columns:8,rows:6
  });
  const mono=new Float64Array(FRAMES);
  let patchHighVelocityEnergy=0;
  for(let i=0;i<FRAMES;i++){
   if(i===Math.round(.55*SR))piano.noteOff();
   if(i===Math.round(.68*SR))piano.setSustain(0);
   const modeV=piano.step();
   for(let k=8;k<modeV.length;k++)patchHighVelocityEnergy+=modeV[k]*modeV[k];
   radiator.step(modeV);
   outputL[s*FRAMES+i]=radiator.left;
   outputR[s*FRAMES+i]=radiator.right;
   mono[i]=.5*(radiator.left+radiator.right);
  }
  if(Math.abs(piano.relativeEnergyResidual())>1e-7)
   throw new Error('E3.3/E3.4 energy conservation regression');
  const attack=rms(mono,.01,.065),body=rms(mono,.14,.38);
  const root=440*2**((spec.key-69)/12);
  report.push({
   ...spec,
   contactPeakGeneralized:piano.peakForce,
   contactDurationMs:piano.contactSamples/SR*1000,
   attackToBodyDb:+(20*Math.log10(attack/Math.max(body,1e-30))).toFixed(3),
   harmonicLevelsDb:spectrum(mono,root),
   higherPlateModeVelocityEnergy:patchHighVelocityEnergy,
   mechanicalBalanceRelativeError:piano.relativeEnergyResidual()
  });
 }
 return {outputL,outputR,report};
}
const renders=configs.map(render);
let peak=0;
for(const render of renders)
 for(const out of [render.outputL,render.outputR])
  for(const v of out)peak=Math.max(peak,Math.abs(v));
if(!(peak>0))throw new Error('silence');
const gain=.77/peak;
const gapSamples=Math.round(.35*SR);
const n=renders[0].outputL.length,frames=2*n+gapSamples;
const l=new Float64Array(frames),rr=new Float64Array(frames);
const fadeIn=Math.round(.002*SR),fadeOut=Math.round(.06*SR);
for(let j=0;j<renders.length;j++){
 const render=renders[j],offset=j*(n+gapSamples);
 for(let i=0;i<n;i++){
  const within=i%FRAMES;
  const fade=Math.min(1,(within+1)/fadeIn,(FRAMES-within)/fadeOut);
  l[offset+i]=render.outputL[i]*fade;
  rr[offset+i]=render.outputR[i]*fade;
 }
}
function wav16(left,right){
 const bytes=Buffer.alloc(44+4*left.length);
 bytes.write('RIFF',0);bytes.writeUInt32LE(bytes.length-8,4);
 bytes.write('WAVE',8);bytes.write('fmt ',12);bytes.writeUInt32LE(16,16);
 bytes.writeUInt16LE(1,20);bytes.writeUInt16LE(2,22);
 bytes.writeUInt32LE(SR,24);bytes.writeUInt32LE(SR*4,28);
 bytes.writeUInt16LE(4,32);bytes.writeUInt16LE(16,34);
 bytes.write('data',36);bytes.writeUInt32LE(left.length*4,40);
 for(let i=0;i<left.length;i++){
  const vl=left[i]*gain,vr=right[i]*gain;
  if(!Number.isFinite(vl)||!Number.isFinite(vr)||Math.abs(vl)>1||Math.abs(vr)>1)
   throw new Error('nonfinite or clipped PCM output');
  bytes.writeInt16LE(Math.round(vl*32767),44+4*i);
  bytes.writeInt16LE(Math.round(vr*32767),46+4*i);
 }
 return bytes;
}
const outputs=[];
const variants=[
 {name:'Stage_Synth_E33_Comparacao_Controlada.wav',left:renders[0].outputL,right:renders[0].outputR},
 {name:'Stage_Synth_E34_Rejeitado_Comparacao_Controlada.wav',left:renders[1].outputL,right:renders[1].outputR},
 {name:'Stage_Synth_AB_E33_vs_E34_Rejeitado.wav',left:l,right:rr}
];
for(const item of variants){
 const wav=wav16(item.left,item.right);
 await writeFile(item.name,wav);
 outputs.push({file:item.name,bytes:wav.length,
  sha256:createHash('sha256').update(wav).digest('hex'),
  durationSeconds:item.left.length/SR});
}
const report={
 title:'E3.4 rejected by user; E3.3-vs-E3.4 identical-input A/B',
 status:'E3.4 REJECTED — more distant from piano, according to user',
 note:'Harmonic diagnostics are relative; no conclusion on perceived realism from calculations alone.',
 source:'100% modelagem fisica. no samples, no recorded impulse response, no post-hoc click.',
 scenarios,configs,sameGlobalGain:gain,outputs,metrics:renders.map((r,i)=>({
  model:configs[i].name,perNote:r.report
 })),
 remainingProblems:[
  'Both models use physically UNCALIBRATED string/bridge/plate parameters',
  'E3.3 was not previously approved as realistic piano either',
  'E3.4 high-frequency panel frequencies were illustrative',
  'Chords of prior demo mixed independently rendered hammer instances',
  'No true shared-soundboard multi-hammer piano or hardware verification'
 ]
};
await writeFile('e34_rejection_e33_match_report.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,files:outputs,
 metrics:report.metrics},null,2));
