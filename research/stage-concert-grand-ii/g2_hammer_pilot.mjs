// G2.06a: isolated single-string hammer contact. No acoustic output.
// Discrete-gradient unilateral felt with rate-dependent dissipative factor.
import {StringPilot,pilotCutoffHz} from './g2_string_pilot.mjs';
import {feltPotential,feltSecant,solveContact} from '../stage-concert-grand/hammer-contact.mjs';
export const HAMMER=Object.freeze({massKg:.010,kNPerMPower:2e9,power:2.5,rateFactorSPerM:.12,gapM:.0002});
export const SPEEDS=Object.freeze([.5,1,2]);
export class HammerPilot {
 constructor(key,sr=48000,{speedMps=1,cutoffHz=pilotCutoffHz(key),params=HAMMER}={}){
  const {massKg,kNPerMPower,power,rateFactorSPerM,gapM}=params;
  if(![massKg,kNPerMPower,speedMps].every(v=>Number.isFinite(v)&&v>0)||!Number.isFinite(power)||power<1||power>5||!Number.isFinite(rateFactorSPerM)||rateFactorSPerM<0||!Number.isFinite(gapM)||gapM<0)throw RangeError('hammer parameters');
  this.string=new StringPilot(key,sr,{cutoffHz});this.h=1/sr;this.params={...params};this.x=-gapM;this.v=speedMps;this.contactLossJ=0;this.impulseNs=0;this.time=0;this.forceN=0;this.residualN=0;this.stepLossJ=0;
  this.g=this.h*this.h/(2*massKg)+this.string.modes.reduce((a,m,i)=>a+this.string.weights[i]**2*m.p.G,0);
 }
 compression(){return this.x-this.string.displacement();}
 energy(){const p=this.params;return .5*p.massKg*this.v**2+this.string.energy()+feltPotential(this.compression(),p.kNPerMPower,p.power);}
 step(){
  const {massKg:m,kNPerMPower:k,power:p,rateFactorSPerM:eta}=this.params,h=this.h,s=this.string,d0=this.compression();
  let xf=0;
  for(let i=0;i<s.modes.length;i++)xf+=s.weights[i]*s.modes[i].predict(0);
  const free=this.x+h*this.v-xf;
  const f=solveContact(d0,free,this.g,h,k,p,eta);
  this.x+=h*this.v-h*h*f/(2*m);this.v-=h*f/m;s.step(f);
  const d1=this.compression(),delta=d1-d0;
  const loss=f*delta-(feltPotential(d1,k,p)-feltPotential(d0,k,p));
  this.residualN=Math.abs(f-feltSecant(d0,d1,k,p)*Math.max(0,1+eta*delta/h));
  this.contactLossJ+=loss;this.stepLossJ=loss;this.impulseNs+=h*f;this.time+=h;this.forceN=f;
 }
}
