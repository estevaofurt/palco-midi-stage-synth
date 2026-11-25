// G2.09c independent lifted midpoint hammer oracle, no acoustic output.
import {movingReference} from './g2_moving_reference.mjs';
import {PILOT_KEYS} from './g2_string_pilot.mjs';
import {LOSS_CASES} from './g2_decay.mjs';
import {profileFor} from './g2_hammer_profile.mjs';
import {feltPotential,feltSecant,solveContact} from '../stage-concert-grand/hammer-contact.mjs';
import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
const rows=[];
for(const key of PILOT_KEYS)for(const lossId of ['control','baseHalf'])for(const speed of [.5,1,2])for(const sr of [192000,384000]){
 const b=movingReference(key,sr,{loss:LOSS_CASES[lossId]}),h=b.h,n=b.wires.length,p=profileFor(key),k=p.kNPerMPower/n,hm=h*h/(2*p.massKg),C=b.contactCompliance().map(r=>r.map(x=>x+hm)),z=Array(n).fill(0);
 let x=-p.gapM,v=speed,loss=0,impulse=0,peak=0,first=-1,last=-1,maxBalance=0,maxResidual=0, minLoss=0;
 const E0=.5*p.massKg*v*v,compression=()=>z.map((_,j)=>x-b.contactDisplacement(j)),energy=()=>.5*p.massKg*v*v+b.energy()+compression().reduce((s,d)=>s+feltPotential(d,k,p.power),0);
 const trace=[];
 for(let i=0;i<sr*.04;i++){
  const d0=compression(),free=b.freeContacts().map(y=>x+h*v-y),f=z.slice();
  const law=(j,d)=>feltSecant(d0[j],d,k,p.power)*Math.max(0,1+p.rateFactorSPerM*(d-d0[j])/h);
  const residual=()=>Math.max(...f.map((a,j)=>Math.abs(a-law(j,free[j]-C[j].reduce((s,c,l)=>s+c*f[l],0)))));
  if(!free.every((d,j)=>law(j,d)===0)){
   let ok=false;
   for(let t=0;t<128;t++){
    for(let j=0;j<n;j++)f[j]=solveContact(d0[j],free[j]-C[j].reduce((s,c,l)=>s+(l===j?0:c*f[l]),0),C[j][j],h,k,p.power,p.rateFactorSPerM);
    if(residual()<1e-9){ok=true;break;}
   }
   assert(ok,'oracle contact');
  }
  const sum=f.reduce((s,a)=>s+a,0);x+=h*v-hm*sum;v-=h*sum/p.massKg;b.step(f,z);const d1=compression();
  let dl=0;
  for(let j=0;j<n;j++){assert(f[j]>=0&&Number.isFinite(f[j]));if(d0[j]<=0&&d1[j]<=0)assert.equal(f[j],0);dl+=f[j]*(d1[j]-d0[j])-feltPotential(d1[j],k,p.power)+feltPotential(d0[j],k,p.power);maxResidual=Math.max(maxResidual,Math.abs(f[j]-law(j,d1[j])));}
  loss+=dl;minLoss=Math.min(minLoss,dl);impulse+=h*sum;peak=Math.max(peak,sum);
  if(sum>1e-8){if(first<0)first=i;last=i;}
  maxBalance=Math.max(maxBalance,Math.abs(E0-energy()-loss-b.lossJ));
  if((i+1)%(sr/1000)===0)trace.push([b.vAxis.b,b.hAxis.b,...z.map((_,j)=>b.contactDisplacement(j))]);
 }
 assert(first>=0&&v<0&&compression().every(d=>d<0));assert(maxBalance<1e-10&&minLoss>=-1e-11&&maxResidual<=1e-7*Math.max(1,peak));
 const row={key,lossId,speed,sr,peak,impulse,duration:(last-first+1)*1000/sr,mechanicalJ:b.energy(),feltJ:loss,structuralJ:b.lossJ,initialJ:E0,maxBalance,maxResidual,trace};
 rows.push(row);console.log('G2_MOVING_HAMMER_REF '+JSON.stringify({...row,trace:undefined}));
}
writeFileSync('/tmp/g2-modal-bridge/hammer_reference.json',JSON.stringify(rows));
