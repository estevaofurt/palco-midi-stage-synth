// G2.08a: shared hammer, 1–3 strings, fixed supports; no bridge or acoustic output.
import {StringPilot,pilotCutoffHz} from './g2_string_pilot.mjs';
import {profileFor} from './g2_hammer_profile.mjs';
import {feltPotential,feltSecant,solveContact} from '../stage-concert-grand/hammer-contact.mjs';
export const GROUP_COUNT=Object.freeze({48:2,60:3,84:3});
export function offsets(n,spread){return n===1?[0]:n===2?[-spread,spread]:[-spread,0,spread];}
export class GroupHammer {
 constructor(key,sr=48000,{speedMps=1,count=GROUP_COUNT[key],spreadCents=.5,cutoffHz=pilotCutoffHz(key)}={}){
  if(![1,2,3].includes(count)||!Number.isFinite(spreadCents)||spreadCents<0||spreadCents>2||!Number.isFinite(speedMps)||speedMps<=0)throw RangeError('group');
  this.h=1/sr;this.params=profileFor(key);this.x=-this.params.gapM;this.v=speedMps;
  this.k=this.params.kNPerMPower/count;this.strings=offsets(count,spreadCents).map(cents=>new StringPilot(key,sr,{cutoffHz,cents}));
  this.g=this.strings.map(s=>s.modes.reduce((a,m,i)=>a+s.weights[i]**2*m.p.G,0));
  this.force=new Float64Array(count);this.contactLossJ=0;this.stepLossJ=0;this.residualN=0;this.impulseNs=0;
 }
 compression(i){return this.x-this.strings[i].displacement();}
 stringEnergy(){return this.strings.reduce((s,q)=>s+q.energy(),0);}
 stringLoss(){return this.strings.reduce((s,q)=>s+q.lossJ,0);}
 energy(){return .5*this.params.massKg*this.v**2+this.stringEnergy()+this.strings.reduce((s,_,i)=>s+feltPotential(this.compression(i),this.k,this.params.power),0);}
 step(){
  const h=this.h,{massKg:m,power:p,rateFactorSPerM:eta}=this.params,hm=h*h/(2*m),d0=this.strings.map((_,i)=>this.compression(i));
  const free=this.strings.map(s=>this.x+h*this.v-s.modes.reduce((sum,q,j)=>sum+s.weights[j]*q.predict(0),0));
  const law=(i,total)=>solveContact(d0[i],free[i]-hm*total,this.g[i],h,this.k,p,eta);
  // Same direct scalar solve as single-string baseline; for shared hammer solve total force then each contact.
  let sum=0;
  if(this.strings.length===1){this.force[0]=solveContact(d0[0],free[0],this.g[0]+hm,h,this.k,p,eta);sum=this.force[0];}
  else {
   let lo=0,hi=free.reduce((a,_,i)=>a+law(i,0),0);
   if(hi===0)this.force.fill(0);
   else {
    for(let j=0;j<40;j++){const mid=(lo+hi)/2,q=free.reduce((a,_,i)=>a+law(i,mid),0);if(mid>q)hi=mid;else lo=mid;}
    const mid=(lo+hi)/2;for(let i=0;i<this.force.length;i++){this.force[i]=law(i,mid);sum+=this.force[i];}
   }
  }
  this.x+=h*this.v-hm*sum;this.v-=h*sum/m;let loss=0,res=0;
  for(let i=0;i<this.strings.length;i++){
   const f=this.force[i];this.strings[i].step(f);const d1=this.compression(i),delta=d1-d0[i],u=feltPotential(d1,this.k,p)-feltPotential(d0[i],this.k,p);
   loss+=f*delta-u;res=Math.max(res,Math.abs(f-feltSecant(d0[i],d1,this.k,p)*Math.max(0,1+eta*delta/h)));
  }
  this.stepLossJ=loss;this.contactLossJ+=loss;this.residualN=res;this.impulseNs+=h*sum;
 }
}
