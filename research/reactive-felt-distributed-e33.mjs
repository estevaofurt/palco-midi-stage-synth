/**
 * E3.3 — ONE nonlinear reactive hammer drives ALL 88 coupled strings and
 * the physically distributed 8-mode board. No recorded sound or IR.
 *
 * Research only: one contact at a time, arbitrary generalized masses,
 * uncalibrated piano geometry, no validated airborne pressure or browser DSP.
 * The older E3.2 reactive one-hammer network remains unmodified.
 *
 * Derivation: free string midpoint velocities solved with the same full
 * Schur elimination as E3.3 plate, including a dense SPD 9x9 panel matrix.
 * The compliance at the hammer point is
 *
 * dq/dF = h Σ_j w_j /a_j [(.5*h*w_j) - s_j * dv_bridge/dF]
 * dv_bridge/dF = -(Σ_j s_j*.5*h*w_j/a_j) * [S^{-1}]_00.
 *
 * Hammer delta_new=delta_free - F*(h²/(2*m_h)+dq/dF).
 * The force F is found by a bounded bisection of the convex felt's discrete
 * potential gradient; hammer/strings/board energy stays balanced.
 */
import {PassiveDistributedSoundboardE33}
 from './passive-distributed-soundboard-e33.mjs';

const bounded=(v,a,b)=>Number.isFinite(v)&&v>=a&&v<=b;
export class ReactiveFeltDistributedPianoE33 {
 constructor({
  sampleRate=48000,key=48,
  hammerVelocityMps=2,hammerMassKg=.008,hammerGapM=.0004,
  feltStiffness=1e10,feltExponent=2.3,
  feltHardeningRatio=0,feltHardeningThresholdM=.00016,
  panelModes=8,partialsBass=5,partialsTreble=2,sustain=127
 }={}){
  if(!Number.isInteger(key)||key<21||key>108||
     !bounded(hammerVelocityMps,0,10)||
     !bounded(hammerMassKg,.0001,.1)||
     !bounded(hammerGapM,0,.01)||
     !bounded(feltStiffness,1e5,1e12)||
     !bounded(feltExponent,1.1,4)||
     !bounded(feltHardeningRatio,0,32)||
     !bounded(feltHardeningThresholdM,0,.002)||
     !bounded(sustain,0,127))
    throw new RangeError('invalid reactive distributed plate contact');
  this.piano=new PassiveDistributedSoundboardE33({
   sampleRate,panelModes,partialsBass,partialsTreble,externalForceMode:true
  });
  this.h=1/sampleRate;this.key=key;this.mass=hammerMassKg;
  this.hammerX=-hammerGapM;this.hammerV=hammerVelocityMps;
  this.k=feltStiffness;this.exponent=feltExponent;
  // E3.4 opt-in: compliant outer felt compresses into denser inner felt.
  // A second convex potential, NOT sampled impact noise or EQ.
  this.hardeningRatio=feltHardeningRatio;
  this.hardeningThresholdM=feltHardeningThresholdM;
  this.start=this.piano.keyStart[key-21];
  this.end=this.piano.keyStart[key-20];
  this.freeRhs=new Float64Array(this.piano.n);
  this.force=0;this.peakForce=0;this.contactSamples=0;
  this.piano.held[key-21]=1;
  this.piano.setSustain(sustain);
  this.initialEnergy=this.totalEnergy();
 }
 stringAtHammer(){
  const p=this.piano;let q=0;
  for(let i=this.start;i<this.end;i++)
   q+=p.strikeWeights[i]*p.x[i];
  return q;
 }
 potential(delta){
  if(delta<=0)return 0;
  const power=this.exponent+1;
  const core=Math.max(0,delta-this.hardeningThresholdM);
  return this.k*delta**power/power+
   this.k*this.hardeningRatio*core**power/power;
 }
 forceAtCompression(delta){
  if(delta<=0)return 0;
  const core=Math.max(0,delta-this.hardeningThresholdM);
  return this.k*delta**this.exponent+
   this.k*this.hardeningRatio*core**this.exponent;
 }
 gradient(previous,current){
  if(previous<=0&&current<=0)return 0;
  const dx=current-previous;
  if(Math.abs(dx)<1e-14)
   return this.forceAtCompression(Math.max(0,.5*(previous+current)));
  return Math.max(0,(this.potential(current)-this.potential(previous))/dx);
 }
 totalEnergy(){
  return this.piano.energy()+.5*this.mass*this.hammerV**2+
   this.potential(this.hammerX-this.stringAtHammer());
 }
 relativeEnergyResidual(){
  const p=this.piano;
  return (this.totalEnergy()+p.dissipated-this.initialEnergy)/
    Math.max(this.initialEnergy,1e-12);
 }
 noteOff(){this.piano.noteOff(this.key)}
 setSustain(cc){this.piano.setSustain(cc)}
 predictor(){
  const p=this.piano,h=this.h,inv=p.aInverse,
        s=p.offDiagonal,ri=this.freeRhs;
  let bridgeSpring=(p.bridgeGround+p.sumK)*p.bridgeX,
      schurRhs=0;
  for(let i=0;i<p.n;i++){
   bridgeSpring-=p.coupling[i]*p.x[i];
   const kx=(p.ground[i]+p.coupling[i])*p.x[i]-
      p.coupling[i]*p.bridgeX;
   ri[i]=p.mass[i]*p.v[i]-.5*h*kx;
   schurRhs+=s[i]*ri[i]*inv[i];
  }
  let plateAtBridge=0;
  for(let j=0;j<p.panelModes;j++)
   plateAtBridge+=p.panelShapeAtBridge[j]*p.panelX[j];
  const mismatch=p.bridgeX-plateAtBridge;
  bridgeSpring+=p.bridgePanelSpring*mismatch;
  p.boardRhs[0]=p.bridgeMass*p.bridgeV-
    .5*h*bridgeSpring-schurRhs;
  for(let j=0;j<p.panelModes;j++)
   p.boardRhs[j+1]=p.panelMass[j]*p.panelV[j]-
    .5*h*(p.panelGround[j]*p.panelX[j]-
     p.bridgePanelSpring*p.panelShapeAtBridge[j]*mismatch);
  p.solveBoard();
  const bridgeFree=p.boardMidV[0],w=p.strikeWeights;
  let qOld=0,qFree=0,drive=0;
  for(let i=this.start;i<this.end;i++){
   const weight=w[i];
   qOld+=weight*p.x[i];
   qFree+=weight*(p.x[i]+h*(ri[i]-s[i]*bridgeFree)*inv[i]);
   drive+=s[i]*(.5*h*weight)*inv[i];
  }
  // Solve S z=e0 using the already factored SPD matrix;
  // inverseS00=z0 is positive and includes ALL spatial plate modes.
  p.boardRhs.fill(0);
  p.boardRhs[0]=1;
  p.solveBoard();
  const inverseS00=p.boardMidV[0];
  const derivativeBridge=-drive*inverseS00;
  let compliance=0;
  for(let i=this.start;i<this.end;i++){
   const weight=w[i];
   compliance+=h*weight*
    ((.5*h*weight-s[i]*derivativeBridge)*inv[i]);
  }
  if(!(compliance>0&&Number.isFinite(compliance)&&
       inverseS00>0))
   throw new RangeError('invalid reciprocal multimode contact compliance');
  return {qOld,qFree,compliance};
 }
 step(){
  const p=this.piano,h=this.h,xOld=this.hammerX,vOld=this.hammerV;
  const {qOld,qFree,compliance}=this.predictor();
  const deltaOld=xOld-qOld,
    deltaFree=xOld+h*vOld-qFree;
  const effectiveCompliance=h*h/(2*this.mass)+compliance;
  const max=this.gradient(deltaOld,deltaFree);
  let F=0;
  if(max>0){
   let low=0,high=max;
   for(let i=0;i<44;i++){
    const mid=.5*(low+high);
    const deltaNew=deltaFree-mid*effectiveCompliance;
    if(mid-this.gradient(deltaOld,deltaNew)>=0)
     high=mid;else low=mid;
   }
   F=.5*(low+high);
  }
  for(let i=this.start;i<this.end;i++)
   p.forces[i]=F*p.strikeWeights[i];
  p.step();
  const nextV=vOld-h*F/this.mass;
  this.hammerX=xOld+.5*h*(vOld+nextV);
  this.hammerV=nextV;
  this.force=F;
  this.peakForce=Math.max(this.peakForce,F);
  if(F>0)this.contactSamples++;
  if(!Number.isFinite(nextV)||!Number.isFinite(this.hammerX))
   throw new RangeError('nonfinite nonlinear distributed contact');
  return p.panelVelocity;
 }
}
