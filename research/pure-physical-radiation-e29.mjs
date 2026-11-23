/**
 * E2.9: 100%-SYNTHESIZED PHYSICAL SCORE WITH ANALYTIC AIR RADIATION.
 * No recorded audio, sample sets, acoustic convolution responses, FX or
 * post-piano oscillators. Offline only, not integrated in Stage-D.
 */
import {SharedPassiveModalPiano} from './shared-passive-modal-piano.mjs';
import {makePurePhysicalScore} from './pure-physical-audition-e28.mjs';
import {AnalyticSoundboardRadiator} from './analytic-soundboard-radiation.mjs';

export function renderAnalyticPhysicalPiano({
 sampleRate=48000,seconds=13,score=makePurePhysicalScore(),
 force=105,partialsBass=5,partialsTreble=2,
 radiation={}
}={}){
 if(!Number.isInteger(sampleRate)||sampleRate<22050||sampleRate>96000||
   !Number.isFinite(seconds)||seconds<.4||seconds>30||
   !Number.isFinite(force)||force<=0||force>1e5||
   !Array.isArray(score)||score.length>512)
  throw new RangeError('invalid physical audition setup');
 const piano=new SharedPassiveModalPiano({sampleRate,partialsBass,partialsTreble});
 const radiator=new AnalyticSoundboardRadiator({sampleRate,...radiation});
 const frames=Math.floor(sampleRate*seconds);
 const left=new Float64Array(frames),right=new Float64Array(frames);
 const events=score.map((event,i)=>{
  if(!event||!Number.isFinite(event.seconds)||
     event.seconds<0||event.seconds>=seconds||
     !['on','off','pedal'].includes(event.type)||
     (event.type==='pedal'&&(!Number.isFinite(event.cc)||event.cc<0||event.cc>127))||
     (event.type!=='pedal'&&(!Number.isInteger(event.key)||event.key<21||event.key>108))||
     (event.type==='on'&&(!Number.isFinite(event.velocity)||event.velocity<1||event.velocity>127)))
   throw new RangeError('invalid event in physical score');
  return {...event,at:Math.round(event.seconds*sampleRate),order:i};
 }).sort((a,b)=>a.at-b.at||a.order-b.order);
 let cursor=0,peak=0;
 for(let i=0;i<frames;i++){
  while(cursor<events.length&&events[cursor].at===i){
   const e=events[cursor++];
   if(e.type==='pedal')piano.setSustain(e.cc);
   else if(e.type==='off')piano.noteOff(e.key);
   else piano.noteOn(e.key,{velocity:e.velocity,peakForce:force,contactMs:3});
  }
  piano.step();
  // Two velocities of the same mechanically coupled 88-key system:
  // first bridge/board mode and second board mode. No dry PCM mix.
  radiator.step(piano.bridgeVelocity,piano.boardPanelVelocity);
  const l=radiator.left,r=radiator.right;
  if(!Number.isFinite(l)||!Number.isFinite(r))
   throw new RangeError('nonfinite physically radiated wave');
  left[i]=l;right[i]=r;
  peak=Math.max(peak,Math.abs(l),Math.abs(r));
 }
 if(!(peak>0))throw new RangeError('acoustically silent score');
 const balance=Math.abs(piano.energyBalanceError())/Math.max(1,piano.externalWork);
 if(!(balance<1e-7))throw new RangeError('nonpassive mechanical simulation');
 return {
  left,right,
  diagnostics:{
   sampleRate,seconds,events:events.length,
   connectedKeys:88,mechanicalStringCoordinates:piano.n,
   sharedPassiveBoardCoordinates:2,platePatches:radiator.patchCount,
   sampleFree:true,recordedImpulseResponses:0,
   radiationMethod:'Rayleigh infinite-baffle spatial quadrature, no recorded IR',
   outputUnit:'relative pressure proxy; modal velocity not calibrated in SI',
   peakRelativePressure:peak,energyBalanceRelativeError:balance,
   physicallyCalibrated:false,listenerEvaluationComplete:false,
   commercialReleaseApproved:false
  }
 };
}
