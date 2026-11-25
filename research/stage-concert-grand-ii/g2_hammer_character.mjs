// G2.06b: isolated sensitivity experiment; diagnostic parameters, not final voicing.
import {HammerPilot,HAMMER} from './g2_hammer_pilot.mjs';
import {memoryEnergy,relaxMemory,frozenMemoryForce,solveFrozen} from '../stage-concert-grand/felt-memory.mjs';
export class MemoryPilot extends HammerPilot {
 constructor(key,sr,options={}){
  super(key,sr,options);const p=this.params;
  this.felt={ke:.7*p.kNPerMPower,km:.3*p.kNPerMPower,kr:1000,viscosity:1,power:p.power};
  this.z=0;this.relaxResidualJ=0;
 }
 energy(){return .5*this.params.massKg*this.v**2+this.string.energy()+memoryEnergy(this.compression(),this.z,this.felt);}
 step(){
  const h=this.h,m=this.params.massKg,s=this.string,p=this.felt,d0=this.compression();
  const a=relaxMemory(d0,this.z,h/2,p);this.z=a.z;
  let xf=0;for(let i=0;i<s.modes.length;i++)xf+=s.weights[i]*s.modes[i].predict(0);
  const f=solveFrozen(d0,this.x+h*this.v-xf,this.g,this.z,p);
  this.x+=h*this.v-h*h*f/(2*m);this.v-=h*f/m;s.step(f);
  const d1=this.compression();
  this.residualN=Math.abs(f-frozenMemoryForce(d0,d1,this.z,p));
  const b=relaxMemory(d1,this.z,h/2,p);this.z=b.z;
  this.stepLossJ=a.lossJ+b.lossJ;this.contactLossJ+=this.stepLossJ;
  this.relaxResidualJ=Math.max(this.relaxResidualJ,Math.abs(a.residualJ),Math.abs(b.residualJ));
  this.impulseNs+=h*f;this.time+=h;this.forceN=f;
 }
}
export const CANDIDATES=Object.freeze([
 {id:'base',params:HAMMER},
 {id:'mass6',params:{...HAMMER,massKg:.006}},
 {id:'mass12',params:{...HAMMER,massKg:.012}},
 {id:'soft',params:{...HAMMER,kNPerMPower:HAMMER.kNPerMPower*.75}},
 {id:'firm',params:{...HAMMER,kNPerMPower:HAMMER.kNPerMPower*1.5}},
 {id:'hard',params:{...HAMMER,kNPerMPower:HAMMER.kNPerMPower*3}},
 {id:'width2',params:HAMMER,footprint:{widthM:.002}},
 {id:'width8',params:HAMMER,footprint:{widthM:.008}},
 {id:'position08',params:HAMMER,footprint:{strikeFraction:.08}},
 {id:'memory',params:HAMMER,memory:true},
]);
