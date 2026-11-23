/**
 * E3.2 — nonlinear HAMMER ↔ MULTI-PARTIAL STRING ↔ SHARED BRIDGE contact.
 * EXPERIMENTAL, SAMPLE-FREE, NOT Stage-D public DSP.
 *
 * This is the first *two-way* felt contact onto the same passive mechanical
 * degrees of freedom that radiate through the common bridge.
 *
 * Each key has one lumped hammer (one per key, NOT a separately synthesized
 * piano attack). The unilateral contact displacement is
 *   delta = hammerPosition - sum_j strikeModeShape_j * stringModePosition_j.
 * Potential: U(delta) = k * max(delta,0)^(p+1)/(p+1).
 *
 * A discrete-gradient force F = (U(delta_new)-U(delta_old)) /
 *                              (delta_new-delta_old)
 * is solved implicitly with the Schur complement of the *existing* passive
 * 88-key network. Force is applied to the string modes with +shape*F and
 * to the hammer with -F. The same F is used in both integrations.
 * This ensures E(after)+dissipation=E(before)+launchWork up to root tolerance,
 * INCLUDING stored nonlinear compression energy — never inject arbitrary
 * recorded piano attacks or predetermined sin² hammer-force pulses.
 *
 * The modal masses, spring constants and contact geometry of E2.3 remain
 * illustrative generalized mechanical units, NOT calibrated SI, even if
 * the isolated E3.1 pair used kg/m/N labels. This is not a real piano yet.
 * Benchmark and 32–64 voice acceptance on PC/Android are still pending.
 */
import {SharedPassiveModalPiano} from './shared-passive-modal-piano.mjs';

function potential(delta,stiffness,power){
 return delta>0?stiffness*delta**(power+1)/(power+1):0;
}
export function contactDiscreteGradient(before,after,stiffness,power){
 if(!Number.isFinite(before)||!Number.isFinite(after)||
    !Number.isFinite(stiffness)||stiffness<=0||
    !Number.isFinite(power)||power<=1)
  throw new RangeError('invalid nonlinear contact discrete gradient');
 const difference=after-before;
 if(Math.abs(difference)<=1e-13*Math.max(1e-4,Math.abs(before),Math.abs(after)))
  return stiffness*Math.max(0,(before+after)/2)**power;
 const result=(potential(after,stiffness,power)-
               potential(before,stiffness,power))/difference;
 return result>0?result:0;
}

