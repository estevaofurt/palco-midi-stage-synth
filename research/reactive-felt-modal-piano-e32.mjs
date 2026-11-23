/**
 * Stage E3.2: one REACTIVE nonlinear felt hammer coupled bidirectionally to
 * the FULL passive 88-key, two-polarization multimode string+bridge system.
 *
 * THIS IS RESEARCH, NOT AN ACOUSTIC PIANO YET:
 * - ONE physically moving hammer per instance; 88 string keys remain connected.
 * - E2.3 modal masses, felt/hammer parameters, strike projections, soundboard
 *   modes and generalized lengths have NOT been physically calibrated.
 * - The old prescribed sin² force is disabled using externalForceMode:true.
 * - Air pressure, radiation, multi-hammer polyphony and MIDI are NOT solved.
 * - No recorded audio, sample attack, SoundFont, IR or hidden output oscillators.
 *
 * Let q = Σ w_j x_j be displacement of the string at the hammer point;
 * its conjugate generalized load is f_j = w_j F. The hammer feels -F.
 * U(delta)=k max(delta,0)^(p+1)/(p+1) is the felt potential.
 *
 * The passive implicit-midpoint string solver has exact linear response
 * q_new(F)=q_free + compliance*F, for the SAME time step and current bridge.
 * The hammer has x_new(F)=x_old+h*v_old-h²F/(2m).
 * Thus delta_new(F)=delta_free-F*(h²/(2m)+compliance).
 *
 * Choose F>=0 by solving the discrete-gradient contact force
 *     F = [U(delta_new(F))-U(delta_old)]/(delta_new(F)-delta_old).
 * This ensures EXACT contact work reciprocity: hammer kinetic energy lost
 * equals string work + change of felt potential (up to roundoff).
 * Since U is convex, RHS decreases as F increases; bisection is bounded.
 * The air/radiation system is deliberately not attached until corrected.
 */
import {SharedPassiveModalPiano} from './shared-passive-modal-piano.mjs';

const finite=(n,lo,hi)=>Number.isFinite(n)&&n>=lo&&n<=hi;
/** Effective modal mass for ideal sinusoidal steel-wire displacement.
 * This applies to a SINGLE local string model; identical geometry across
 * 88 different keys is NOT a physically measured full piano.
 */
