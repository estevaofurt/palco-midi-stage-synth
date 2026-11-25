// G2.08d: band convergence and bounded treble sensitivity, not voicing.
import assert from 'node:assert/strict';
import {IntegratedGroup} from './g2_integrated_group.mjs';
import {LOADS} from './g2_polar_port.mjs';
import {LOSS_CASES} from './g2_decay.mjs';
import {PILOT_KEYS,pilotCutoffHz} from './g2_string_pilot.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
const rows=[],checks=[],sensitivity=[];
function run(key,speed,lossId,cutoffHz,{id='base',massScale=1,stiffnessScale=1,loadId='rotated'}={}){
 const sr=96000,q=new IntegratedGroup(key,sr,{speedMps:speed,loss:LOSS_CASES[lossId],load:LOADS[loadId],cutoffHz,massScale,stiffnessScale}),E=q.energy(),n=q.force.length;
 const re=new Float64Array(n),im=new Float64Array(n),dc=new Float64Array(n);
 let peak=0,first=-1,last=-1,maxBalance=0,maxResidual=0,maxPortResidual=0,minFelt=0,minLocal=0,minLoad=0,open=false,atSeparation=null;
 for(let i=0;i<sr*.04;i++){
  const before=q.vertical.map((_,j)=>q.compression(j));q.step();let sum=0;
  for(let j=0;j<n;j++){
   const f=q.force[j],w=2*Math.PI*q.vertical[j].s.wire.f1Hz*(i+.5)/sr;
   assert(Number.isFinite(f)&&f>=0);if(before[j]<=0&&q.compression(j)<=0)assert.equal(f,0);
   re[j]+=f*Math.cos(w)/sr;im[j]+=f*Math.sin(w)/sr;dc[j]+=f/sr;sum+=f;
  }
  if(sum>1e-8){if(first<0)first=i;last=i;}
  if(first>=0&&sum<=1e-8&&q.v<0&&q.vertical.every((_,j)=>q.compression(j)<=0)){open=true;if(atSeparation===null)atSeparation={timeS:(i+1)/sr,energyJ:q.port.energy(),loadLossJ:q.loadLossJ,localLossJ:q.localLossJ};}
  peak=Math.max(peak,sum);maxBalance=Math.max(maxBalance,Math.abs(E-q.energy()-q.feltLossJ-q.localLossJ-q.loadLossJ));
  maxResidual=Math.max(maxResidual,q.residualN);maxPortResidual=Math.max(maxPortResidual,q.portResidualN);
  minFelt=Math.min(minFelt,q.stepFeltJ);minLocal=Math.min(minLocal,q.stepLocalJ);minLoad=Math.min(minLoad,q.stepLoadJ);
 }
 assert(open&&q.force.every(x=>x===0)&&q.vertical.every((_,j)=>q.compression(j)<0));
 assert(q.port.energy()>0&&minFelt>=-1e-11&&minLocal>=-1e-11&&minLoad>=-1e-12);
 assert(maxResidual<=1e-7*Math.max(1,peak)&&maxPortResidual<1e-7&&maxBalance<=Math.max(1e-10,E*1e-7));
 const stringJ=q.port.energy(),inputWorkJ=stringJ+q.localLossJ+q.loadLossJ;
 const forceF1Ratio=Array.from(re,(a,j)=>Math.hypot(a,im[j])/dc[j]);
 assert(forceF1Ratio.every(x=>Number.isFinite(x)&&x>=0&&x<=1+1e-12));
 return {key,sr,speed,lossId,cutoffHz,id,loadId,massScale,stiffnessScale,massKg:q.params.massKg,KPerContact:q.k,initialJ:E,peakForceN:peak,durationMs:(last-first+1)*1000/sr,impulseNs:q.impulseNs,stringJ,stringFraction:stringJ/E,inputWorkJ,inputFraction:inputWorkJ/E,loadLossJ:q.loadLossJ,feltLossJ:q.feltLossJ,localLossJ:q.localLossJ,forceF1Ratio,atSeparation,maxBalance,maxResidual,maxPortResidual};
}
for(const key of PILOT_KEYS)for(const lossId of ['control','baseHalf'])for(const speed of [.5,1,2]){
 const a=run(key,speed,lossId,pilotCutoffHz(key)),b=run(key,speed,lossId,20000);
 rows.push(a,b);
 const errors=Object.fromEntries(['peakForceN','impulseNs','stringJ','feltLossJ','loadLossJ'].map(k=>[k,Math.abs(a[k]-b[k])/Math.max(Math.abs(b[k]),1e-20)])),durationErrorMs=Math.abs(a.durationMs-b.durationMs);
 const r={key,speed,lossId,errors,durationErrorMs,pass:Object.values(errors).every(x=>x<=.1)&&durationErrorMs<=.1};checks.push(r);
 console.log('G2_INTEGRATED_BAND '+JSON.stringify(r));
}
const variants=[{id:'base'},{id:'massHalf',massScale:.5},{id:'mass150',massScale:1.5},{id:'soft',stiffnessScale:.75},{id:'firm',stiffnessScale:1.5},{id:'hard',stiffnessScale:3}];
for(const loadId of ['open','rotated'])for(const c of variants)for(const speed of [.5,1,2]){
 const r=run(84,speed,'control',pilotCutoffHz(84),{...c,loadId});sensitivity.push(r);
 if(speed===1)console.log('G2_TREBLE '+JSON.stringify(r));
}
mkdirSync('/tmp/g2-integrated-band',{recursive:true});writeFileSync('/tmp/g2-integrated-band/report.json',JSON.stringify({scope:'96k band convergence and OFAT C6 contact sensitivity; fixed supports, no sound pressure, no selection by energy',rows,checks,sensitivity},null,2));
console.log('G2_INTEGRATED_BAND_GATE '+JSON.stringify({physical:rows.length,sensitivity:sensitivity.length,comparisons:checks.length,passed:checks.filter(x=>x.pass).length}));
if(!checks.every(x=>x.pass))process.exitCode=1;
