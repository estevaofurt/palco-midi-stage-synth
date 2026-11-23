/**
 * STAGE SYNTH V4.0: NEW single-string mechanical bench, no E2/E3 imports.
 * ONE stiff string with physical SI geometry and a unilateral felt hammer.
 * No soundboard, acoustic pressure, PCM notes, samples, SF2, IR or FX.
 *
 * String: mu*y_tt = T*y_xx - EI*y_xxxx - positive_loss*y_t + contact.
 * Pinned-boundary modes: sin(n*pi*x/L), modal mass mu*L/2.
 * f_n = n/(2L)*sqrt(T/mu)*sqrt(1 + B*n*n), B=pi^2*EI/(T*L^2).
 * Hammer: U(delta)=k*positive(delta)^(p+1)/(p+1).
 * Fully reactive, discrete-gradient contact + implicit midpoint string;
 * total stored energy + dissipation = original hammer kinetic energy.
 *
 * NOT an acoustic piano yet; source data and dimensions are illustrative.
 */
const TAU=2*Math.PI;
const valid=(x,lo,hi)=>Number.isFinite(x)&&x>=lo&&x<=hi;
export class StiffStringHammerV4 {
 constructor({sampleRate=48000,numberOfModes=32,
  lengthM=.62,radiusM=.00048,densityKgM3=7850,
  youngModulusPa=2e11,targetFundamentalHz=261.625565,
  hammerStrikeFraction=.125,hammerMassKg=.008,
  hammerGapM=.00020,hammerInitialVelocityMps=2.0,
  feltScale=1e10,feltExponent=2.3,
  baseLossRateS=0.7,extraLossRateByModeSquaredS=.006}={}){
  if(!Number.isInteger(sampleRate)||sampleRate<22050||sampleRate>192000||
     !Number.isInteger(numberOfModes)||numberOfModes<4||numberOfModes>96||
     !valid(lengthM,.15,2.5)||!valid(radiusM,.00012,.002)||
     !valid(densityKgM3,1000,15000)||!valid(youngModulusPa,1e9,4e11)||
     !valid(targetFundamentalHz,28,1500)||
     !valid(hammerStrikeFraction,.04,.40)||
     !valid(hammerMassKg,.001,.050)||!valid(hammerGapM,0,.003)||
     !valid(hammerInitialVelocityMps,0,7)||
     !valid(feltScale,1e6,1e12)||!valid(feltExponent,1.3,3.8)||
     !valid(baseLossRateS,0,12)||
     !valid(extraLossRateByModeSquaredS,0,.05))
   throw new RangeError('invalid physical string or hammer geometry');
  this.sampleRate=sampleRate;this.dt=1/sampleRate;
  this.lengthM=lengthM;this.radiusM=radiusM;
  this.linearDensityKgM=densityKgM3*Math.PI*radiusM**2;
  this.bendingRigidityNm2=youngModulusPa*Math.PI*radiusM**4/4;
  this.tensionN=this.linearDensityKgM*(2*lengthM*targetFundamentalHz)**2-
   this.bendingRigidityNm2*(Math.PI/lengthM)**2;
  if(!(this.tensionN>0&&this.tensionN<4000))
   throw new RangeError('target pitch requires nonphysical string tension');
  this.inharmonicityB=Math.PI**2*this.bendingRigidityNm2/
   (this.tensionN*lengthM**2);
  this.modalMassKg=.5*this.linearDensityKgM*lengthM;
  this.targetFundamentalHz=targetFundamentalHz;
  this.xHammerM=-hammerGapM;this.vHammerMps=hammerInitialVelocityMps;
  this.hammerMassKg=hammerMassKg;
  this.feltScale=feltScale;this.feltExponent=feltExponent;
  this.modeIndices=[];
  const omega=[],stiffness=[],loss=[],striking=[],invDenom=[];
  for(let n=1;n<=numberOfModes;n++){
   const waveNumber=n*Math.PI/lengthM;
   const squareOmega=(this.tensionN*waveNumber**2+
    this.bendingRigidityNm2*waveNumber**4)/this.linearDensityKgM;
   const f=Math.sqrt(squareOmega)/TAU;
   if(f>=sampleRate*.42)break;
   const k=this.modalMassKg*squareOmega;
   const gamma=baseLossRateS+extraLossRateByModeSquaredS*n*n;
   const damping=2*this.modalMassKg*gamma;
   const denom=this.modalMassKg+.5*this.dt*damping+
    .25*this.dt*this.dt*k;
   this.modeIndices.push(n);
   omega.push(TAU*f);stiffness.push(k);loss.push(damping);
   striking.push(Math.sin(n*Math.PI*hammerStrikeFraction));
   invDenom.push(1/denom);
  }
  if(this.modeIndices.length<4)
   throw new RangeError('sample rate cannot represent string spectrum');
  this.n=this.modeIndices.length;
  this.omega=Float64Array.from(omega);
  this.modalStiffness=Float64Array.from(stiffness);
  this.modalDamping=Float64Array.from(loss);
  this.strikeShapes=Float64Array.from(striking);
  this.invDenom=Float64Array.from(invDenom);
  this.q=new Float64Array(this.n);this.v=new Float64Array(this.n);
  this.midpointV=new Float64Array(this.n);
  this.freeV=new Float64Array(this.n);
  this.contactForceN=0;this.peakContactForceN=0;
  this.contactSamples=0;this.steps=0;this.dissipatedJ=0;
  this.initialEnergyJ=this.totalEnergyJ();
 }
 get frequenciesHz(){return Float64Array.from(this.omega,w=>w/TAU)}
 strikeDisplacementM(){
  let x=0;
  for(let j=0;j<this.n;j++)x+=this.strikeShapes[j]*this.q[j];
  return x;
 }
 feltPotentialJ(deltaM){
  const compression=Math.max(0,deltaM);
  return this.feltScale*compression**(this.feltExponent+1)/
   (this.feltExponent+1);
 }
 contactGradientN(oldDelta,newDelta){
  if(oldDelta<=0&&newDelta<=0)return 0;
  const dx=newDelta-oldDelta;
  if(Math.abs(dx)<1e-14)
   return this.feltScale*Math.max(0,.5*(oldDelta+newDelta))**this.feltExponent;
  return Math.max(0,(this.feltPotentialJ(newDelta)-
    this.feltPotentialJ(oldDelta))/dx);
 }
 totalEnergyJ(){
  let e=.5*this.hammerMassKg*this.vHammerMps**2;
  for(let j=0;j<this.n;j++)
   e+=.5*this.modalMassKg*this.v[j]**2+
    .5*this.modalStiffness[j]*this.q[j]**2;
  return e+this.feltPotentialJ(this.xHammerM-this.strikeDisplacementM());
 }
 relativeEnergyBalance(){
  return (this.totalEnergyJ()+this.dissipatedJ-this.initialEnergyJ)/
   Math.max(this.initialEnergyJ,1e-12);
 }
 bridgeShearForceN(){
  // The boundary shear is a mechanical force, NOT pressure at the ear.
  let force=0;
  for(let j=0;j<this.n;j++){
   const k=this.modeIndices[j]*Math.PI/this.lengthM;
   const sign=this.modeIndices[j]%2===0?1:-1;
   force+=sign*(this.tensionN*k+this.bendingRigidityNm2*k**3)*this.q[j];
  }
  return force;
 }
 step(){
  const h=this.dt,m=this.modalMassKg;
  let oldStrike=0,freeStrike=0,compliance=0;
  for(let j=0;j<this.n;j++){
   const phi=this.strikeShapes[j];
   const free=(m*this.v[j]-.5*h*this.modalStiffness[j]*this.q[j])*
    this.invDenom[j];
   this.freeV[j]=free;
   oldStrike+=phi*this.q[j];
   freeStrike+=phi*(this.q[j]+h*free);
   compliance+=.5*h*h*phi*phi*this.invDenom[j];
  }
  const oldH=this.xHammerM,oldHV=this.vHammerMps;
  const oldDelta=oldH-oldStrike;
  const freeDelta=oldH+h*oldHV-freeStrike;
  const inverseMobility=.5*h*h/this.hammerMassKg+compliance;
  let force=0;
  const upper=this.contactGradientN(oldDelta,freeDelta);
  if(upper>0){
   if(!Number.isFinite(upper)||upper>1e7)
    throw new RangeError('nonphysical felt compression');
   let lower=0,high=upper;
   for(let i=0;i<54;i++){
    const guess=.5*(lower+high);
    const current=freeDelta-inverseMobility*guess;
    const residual=guess-this.contactGradientN(oldDelta,current);
    if(residual>=0)high=guess;else lower=guess;
   }
   force=.5*(lower+high);
  }
  let dissipated=0;
  for(let j=0;j<this.n;j++){
   const mid=this.freeV[j]+.5*h*this.strikeShapes[j]*force*
    this.invDenom[j];
   this.midpointV[j]=mid;
   this.q[j]+=h*mid;this.v[j]=2*mid-this.v[j];
   dissipated+=h*this.modalDamping[j]*mid**2;
  }
  this.dissipatedJ+=dissipated;
  this.vHammerMps=oldHV-h*force/this.hammerMassKg;
  this.xHammerM=oldH+.5*h*(oldHV+this.vHammerMps);
  this.contactForceN=force;
  this.peakContactForceN=Math.max(this.peakContactForceN,force);
  if(force>0)this.contactSamples++;
  this.steps++;
  if(!Number.isFinite(this.xHammerM)||!Number.isFinite(this.vHammerMps)||
     !Number.isFinite(this.totalEnergyJ()))
   throw new RangeError('nonfinite single-string physical model');
  return this.bridgeShearForceN();
 }
}
