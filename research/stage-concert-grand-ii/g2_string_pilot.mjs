// G2.05a: SI string pilot, no hammer, moving support, body or sound pressure.
import {bassCandidate} from '../stage-concert-grand/f11c-bass-candidates.mjs';
import {stringMode,spatialWeight} from '../stage-concert-grand/stiff-string.mjs';
import {PortMode} from './g2_arch_port.mjs';
export const PILOT_KEYS=Object.freeze([48,60,84]);
export const DESIGN=Object.freeze({cutoffHz:12000,maxModes:128,sigma0PerS:.4,sigma2M2PerS:.0002,strikeFraction:.13,widthM:.005});
export function wireFor(midi){
 if(!PILOT_KEYS.includes(midi))throw RangeError('pilot key');
 if(midi===48)return {...bassCandidate(midi),provenance:'G1 diagnostic wound anchor; not measured'};
 const lengthM=midi===60?.65:.18,diameterM=midi===60?.00096:.00080,youngPa=200e9,densityKgM3=7850;
 const areaM2=Math.PI*diameterM**2/4,linearDensityKgM=densityKgM3*areaM2,EI=youngPa*Math.PI*diameterM**4/64;
 const f1Hz=440*2**((midi-69)/12),tensionN=4*lengthM**2*linearDensityKgM*f1Hz**2-Math.PI**2*EI/lengthM**2;
 if(!(tensionN>0))throw Error('invalid candidate tension');
 return {midi,lengthM,diameterM,youngPa,densityKgM3,areaM2,linearDensityKgM,EI,tensionN,f1Hz,B:Math.PI**2*EI/(tensionN*lengthM**2),stressPa:tensionN/areaM2,provenance:midi===60?'G1 C4 control geometry':'G2 C6 original diagnostic geometry, not measured'};
}
export class StringPilot {
 constructor(midi,sr=48000,{cutoffHz=DESIGN.cutoffHz}={}){
  if(![44100,48000,96000].includes(sr))throw RangeError('rate');
  if(!Number.isFinite(cutoffHz)||cutoffHz<=0||cutoffHz>.4*sr)throw RangeError('cutoff');
  this.sr=sr;this.cutoffHz=cutoffHz;this.wire=wireFor(midi);this.modes=[];this.weights=[];this.info=[];
  const L=this.wire.lengthM;
  for(let n=1;n<=DESIGN.maxModes;n++){
   const m=stringMode(this.wire,n);
   if(m.frequencyHz>=cutoffHz)break;
   const sigma=DESIGN.sigma0PerS+DESIGN.sigma2M2PerS*m.waveNumber**2;
   this.modes.push(new PortMode({massKg:m.massKg,frequencyHz:m.frequencyHz,dampingNsM:2*m.massKg*sigma,dt:1/sr}));
   this.weights.push(spatialWeight(m,L,DESIGN.strikeFraction*L,DESIGN.widthM));this.info.push({...m,sigma});
  }
  if(!this.modes.length)throw Error('no modes');
  this.workJ=0;this.lossJ=0;
 }
 displacement(){let x=0;for(let i=0;i<this.modes.length;i++)x+=this.weights[i]*this.modes[i].x;return x;}
 velocity(){let v=0;for(let i=0;i<this.modes.length;i++)v+=this.weights[i]*this.modes[i].velocity();return v;}
 energy(){let e=0;for(const m of this.modes)e+=m.energy();return e;}
 step(forceN=0){
  if(!Number.isFinite(forceN))throw RangeError('force');
  const x0=this.displacement(),e0=this.energy();
  for(let i=0;i<this.modes.length;i++)this.modes[i].advance(forceN*this.weights[i]);
  const work=forceN*(this.displacement()-x0);this.workJ+=work;this.lossJ+=work+e0-this.energy();
 }
}