export function idealStringModalMassKg({
 lengthM=.85,radiusM=.0006,densityKgM3=7850
}={}){
 if(!finite(lengthM,.1,2.5)||!finite(radiusM,.0001,.003)||
    !finite(densityKgM3,1000,20000))
  throw new RangeError('invalid illustrative string dimensions/density');
 return densityKgM3*Math.PI*radiusM**2*lengthM/2;
}
export class ReactiveFeltModalPiano {
 constructor({
  sampleRate=48000,key=48,
  velocityMps=2,hammerMassKg=.008,hammerGapM=.0004,
  feltStiffness=1e10,feltExponent=2.3,
  partialsBass=5,partialsTreble=2,
  coupling=.12,inharmonicity=.00010,
  stringGeometry=null,sustain=127
 }={}){
  if(!Number.isInteger(sampleRate)||sampleRate<22050||sampleRate>96000||
     !Number.isInteger(key)||key<21||key>108||
     !finite(velocityMps,0,10)||!finite(hammerMassKg,.0001,.1)||
     !finite(hammerGapM,0,.01)||
     !finite(feltStiffness,1e5,1e12)||
     !finite(feltExponent,1.1,4)||
     !finite(sustain,0,127))
   throw new RangeError('invalid reactive hammer contact setup');
  if(stringGeometry!==null&&(typeof stringGeometry!=='object'||Array.isArray(stringGeometry)))
   throw new RangeError('invalid local string geometry');
  this.localModalMassKg=stringGeometry===null?null:
   idealStringModalMassKg(stringGeometry);
  this.piano=new SharedPassiveModalPiano({
   sampleRate,externalForceMode:true,partialsBass,partialsTreble,
   coupling,inharmonicity,uniformModalMassKg:this.localModalMassKg
  });
  this.sampleRate=sampleRate;this.h=1/sampleRate;
  this.key=key;this.mass=hammerMassKg;
  this.hammerX=-hammerGapM;this.hammerV=velocityMps;
  this.k=feltStiffness;this.exponent=feltExponent;
  this.keyStart=this.piano.keyStart[key-21];
  this.keyEnd=this.piano.keyStart[key-20];
  this.freeRhs=new Float64Array(this.piano.n);
  this.force=0;this.maxForce=0;this.contactSamples=0;this.samples=0;
  // Open the struck key's damper, but do not trigger the old sine pulse.
  this.piano.held[key-21]=1;
  this.piano.setSustain(sustain);
  this.initialEnergy=this.totalMechanicalEnergy();
 }
 currentStringX(){
  const p=this.piano,w=p.strikeWeights;
  let x=0;
  for(let i=this.keyStart;i<this.keyEnd;i++)x+=w[i]*p.x[i];
  return x;
 }
 feltPotential(delta){
  return delta>0?this.k*delta**(this.exponent+1)/(this.exponent+1):0;
 }
 discreteGradient(oldDelta,newDelta){
  if(oldDelta<=0&&newDelta<=0)return 0;
  const change=newDelta-oldDelta;
  if(Math.abs(change)<1e-14)
   return this.k*Math.max(0,(oldDelta+newDelta)/2)**this.exponent;
  return Math.max(0,
   (this.feltPotential(newDelta)-this.feltPotential(oldDelta))/change);
 }
 totalMechanicalEnergy(){
  const delta=this.hammerX-this.currentStringX();
  return this.piano.energy()+.5*this.mass*this.hammerV**2+
   this.feltPotential(delta);
 }
 balanceRelativeError(){
  return (this.totalMechanicalEnergy()+this.piano.dissipated-this.initialEnergy)/
    Math.max(this.initialEnergy,1e-12);
 }
 noteOff(){this.piano.noteOff(this.key)}
 setSustain(cc){this.piano.setSustain(cc)}
 // Return force-independent response at q and its EXACT instantaneous
 // compliance, including feedback through the SAME shared passive bridge.
 predictor(){
  const p=this.piano,h=this.h,n=p.n,
        inv=p.aInverse,s=p.offDiagonal,ri=this.freeRhs;
  let bridgeStiff=p.sumK*p.bx[0],schurRhs=0;
  for(let i=0;i<n;i++){
   bridgeStiff-=p.coupling[i]*p.x[i];
   const kx=(p.ground[i]+p.coupling[i])*p.x[i]-
      p.coupling[i]*p.bx[0];
   ri[i]=p.mass[i]*p.v[i]-.5*h*kx;
   schurRhs+=s[i]*ri[i]*inv[i];
  }
  const rhs0=p.bmass[0]*p.bv[0]-
   .5*h*(bridgeStiff+(p.bground[0]+p.boardSpring)*p.bx[0]-
     p.boardSpring*p.bx[1])-schurRhs;
  const rhs1=p.bmass[1]*p.bv[1]-
   .5*h*((p.bground[1]+p.boardSpring)*p.bx[1]-
     p.boardSpring*p.bx[0]);
  const vBoard0=(rhs0*p.S11-p.S01*rhs1)/p.determinant;
  const w=p.strikeWeights;
  let derivativeSchur=0,q0=0,qFree=0;
  for(let i=this.keyStart;i<this.keyEnd;i++){
   const weight=w[i];
   derivativeSchur+=s[i]*(.5*h*weight)*inv[i];
   q0+=weight*p.x[i];
   qFree+=weight*(p.x[i]+h*(ri[i]-s[i]*vBoard0)*inv[i]);
  }
  const dvBoard0=-derivativeSchur*p.S11/p.determinant;
  let compliance=0;
  for(let i=this.keyStart;i<this.keyEnd;i++){
   const weight=w[i];
   compliance+=h*weight*((.5*h*weight-s[i]*dvBoard0)*inv[i]);
  }
  if(!(compliance>0&&Number.isFinite(compliance)))
   throw new RangeError('invalid mechanically passive string compliance');
  return {q0,qFree,compliance};
 }
 step(){
  const p=this.piano,h=this.h,oldX=this.hammerX,oldV=this.hammerV;
  const {q0,qFree,compliance}=this.predictor();
  const delta0=oldX-q0,freeDelta=oldX+h*oldV-qFree;
  const stiffness=h*h/(2*this.mass)+compliance;
  // F=0 if there is no compression in either the existing or free step.
  const upper=this.discreteGradient(delta0,freeDelta);
  let f=0;
  if(upper>0){
   let lo=0,hi=upper;
   for(let k=0;k<44;k++){
    const mid=(lo+hi)/2;
    const delta=freeDelta-stiffness*mid;
    const residual=mid-this.discreteGradient(delta0,delta);
    if(residual>=0)hi=mid;else lo=mid;
   }
   f=(lo+hi)/2;
  }
  const forces=p.forces,w=p.strikeWeights;
  // Only the struck key has external generalized contact forces.
  for(let i=this.keyStart;i<this.keyEnd;i++)forces[i]=f*w[i];
  p.step();
  const nextV=oldV-h*f/this.mass;
  this.hammerX=oldX+.5*h*(oldV+nextV);
  this.hammerV=nextV;
  this.force=f;
  this.maxForce=Math.max(this.maxForce,f);
  if(f>0)this.contactSamples++;
  this.samples++;
  if(!Number.isFinite(nextV)||!Number.isFinite(this.hammerX))
   throw new RangeError('nonfinite reactive hammer');
  return p.boardPanelVelocity;
 }
}
