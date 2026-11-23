/**
 * E3.1 - sample-free nonlinear unilateral hammer/felt-string CONTACT CORE.
 * One simplified string coordinate only (no bridge / soundboard yet), intended
 * as a physics building block for replacing E2.3's prescribed sine pulse.
 *
 * Felt: F = k * max(x_hammer - x_string,0)^p, p>1, F>=0.
 * Stored contact energy = k * delta^(p+1)/(p+1).
 * Real parameters and effective string mass must still be identified; this
 * is NOT a finished piano or an integrated Stage D/AudioWorklet instrument.
 *
 * Velocity-Verlet (explicit) at 96kHz with frequency/force ceilings. No
 * audio samples and no oscillator added at the output. Model is unforced
 * after initial hammer launch, with string viscous damping >=0.
 */
const TAU=2*Math.PI;
export class NonlinearFeltContactPair {
 constructor({sampleRate=96000,hammerMassKg=.008,stringEffectiveMassKg=.004,
  stringFrequencyHz=130.8128,feltStiffness=1e10,feltExponent=2.3,
  hammerGapM=.0004,hammerInitialVelocityMps=2,stringLossRate=0}={}){
  if(!Number.isInteger(sampleRate)||sampleRate<48000||sampleRate>192000||
     !Number.isFinite(hammerMassKg)||hammerMassKg<=0||hammerMassKg>.1||
     !Number.isFinite(stringEffectiveMassKg)||stringEffectiveMassKg<=0||stringEffectiveMassKg>.1||
     !Number.isFinite(stringFrequencyHz)||stringFrequencyHz<25||stringFrequencyHz>1000||
     !Number.isFinite(feltStiffness)||feltStiffness<=0||feltStiffness>1e12||
     !Number.isFinite(feltExponent)||feltExponent<1.1||feltExponent>4||
     !Number.isFinite(hammerGapM)||hammerGapM<0||hammerGapM>.01||
     !Number.isFinite(hammerInitialVelocityMps)||hammerInitialVelocityMps<0||hammerInitialVelocityMps>10||
     !Number.isFinite(stringLossRate)||stringLossRate<0||stringLossRate>15)
   throw new RangeError('invalid nonlinear contact physics');
  this.dt=1/sampleRate;this.sampleRate=sampleRate;
  this.hammerMassKg=hammerMassKg;this.stringEffectiveMassKg=stringEffectiveMassKg;
  this.stringSpringNpm=stringEffectiveMassKg*(TAU*stringFrequencyHz)**2;
  this.stringLossNspm=2*stringEffectiveMassKg*stringLossRate;
  this.feltStiffness=feltStiffness;this.feltExponent=feltExponent;
  this.hammerPositionM=-hammerGapM;this.stringPositionM=0;
  this.hammerVelocityMps=hammerInitialVelocityMps;this.stringVelocityMps=0;
  this.contactForceN=0;this.maxForceN=0;
  this.contactSamples=0;this.dissipatedJ=0;this.sampleCount=0;
  this.initialEnergyJ=this.energy();
 }
 force(){
  const penetration=this.hammerPositionM-this.stringPositionM;
  return penetration>0?this.feltStiffness*penetration**this.feltExponent:0;
 }
 energy(){
  const compression=Math.max(0,this.hammerPositionM-this.stringPositionM);
  return .5*this.hammerMassKg*this.hammerVelocityMps**2+
   .5*this.stringEffectiveMassKg*this.stringVelocityMps**2+
   .5*this.stringSpringNpm*this.stringPositionM**2+
   this.feltStiffness*compression**(this.feltExponent+1)/(this.feltExponent+1);
 }
 step(){
  const h=this.dt,oldForce=this.force();
  const oldStringAcc=(oldForce-this.stringSpringNpm*this.stringPositionM-
    this.stringLossNspm*this.stringVelocityMps)/this.stringEffectiveMassKg;
  const vh=this.hammerVelocityMps-.5*h*oldForce/this.hammerMassKg;
  const vs=this.stringVelocityMps+.5*h*oldStringAcc;
  this.hammerPositionM+=h*vh;
  this.stringPositionM+=h*vs;
  const nextForce=this.force();
  const stringAcc=(nextForce-this.stringSpringNpm*this.stringPositionM-
    this.stringLossNspm*vs)/this.stringEffectiveMassKg;
  this.hammerVelocityMps=vh-.5*h*nextForce/this.hammerMassKg;
  this.stringVelocityMps=vs+.5*h*stringAcc;
  this.contactForceN=nextForce;
  if(nextForce>0)this.contactSamples++;
  this.maxForceN=Math.max(this.maxForceN,nextForce);
  this.dissipatedJ+=h*this.stringLossNspm*vs*vs;
  this.sampleCount++;
  if(!Number.isFinite(this.hammerVelocityMps)||
      !Number.isFinite(this.stringVelocityMps)||
      !Number.isFinite(this.stringPositionM)||
      nextForce>1e8)
   throw new RangeError('unstable nonlinear hammer contact');
  return nextForce;
 }
 balanceRelativeError(){
  return (this.energy()+this.dissipatedJ-this.initialEnergyJ)/
   Math.max(this.initialEnergyJ,1e-12);
 }
}
