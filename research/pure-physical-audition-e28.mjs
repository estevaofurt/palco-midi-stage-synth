/**
 * E2.8 - SAMPLE-FREE, OFFLINE, physically coupled piano audition.
 *
 * All vibration originates in a normalized hammer force delivered to the
 * passive multi-mode string bank, 88 permanently connected keys and shared
 * 2DOF bridge/soundboard (E2.3). No recorded piano, PCM attack, soundfont,
 * convolution IR, oscillator mixed after the bridge, room reverb or FX.
 *
 * IMPORTANT: output is normalized GENERALIZED BOARD VELOCITY (not measured
 * air pressure). WAV normalization only makes this mechanical proxy audible;
 * it is NOT a calibrated piano recording or an integrated Stage-D model.
 */
import {SharedPassiveModalPiano} from './shared-passive-modal-piano.mjs';

const RATE=48000;
const note=(seconds,key,velocity=85,hold=.45)=>
 [{seconds,type:'on',key,velocity},
  {seconds:seconds+hold,type:'off',key}];

export function makePurePhysicalScore(){
 const result=[
  {seconds:0,type:'pedal',cc:127},
  {seconds:4.23,type:'pedal',cc:0},
  {seconds:4.40,type:'pedal',cc:127},
  {seconds:8.87,type:'pedal',cc:0},
  {seconds:9.05,type:'pedal',cc:127},
  {seconds:11.55,type:'pedal',cc:0}
 ];
 const sequences=[
  {start:.18,notes:[48,52,55,60,64,67,72],velocity:82,spacing:.285},
  {start:2.34,notes:[45,48,52,57,60,64,69],velocity:88,spacing:.285},
  {start:4.65,notes:[41,48,53,57,60,65],velocity:95,spacing:.008},
  {start:6.79,notes:[43,50,55,59,62,65],velocity:97,spacing:.008},
  {start:9.25,notes:[48,55,60,64,67,72],velocity:92,spacing:.008}
 ];
 for(const seq of sequences)
  for(let i=0;i<seq.notes.length;i++)
   result.push(...note(seq.start+i*seq.spacing,seq.notes[i],
      seq.velocity-i%3*4,seq.spacing<.1?1.45:.57));
 result.sort((a,b)=>a.seconds-b.seconds||
  (a.type==='pedal'?0:a.type==='off'?1:2)-
  (b.type==='pedal'?0:b.type==='off'?1:2));
 return result;
}
export function renderPurePhysicalMechanical({
 sampleRate=RATE,seconds=13,
 partialsBass=5,partialsTreble=2,force=105,score=makePurePhysicalScore()
}={}){
 if(!Number.isInteger(sampleRate)||sampleRate<22050||sampleRate>96000||
    !Number.isFinite(seconds)||seconds<.4||seconds>30||
    !Number.isFinite(force)||force<=0||force>1e5||
    !Array.isArray(score)||score.length>512)
  throw new RangeError('invalid physical research audition configuration');
 const piano=new SharedPassiveModalPiano({sampleRate,partialsBass,partialsTreble});
 const frames=Math.floor(seconds*sampleRate);
 const output=new Float64Array(frames);
 const events=score.map((e,i)=>{
  if(!e||!Number.isFinite(e.seconds)||e.seconds<0||e.seconds>=seconds||
      !['on','off','pedal'].includes(e.type)||
      (e.type==='pedal'&&(!Number.isFinite(e.cc)||e.cc<0||e.cc>127))||
      (e.type!=='pedal'&&(!Number.isInteger(e.key)||e.key<21||e.key>108))||
      (e.type==='on'&&(!Number.isFinite(e.velocity)||e.velocity<1||e.velocity>127)))
   throw new RangeError('invalid physical score event');
  return {...e,at:Math.round(e.seconds*sampleRate),order:i};
 }).sort((a,b)=>a.at-b.at||a.order-b.order);
 let at=0,max=0;
 for(let frame=0;frame<frames;frame++){
  while(at<events.length&&events[at].at===frame){
   const event=events[at++];
   if(event.type==='pedal')piano.setSustain(event.cc);
   else if(event.type==='off')piano.noteOff(event.key);
   else piano.noteOn(event.key,{velocity:event.velocity,peakForce:force,contactMs:3});
  }
  const value=piano.step();
  if(!Number.isFinite(value))throw new RangeError('nonfinite mechanical output');
  output[frame]=value;
  max=Math.max(max,Math.abs(value));
 }
 if(!(max>0))throw new RangeError('silent mechanical render');
 const rel=Math.abs(piano.energyBalanceError())/Math.max(1,piano.externalWork);
 if(!(rel<1e-7))throw new RangeError('nonpassive work-energy balance');
 return {
  signal:output,peakMechanical:max,
  diagnostics:{
   sampleRate,seconds,partialsBass,partialsTreble,
   connectedKeys:88,mechanicalStringCoordinates:piano.n,
   sharedBoardCoordinates:2,events:events.length,
   energy:piano.energy(),work:piano.externalWork,
   dissipated:piano.dissipated,balanceRelativeError:rel,
   source:'E2.3 normalized hammer/strings/bridge; zero PCM samples',
   outputUnit:'uncalibrated generalized board velocity; NOT Pa',
   acousticRealismVerified:false
  }
 };
}
export function encodeNormalizedMechanicalWav16(input,sampleRate=RATE){
 if(!(input instanceof Float32Array||input instanceof Float64Array)||
    input.length<1||input.length>sampleRate*30||
    !Number.isInteger(sampleRate)||sampleRate<22050||sampleRate>96000)
  throw new RangeError('invalid offline mono WAV parameters');
 let peak=0;
 for(const x of input){
  if(!Number.isFinite(x))throw new TypeError('nonfinite mechanical signal');
  peak=Math.max(peak,Math.abs(x));
 }
 if(!(peak>0))throw new RangeError('cannot write silent mechanical WAV');
 const wav=Buffer.alloc(44+input.length*2);
 wav.write('RIFF',0);wav.writeUInt32LE(wav.length-8,4);
 wav.write('WAVE',8);wav.write('fmt ',12);
 wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);
 wav.writeUInt16LE(1,22);wav.writeUInt32LE(sampleRate,24);
 wav.writeUInt32LE(sampleRate*2,28);wav.writeUInt16LE(2,32);
 wav.writeUInt16LE(16,34);wav.write('data',36);
 wav.writeUInt32LE(input.length*2,40);
 const gain=.87/peak;
 const fadeIn=Math.max(1,Math.round(.006*sampleRate));
 const fadeOut=Math.max(1,Math.round(.18*sampleRate));
 for(let i=0;i<input.length;i++){
  // One global linear gain and endpoint click protection: no tone/FX.
  const fade=Math.min(1,(i+1)/fadeIn,(input.length-i)/fadeOut);
  const x=Math.max(-1,Math.min(1,input[i]*gain*fade));
  wav.writeInt16LE(Math.round(x*32767),44+i*2);
 }
 return {wav,gain,peakBeforeNormalization:peak};
}
