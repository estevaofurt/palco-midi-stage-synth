/**
 * Stage E2.2 — measured radiation transport (RESEARCH ONLY).
 *
 * Input: generalized board acceleration obtained from the E2.1 bridge.
 * Output: a two-channel convolution proxy which becomes calibrated pressure
 * ONLY if the physical bridge coordinate has been measured/calibrated AND
 * the supplied impulse response is a measured Pa/(m/s²) transfer with
 * authorized provenance. No synthetic "wood" modes, fallback EQ or FX.
 *
 * The impulse response is REQUIRED and externally validated. An H1 spectrum
 * alone is not an impulse response: phase, causality, windowing, alignment
 * and calibration must first be independently resolved offline.
 *
 * No allocations inside step() or render(); direct FIR O(taps)/sample,
 * practical only for SHORT validated filters, never assert full 64-note CPU.
 */
import {HammerDrivenPassivePiano} from './hammer-driven-passive-piano.mjs';

function typedFinite(a,label){
 if(!(a instanceof Float32Array||a instanceof Float64Array)||a.length<1||a.length>1024)
  throw new RangeError(label+' needs 1..1024 numeric FIR taps');
 for(const x of a)if(!Number.isFinite(x))throw new TypeError(label+' contains nonfinite tap');
}
export class MeasuredRadiationAdapter {
 constructor({impulseLeft,impulseRight,sampleRate,metadata}={}){
  typedFinite(impulseLeft,'left');
  typedFinite(impulseRight,'right');
  if(!Number.isFinite(sampleRate)||sampleRate<22050||sampleRate>192000)
   throw new RangeError('sample rate must be 22050..192000');
  if(impulseLeft.length!==impulseRight.length)
   throw new RangeError('stereo FIR lengths differ');
  if(!metadata||metadata.inputUnit!=='m/s2'||metadata.outputUnit!=='Pa'||
     metadata.transferUnit!=='Pa/(m/s2)'||
     metadata.measured!==true||
     metadata.sourceType!=='synchronized-calibrated-bridge-and-microphone'||
     !metadata.sourceId||!metadata.rightsDocumentId||
     metadata.commercialUseAuthorized!==true||
     metadata.sampleRate!==sampleRate||
     !Number.isInteger(metadata.alignmentSamples)||metadata.alignmentSamples<0)
   throw new RangeError('missing measured/calibrated/synchronized/authorized radiation provenance');
  // This declaration is NOT a legal license verification. Source hash and
  // rights record must be audited outside DSP before commercial integration.
  this.sampleRate=sampleRate;
  this.length=impulseLeft.length;
  this.left=new Float64Array(impulseLeft);
  this.right=new Float64Array(impulseRight);
  this.history=new Float64Array(this.length);
  this.cursor=0;
  this.previousVelocity=0;
  this.metadata={...metadata};
  this.samples=0;
 }
 reset(){
  this.history.fill(0);this.cursor=0;this.previousVelocity=0;this.samples=0;
 }
 step(boardVelocity){
  if(!Number.isFinite(boardVelocity))throw new TypeError('nonfinite bridge velocity');
  const acceleration=(boardVelocity-this.previousVelocity)*this.sampleRate;
  this.previousVelocity=boardVelocity;
  const at=this.cursor;
  this.history[at]=acceleration;
  let l=0,r=0,index=at;
  for(let j=0;j<this.length;j++){
   const input=this.history[index];
   l+=input*this.left[j];
   r+=input*this.right[j];
   if(--index<0)index=this.length-1;
  }
  this.cursor=(at+1)%this.length;
  this.samples++;
  return {left:l,right:r};
 }
 /**
  * Allocate-free caller API for production-style sample loops. The object
  * returned by step() is only intended for OFFLINE research and uses an
  * allocation: do not call step() in a real-time callback. render() is
  * allocation-free by using the private _sample method.
  */
 _sample(boardVelocity,outL,outR,i){
  if(!Number.isFinite(boardVelocity))throw new TypeError('nonfinite bridge velocity');
  const acceleration=(boardVelocity-this.previousVelocity)*this.sampleRate;
  this.previousVelocity=boardVelocity;
  const at=this.cursor;
  this.history[at]=acceleration;
  let l=0,r=0,index=at;
  for(let j=0;j<this.length;j++){
   const input=this.history[index];
   l+=input*this.left[j];
   r+=input*this.right[j];
   if(--index<0)index=this.length-1;
  }
  this.cursor=(at+1)%this.length;
  this.samples++;
  outL[i]=l;outR[i]=r;
 }
 render(velocities,left,right){
  if(!(velocities instanceof Float32Array||velocities instanceof Float64Array)||
     !(left instanceof Float32Array||left instanceof Float64Array)||
     !(right instanceof Float32Array||right instanceof Float64Array)||
     velocities.length!==left.length||velocities.length!==right.length||
     left===right||left===velocities||right===velocities)
   throw new RangeError('requires distinct equal-length typed buffers');
  for(let i=0;i<velocities.length;i++)this._sample(velocities[i],left,right,i);
 }
}
export class CalibratedPassivePianoResearchChain {
 constructor({sampleRate=48000,measuredImpulseLeft,measuredImpulseRight,metadata,
               coupling=.12}={}){
  if(!metadata||metadata.bridgeCoordinateCalibrated!==true)
   throw new RangeError('uncalibrated generalized board coordinate cannot be used as m/s velocity');
  this.mechanics=new HammerDrivenPassivePiano({sampleRate,coupling});
  this.radiation=new MeasuredRadiationAdapter({
   impulseLeft:measuredImpulseLeft,impulseRight:measuredImpulseRight,
   sampleRate,metadata});
  this.velocity=new Float64Array(128);
 }
 noteOn(key,params){this.mechanics.noteOn(key,params)}
 noteOff(key){this.mechanics.noteOff(key)}
 setSustain(value){this.mechanics.setSustain(value)}
 render(left,right){
  if(!(left instanceof Float32Array||left instanceof Float64Array)||
     !(right instanceof Float32Array||right instanceof Float64Array)||
     left===right||left.length!==right.length||left.length>128)
   throw new RangeError('calibrated chain requires distinct <=128 sample buffers');
  this.mechanics.render(this.velocity,0,left.length);
  // Render only the samples written; no allocation in full-chain render.
  this.radiation.renderBlock(this.velocity,left,right,left.length);
 }
 reset(){this.mechanics.reset();this.radiation.reset();}
}
MeasuredRadiationAdapter.prototype.renderBlock=function(velocities,left,right,n){
 if(!Number.isInteger(n)||n<0||n>velocities.length||n>left.length||n>right.length)
  throw new RangeError('invalid block');
 for(let i=0;i<n;i++)this._sample(velocities[i],left,right,i);
};