export class CoupledNonlinearHammerPiano {
 constructor({sampleRate=48000,pianoOptions={},
  hammerMass=.008,feltStiffness=1e10,feltExponent=2.3,
  hammerGap=.0004,maxHammerSpeed=3.2,maxHammers=64,
  solverPasses=3,rootIterations=16}={}){
  if(!Number.isInteger(sampleRate)||sampleRate<44100||sampleRate>96000||
    !Number.isFinite(hammerMass)||hammerMass<=0||hammerMass>1||
    !Number.isFinite(feltStiffness)||feltStiffness<=0||feltStiffness>1e12||
    !Number.isFinite(feltExponent)||feltExponent<=1.1||feltExponent>4||
    !Number.isFinite(hammerGap)||hammerGap<=0||hammerGap>.01||
    !Number.isFinite(maxHammerSpeed)||maxHammerSpeed<=0||maxHammerSpeed>10||
    !Number.isInteger(maxHammers)||maxHammers<1||maxHammers>88||
    !Number.isInteger(solverPasses)||solverPasses<2||solverPasses>12||
    !Number.isInteger(rootIterations)||rootIterations<8||rootIterations>48)
   throw new RangeError('invalid E3.2 physics parameters');
  this.piano=new SharedPassiveModalPiano({
   ...pianoOptions,sampleRate,externalForceMode:true
  });
  this.h=1/sampleRate;
  this.mass=hammerMass;this.stiffness=feltStiffness;this.power=feltExponent;
  this.gap=hammerGap;this.maxSpeed=maxHammerSpeed;
  this.maxHammers=maxHammers;this.solverPasses=solverPasses;
  this.rootIterations=rootIterations;
  this.hammers=new Map();
  this.freeRhs=new Float64Array(this.piano.n);
  this.launchWork=0;
  this.steps=0;this.peakForce=0;this.contactSampleCount=0;
  this.rootEvaluations=0;this.maxForceResidual=0;
  this.bridgeVelocity=0;this.boardPanelVelocity=0;
 }
 stringDisplacement(key){
  const p=this.piano;let sum=0,k=key-21;
  for(let i=p.keyStart[k];i<p.keyStart[k+1];i++)
   sum+=p.strikeWeights[i]*p.x[i];
  return sum;
 }
 contactCompression(hammer){
  return hammer.q-this.stringDisplacement(hammer.key);
 }
 totalEnergy(){
  let total=this.piano.energy();
  for(const hammer of this.hammers.values()){
   const compression=this.contactCompression(hammer);
   total+=.5*hammer.mass*hammer.v*hammer.v+
    potential(compression,this.stiffness,this.power);
  }
  return total;
 }
 noteOn(key,{velocity=90}={}){
  if(!Number.isInteger(key)||key<21||key>108||
     !Number.isFinite(velocity)||velocity<1||velocity>127)
   throw new RangeError('invalid physical MIDI hammer launch');
  if(!this.hammers.has(key)&&this.hammers.size>=this.maxHammers)
   throw new RangeError('too many E3.2 hammers');
  const before=this.totalEnergy();
  // Velocity is an initial kinetic condition, NEVER a canned force pulse.
  const speed=this.maxSpeed*(velocity/127)**1.35;
  const wasHeld=this.hammers.get(key)?.held??false;
  this.hammers.set(key,{key,q:-this.gap,v:speed,mass:this.mass,
   held:true,force:0,contactSamples:0,maxForce:0,
   deltaOld:0,deltaFree:0,mobility:0,t:0});
  if(!wasHeld)this.piano.held[key-21]=1;
  this.piano.updateDampers();
  this.launchWork+=this.totalEnergy()-before;
 }
 noteOff(key){
  if(!Number.isInteger(key)||key<21||key>108)
   throw new RangeError('invalid physical MIDI note-off');
  const h=this.hammers.get(key);
  if(h){h.held=false;this.piano.held[key-21]=0;this.piano.updateDampers();}
 }
 setSustain(cc){this.piano.setSustain(cc)}
 /** Free midpoint solve, plus exact rank-one hammer→string compliance.
  * No state is committed until contact forces have been solved.
  */
 prepareFreeResponse(){
  const p=this.piano,h=this.h,xb=p.bx,bv=p.bv,inv=p.aInverse,
   s=p.offDiagonal,x=p.x,v=p.v;
  let stiffness=p.sumK*xb[0],schur=0;
  for(let i=0;i<p.n;i++){
   stiffness-=p.coupling[i]*x[i];
   const kx=(p.ground[i]+p.coupling[i])*x[i]-
    p.coupling[i]*xb[0];
   const ri=p.mass[i]*v[i]-.5*h*kx;
   this.freeRhs[i]=ri;
   schur+=s[i]*ri*inv[i];
  }
  const b0=p.bmass[0]*bv[0]-.5*h*(stiffness+
    (p.bground[0]+p.boardSpring)*xb[0]-p.boardSpring*xb[1])-schur;
  const b1=p.bmass[1]*bv[1]-.5*h*
    ((p.bground[1]+p.boardSpring)*xb[1]-p.boardSpring*xb[0]);
  const bridgeMid=(b0*p.S11-p.S01*b1)/p.determinant;
  const rankFactor=.5*h*h*p.S11/p.determinant;
  for(const hammer of this.hammers.values()){
   const keyIndex=hammer.key-21;
   let oldString=0,newFreeString=0,localMobility=0,t=0;
   for(let i=p.keyStart[keyIndex];i<p.keyStart[keyIndex+1];i++){
    const w=p.strikeWeights[i],freeMid=
     (this.freeRhs[i]-s[i]*bridgeMid)*inv[i];
    oldString+=w*x[i];
    newFreeString+=w*(x[i]+h*freeMid);
    localMobility+=w*w*inv[i];
    t+=w*s[i]*inv[i];
   }
   hammer.deltaOld=hammer.q-oldString;
   hammer.deltaFree=hammer.q+h*hammer.v-newFreeString;
   hammer.t=t;
   hammer.mobility=.5*h*h*(1/hammer.mass+localMobility)+
    rankFactor*t*t;
  }
  return rankFactor;
 }
 /**
  * Bracketed Newton. U is convex, so F = DG(U, deltaFree - mobility*F)
  * has exactly one nonnegative solution. Fall back to bisection when Newton
  * would leave the bracket. The derivative is analytically derived, not
  * a fitted hammer velocity curve.
  */
 solveForce(hammer,otherBridgeForce){
  const base=hammer.deltaFree-otherBridgeForce;
  const old=hammer.deltaOld,diagonal=hammer.mobility;
  const upper=contactDiscreteGradient(old,base,this.stiffness,this.power);
  if(!(upper>0))return 0;
  if(!Number.isFinite(upper)||upper>1e7)
   throw new RangeError('unphysical implicit hammer contact');
  let lo=0,hi=upper,force=upper*.5;
  const tolerance=2e-11*Math.max(1,upper);
  const stiffness=this.stiffness,power=this.power;
  for(let iteration=0;iteration<this.rootIterations;iteration++){
   const after=base-diagonal*force,difference=after-old;
   const beforePos=Math.max(0,old),afterPos=Math.max(0,after);
   let gradient,slope;
   if(Math.abs(difference)<=1e-13*
     Math.max(1e-4,Math.abs(old),Math.abs(after))){
    const contact=Math.max(0,(after+old)*.5);
    gradient=stiffness*contact**power;
    slope=.5*stiffness*power*contact**(power-1);
   }else{
    const jump=stiffness*(afterPos**(power+1)-
      beforePos**(power+1))/(power+1);
    gradient=jump/difference;
    slope=(stiffness*afterPos**power*difference-jump)/
     (difference*difference);
   }
   slope=Math.max(0,slope);
   const residual=force-gradient;
   this.rootEvaluations++;
   if(Math.abs(residual)<=tolerance)break;
   if(residual>0)hi=force;else lo=force;
   const derivative=1+diagonal*slope;
   const proposal=force-residual/derivative;
   force=proposal>lo&&proposal<hi?proposal:(lo+hi)*.5;
  }
  const actual=contactDiscreteGradient(old,base-diagonal*force,
    stiffness,power);
  const finalResidual=Math.abs(force-actual);
  this.maxForceResidual=Math.max(this.maxForceResidual,finalResidual);
  if(finalResidual>1e-7*Math.max(1,upper))
   throw new RangeError('nonlinear hammer root failed convergence');
  return force;
 }
 step(){
  const p=this.piano,h=this.h,forces=p.forces;
  forces.fill(0);
  if(this.hammers.size){
   const factor=this.prepareFreeResponse();
   let sumT=0;
   for(const hammer of this.hammers.values())sumT+=hammer.t*hammer.force;
   for(let pass=0;pass<this.solverPasses;pass++){
    let largestChange=0;
    for(const hammer of this.hammers.values()){
     const other=factor*hammer.t*(sumT-hammer.t*hammer.force);
     const updated=this.solveForce(hammer,other);
     largestChange=Math.max(largestChange,Math.abs(updated-hammer.force));
     sumT+=hammer.t*(updated-hammer.force);
     hammer.force=updated;
    }
    if(largestChange<1e-10)break;
   }
   for(const hammer of this.hammers.values()){
    const k=hammer.key-21,F=hammer.force;
    if(F>0){
     this.contactSampleCount++;hammer.contactSamples++;
     this.peakForce=Math.max(this.peakForce,F);
     hammer.maxForce=Math.max(hammer.maxForce,F);
    }
    for(let i=p.keyStart[k];i<p.keyStart[k+1];i++)
     forces[i]+=p.strikeWeights[i]*F;
   }
  }
  p.step();
  for(const hammer of this.hammers.values()){
   const oldVelocity=hammer.v;
   hammer.v-=h*hammer.force/hammer.mass;
   hammer.q+=h*.5*(oldVelocity+hammer.v);
   if(!Number.isFinite(hammer.q)||!Number.isFinite(hammer.v))
    throw new RangeError('nonfinite E3.2 hammer response');
  }
  this.bridgeVelocity=p.bridgeVelocity;
  this.boardPanelVelocity=p.boardPanelVelocity;
  this.steps++;
  return this.boardPanelVelocity;
 }
 energyBalanceError(){
  return this.totalEnergy()+this.piano.dissipated-this.launchWork;
 }
 energyBalanceRelativeError(){
  return this.energyBalanceError()/Math.max(1e-12,Math.abs(this.launchWork));
 }
}
