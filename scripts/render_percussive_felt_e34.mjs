#!/usr/bin/env node
/**
 * Stage E3.4: inspect a physically harder hammer attack.
 * 100% equations: moving felt/hammer ↔ modal strings ↔ local bridge ↔
 * spatial plate ↔ geometric Rayleigh air radiation. No PCM sample notes,
 * no recorded hammer click, noise layer, EQ, convolution IR or reverb.
 *
 * Two controlled A/B comparisons: SAME board with default vs opt-in
 * compression-dependent felt core, first with eight, then sixteen modes.
 * Each variation gets the SAME global gain across the whole experiment,
 * preserving relative attack amplitude (not loudness-matched).
 * Not approved as a realistic piano sound.
 */
import {writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {ReactiveFeltDistributedPianoE33}
 from '../research/reactive-felt-distributed-e33.mjs';
import {AnalyticSpatialPlateRadiatorE33}
 from '../research/analytic-spatial-plate-radiation-e33.mjs';

const rate=48000,slotSeconds=.83,frames=Math.round(slotSeconds*rate);
const notes=[
 {key:48,hammerMps:.7,label:'C3 soft'},
 {key:48,hammerMps:2.8,label:'C3 hard'},
 {key:60,hammerMps:.7,label:'C4 soft'},
 {key:60,hammerMps:2.8,label:'C4 hard'}
];
const configurations=[
 {panelModes:8,feltHardeningRatio:0,name:'e34_8mode_felt_normal'},
 {panelModes:8,feltHardeningRatio:12,name:'e34_8mode_felt_core'},
 {panelModes:16,feltHardeningRatio:0,name:'e34_16mode_felt_normal'},
 {panelModes:16,feltHardeningRatio:12,name:'e34_16mode_felt_core'}
];
function windowRms(data,start,end){
 let energy=0,n=0;
 for(let i=Math.round(start*rate);i<Math.round(end*rate);i++){
  const v=data[i];energy+=v*v;n++;
 }
 return Math.sqrt(energy/n);
}
function render(c){
 const left=new Float64Array(frames*notes.length);
 const right=new Float64Array(left.length);
 const details=[];
 for(let k=0;k<notes.length;k++){
  const n=notes[k];
  const piano=new ReactiveFeltDistributedPianoE33({
   sampleRate:rate,key:n.key,hammerVelocityMps:n.hammerMps,
   feltHardeningRatio:c.feltHardeningRatio,
   feltHardeningThresholdM:.00016,
   panelModes:c.panelModes,sustain:127
  });
  const radiation=new AnalyticSpatialPlateRadiatorE33({
   sampleRate:rate,shapes:piano.piano.panelShapes,columns:8,rows:6
  });
  let highPlateEnergy=0;
  for(let i=0;i<frames;i++){
   if(i===Math.round(.59*rate))piano.noteOff();
   if(i===Math.round(.70*rate))piano.setSustain(0);
   const velocity=piano.step();
   radiation.step(velocity);
   left[k*frames+i]=radiation.left;
   right[k*frames+i]=radiation.right;
   for(let j=8;j<velocity.length;j++)
    highPlateEnergy+=velocity[j]*velocity[j];
  }
  const error=piano.relativeEnergyResidual();
  if(!(Math.abs(error)<1e-7))throw new Error('contact energy mismatch: '+error);
  const l=left.subarray(k*frames,(k+1)*frames);
  const r=right.subarray(k*frames,(k+1)*frames);
  const attack=Math.hypot(windowRms(l,.008,.065),windowRms(r,.008,.065));
  const body=Math.hypot(windowRms(l,.14,.38),windowRms(r,.14,.38));
  details.push({
   ...n,peakContactForceGeneralized:piano.peakForce,
   totalContactMs:piano.contactSamples*1000/rate,
   contactEnergyError:error,
   extraPlateModeVelocityEnergy:highPlateEnergy,
   attackRmsRelative:attack,bodyRmsRelative:body,
   attackToBodyDb:20*Math.log10(attack/Math.max(body,1e-30))
  });
 }
 return {left,right,details};
}
function encode(left,right,gain,{slotFades=true}={}){
 if(left.length!==right.length||left.length<1||left.length>rate*25)
  throw new RangeError('invalid physical audition wave');
 const count=left.length,wav=Buffer.alloc(44+count*4);
 wav.write('RIFF',0);wav.writeUInt32LE(wav.length-8,4);
 wav.write('WAVE',8);wav.write('fmt ',12);
 wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);
 wav.writeUInt16LE(2,22);wav.writeUInt32LE(rate,24);
 wav.writeUInt32LE(rate*4,28);wav.writeUInt16LE(4,32);
 wav.writeUInt16LE(16,34);wav.write('data',36);
 wav.writeUInt32LE(count*4,40);
 const fadeIn=Math.round(.0015*rate),fadeOut=Math.round(.055*rate);
 for(let i=0;i<count;i++){
  const rel=slotFades?i%frames:i;
  const last=slotFades?frames-i%frames:count-i;
  const fade=Math.min(1,(rel+1)/fadeIn,last/fadeOut);
  const l=left[i]*gain*fade,r=right[i]*gain*fade;
  if(!Number.isFinite(l)||!Number.isFinite(r)||Math.abs(l)>1||Math.abs(r)>1)
   throw new RangeError('nonfinite or clipped mechanical radiation');
  wav.writeInt16LE(Math.round(32767*l),44+i*4);
  wav.writeInt16LE(Math.round(32767*r),46+i*4);
 }
 return wav;
}
const renders=configurations.map(render);
let globalPeak=0;
for(const data of renders)for(const stream of [data.left,data.right])
 for(const x of stream)globalPeak=Math.max(globalPeak,Math.abs(x));
