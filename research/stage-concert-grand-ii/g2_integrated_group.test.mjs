import assert from 'node:assert/strict';
import {IntegratedGroup} from './g2_integrated_group.mjs';
import {GroupHammer} from './g2_group_hammer.mjs';
import {LOADS} from './g2_polar_port.mjs';
import {LOSS_CASES} from './g2_decay.mjs';
import {PILOT_KEYS} from './g2_string_pilot.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
const rows=[],checks=[],parities=[],tails=[];
for(const key of PILOT_KEYS){
 const a=new IntegratedGroup(key,48000,{load:LOADS.open}),b=new GroupHammer(key,48000);
 let f=0,x=0,v=0;
 for(let i=0;i<1920;i++){a.step();b.step();f=Math.max(f,...Array.from(a.force,(q,j)=>Math.abs(q-b.force[j])));x=Math.max(x,Math.abs(a.x-b.x));v=Math.max(v,Math.abs(a.v-b.v));}
 assert(f<1e-7&&x<1e-10&&v<1e-8);assert(a.loadLossJ===0&&a.port.axisEnergy(1)===0);
 parities.push({key,f,x,v});
}
function run(key,sr,speed,lossId){
 const q=new IntegratedGroup(key,sr,{speedMps:speed,loss:LOSS_CASES[lossId],load:LOADS.rotated}),E=q.energy();
 let peak=0,first=-1,last=-1,minFelt=0,minLocal=0,minLoad=0,maxBalance=0,maxResidual=0,maxPortResidual=0,maxSweeps=0,open=false,peakHorizontal=0;
 for(let i=0;i<sr*.04;i++){
  const d0=q.vertical.map((_,j)=>q.compression(j));q.step();let sum=0;
  for(let j=0;j<q.force.length;j++){const f=q.force[j];assert(Number.isFinite(f)&&f>=0);if(d0[j]<=0&&q.compression(j)<=0)assert.equal(f,0);sum+=f;}
  if(sum>1e-8){if(first<0)first=i;last=i;}
  if(first>=0&&sum<=1e-8&&q.v<0&&q.vertical.every((_,j)=>q.compression(j)<=0))open=true;
  peak=Math.max(peak,sum);minFelt=Math.min(minFelt,q.stepFeltJ);minLocal=Math.min(minLocal,q.stepLocalJ);minLoad=Math.min(minLoad,q.stepLoadJ);
  maxResidual=Math.max(maxResidual,q.residualN);maxPortResidual=Math.max(maxPortResidual,q.portResidualN);maxSweeps=Math.max(maxSweeps,q.sweeps);
  maxBalance=Math.max(maxBalance,Math.abs(E-q.energy()-q.feltLossJ-q.localLossJ-q.loadLossJ));
  peakHorizontal=Math.max(peakHorizontal,q.port.axisEnergy(1));
 }
 assert(open&&q.force.every(x=>x===0)&&q.vertical.every((_,j)=>q.compression(j)<0));
 assert(q.port.energy()>0&&q.loadLossJ>0&&peakHorizontal>0);
 assert(minFelt>=-1e-11&&minLocal>=-1e-11&&minLoad>=-1e-12);
 assert(maxResidual<=1e-7*Math.max(1,peak)&&maxPortResidual<1e-7&&maxBalance<=Math.max(1e-10,E*1e-7));
 const r={key,sr,speed,lossId,initialJ:E,peakForceN:peak,durationMs:(last-first+1)*1000/sr,impulseNs:q.impulseNs,stringJ:q.port.energy(),horizontalJ:q.port.axisEnergy(1),feltLossJ:q.feltLossJ,loadLossJ:q.loadLossJ,localLossJ:q.localLossJ,maxBalance,maxResidual,maxPortResidual,maxSweeps};
 rows.push(r);
 if(sr===48000&&speed===1){
  const initial=q.port.energy(),windows=[{timeS:0,energyDb:0,horizontalFraction:q.port.axisEnergy(1)/initial}];
  let maxTailIncrease=0;
  for(let i=0;i<sr*.25;i++){
   const prev=q.port.energy();q.step();assert(q.force.every(x=>x===0));maxTailIncrease=Math.max(maxTailIncrease,q.port.energy()-prev);
   if((i+1)%(sr/20)===0)windows.push({timeS:(i+1)/sr,energyDb:10*Math.log10(q.port.energy()/initial),horizontalFraction:q.port.axisEnergy(1)/initial});
  }
  assert(maxTailIncrease<=1e-12);assert(Math.abs(E-q.energy()-q.feltLossJ-q.localLossJ-q.loadLossJ)<1e-10);
  tails.push({key,lossId,windows,maxTailIncrease});
  console.log('G2_INTEGRATED '+JSON.stringify(r));
 }
 return r;
}
for(const key of PILOT_KEYS)for(const lossId of ['control','baseHalf']){
 for(const speed of [.5,1,2]){
  const a=run(key,48000,speed,lossId),b=run(key,96000,speed,lossId);
  const errors=Object.fromEntries(['peakForceN','impulseNs','stringJ','feltLossJ','loadLossJ'].map(k=>[k,Math.abs(a[k]-b[k])/Math.max(Math.abs(b[k]),1e-20)])),durationErrorMs=Math.abs(a.durationMs-b.durationMs);
  checks.push({key,speed,lossId,errors,durationErrorMs,pass:Object.values(errors).every(x=>x<=.1)&&durationErrorMs<=.1});
 }
 for(const sr of [48000,96000]){const a=rows.filter(r=>r.key===key&&r.lossId===lossId&&r.sr===sr);assert(a[0].peakForceN<a[1].peakForceN&&a[1].peakForceN<a[2].peakForceN);}
}
for(const r of checks)console.log('G2_INTEGRATED_CONVERGENCE '+JSON.stringify(r));
for(const r of tails)console.log('G2_INTEGRATED_TAIL '+JSON.stringify(r));
mkdirSync('/tmp/g2-integrated',{recursive:true});writeFileSync('/tmp/g2-integrated/report.json',JSON.stringify({scope:'continuous hammer plus diagnostic reciprocal internal load, fixed supports, no sound pressure',rows,checks,parities,tails},null,2));
console.log('G2_INTEGRATED_GATE '+JSON.stringify({physical:rows.length,parity:parities.length,convergence:checks.length,passed:checks.filter(r=>r.pass).length,tails:tails.length}));
if(!checks.every(r=>r.pass))process.exitCode=1;