if(!(globalPeak>0))throw new Error('physically silent audition');
const gain=.78/globalPeak,files=[];
for(let i=0;i<configurations.length;i++){
 const name=configurations[i].name+'.wav';
 const bytes=encode(renders[i].left,renders[i].right,gain);
 await writeFile(name,bytes);
 files.push({
  name,sizeBytes:bytes.length,
  sha256:createHash('sha256').update(bytes).digest('hex'),
  configuration:configurations[i],notes:renders[i].details
 });
}
const pauseFrames=Math.round(.27*rate);
for(const pair of [[0,1],[2,3]]){
 const framesTotal=renders[pair[0]].left.length*2+pauseFrames;
 const l=new Float64Array(framesTotal),rr=new Float64Array(framesTotal);
 const first=renders[pair[0]],second=renders[pair[1]];
 const offset=first.left.length+pauseFrames;
 // The AB WAV must not add sharp EDIT boundaries that could be mistaken
 // for hammer percussion. The same short boundary fade is applied to BOTH.
 const fadeIn=Math.round(.0015*rate),fadeOut=Math.round(.055*rate);
 for(let i=0;i<first.left.length;i++){
  const phase=i%frames;
  const fade=Math.min(1,(phase+1)/fadeIn,(frames-phase)/fadeOut);
  l[i]=first.left[i]*fade;rr[i]=first.right[i]*fade;
  l[offset+i]=second.left[i]*fade;rr[offset+i]=second.right[i]*fade;
 }
 const name='e34_AB_'+configurations[pair[0]].panelModes+
   'panel_normal_then_compressed_felt.wav';
 const bytes=encode(l,rr,gain,{slotFades:false});
 await writeFile(name,bytes);
 files.push({name,sizeBytes:bytes.length,
  sha256:createHash('sha256').update(bytes).digest('hex'),
  description:'Baseline followed by harder felt; common GAIN, not equal-loudness'});
}
const report={
 stage:'E3.4 compression-hardening felt + 8/16 spatial soundboard modes',
 source:'100% analytical physics: no sampled piano or percussive noise track',
 note:'8/16 are plate DOF counts, NOT radiation patch counts',
 noteSequence:notes,slotSeconds,
 commonGain:gain,globalPeak,files,
 limitations:[
  'SINGLE reactive hammer per sequential note; NOT simultaneous piano notes',
  'Uncalibrated felt, bridge, 88 string masses and panel modes',
  '12x felt-core strength and 0.16mm threshold are illustrative, not measured',
  'Relative stereo air pressure only; no acoustic Pa/SPL calibration',
  'Variation changes actual physical impact but piano realism not proven',
  '88-key MIDI live polyphony, browser CPU and subjective audition NOT validated'
 ]
};
await writeFile('e34_percussive_hammer_report.json',
 JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({
 ...report,files:files.map(({name,sizeBytes,sha256,...rest})=>({
  name,sizeBytes,sha256,...(rest.configuration?{configuration:rest.configuration,
   notes:rest.notes}:rest)
 }))
},null,2));
