import assert from 'node:assert/strict';
import {GroupHammer,GROUP_COUNT} from './g2_group_hammer.mjs';
import {makeProfileHammer} from './g2_hammer_profile.mjs';
import {PILOT_KEYS} from './g2_string_pilot.mjs';
import {stringMode} from '../stage-concert-grand/stiff-string.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
const rows=[],checks=[];
for(const key of PILOT_KEYS){
 const a=new GroupHammer(key,48000,{count:1,speedMps:1}),b=makeProfileHammer(key,48000,{speedMps:1});
 for(let i=0;i<1920;i++){a.step();b.step();assert(Math.abs(a.force[0]-b.forceN)<1e-8);assert(Math.abs(a.x-b.x)<1e-10);assert(Math.abs(a.v-b.v)<1e-8);assert(Math.abs(a.energy()-b.energy())<1e-10);}
}
function run(key,sr,speed,spread){
 const a=new GroupHammer(key,sr,{speedMps:speed,spreadCents:spread}),E0=a.energy();
 let peak=0,first=-1,last=-1,minLoss=0,maxBalance=0,maxResidual=0,open=false,maxSymmetry=0;
 for(const s of a.strings){assert(Math.abs(1200*Math.log2(stringMode(s.wire,1).frequencyHz/s.wire.f1Hz))<1e-8);}
 for(let i=0;i<sr*.04;i++){
  const d0=a.strings.map((_,j)=>a.compression(j));a.step();let sum=0;
  for(let j=0;j<a.force.length;j++){const f=a.force[j];assert(Number.isFinite(f)&&f>=0);if(d0[j]<=0&&a.compression(j)<=0)assert.equal(f,0);sum+=f;if(spread===0)maxSymmetry=Math.max(maxSymmetry,Math.abs(f-a.force[0]));}
  if(sum>1e-8){if(first<0)first=i;last=i;}
  if(first>=0&&sum<=1e-8&&a.v<0&&a.strings.every((_,j)=>a.compression(j)<=0))open=true;
  peak=Math.max(peak,sum);minLoss=Math.min(minLoss,a.stepLossJ);maxResidual=Math.max(maxResidual,a.residualN);
  maxBalance=Math.max(maxBalance,Math.abs(E0-a.energy()-a.contactLossJ-a.stringLoss()));
 }
 assert(open&&a.force.every(x=>x===0)&&a.strings.every((_,j)=>a.compression(j)<0));
 assert(a.strings.every(s=>s.energy()>0&&s.lossJ>=-1e-11));assert(a.contactLossJ>=-1e-11&&minLoss>=-1e-11);
 assert(maxResidual<=1e-7*Math.max(1,peak)&&maxBalance<=Math.max(1e-10,E0*1e-7));
 if(spread===0){assert(maxSymmetry<1e-9);assert(a.strings.every(s=>Math.abs(s.energy()-a.strings[0].energy())<1e-12));}
 const row={key,sr,speed,spread,count:a.strings.length,frequencies:a.strings.map(s=>s.wire.f1Hz),cents:a.strings.map(s=>s.cents),peakForceN:peak,durationMs:(last-first+1)*1000/sr,impulseNs:a.impulseNs,initialJ:E0,stringJ:a.stringEnergy(),feltLossJ:a.contactLossJ,stringLossJ:a.stringLoss(),perStringJ:a.strings.map(s=>s.energy()),maxBalance,maxResidual,maxSymmetry};
 rows.push(row);return row;
}
for(const key of PILOT_KEYS)for(const spread of [0,.5]){
 for(const speed of [.5,1,2]){
  const a=run(key,48000,speed,spread),b=run(key,96000,speed,spread);
  const errors=Object.fromEntries(['peakForceN','impulseNs','stringJ','feltLossJ'].map(k=>[k,Math.abs(a[k]-b[k])/Math.max(Math.abs(b[k]),1e-20)])),durationErrorMs=Math.abs(a.durationMs-b.durationMs);
  checks.push({key,speed,spread,errors,durationErrorMs,pass:Object.values(errors).every(x=>x<=.1)&&durationErrorMs<=.1});
 }
 for(const sr of [48000,96000]){const r=rows.filter(x=>x.key===key&&x.spread===spread&&x.sr===sr);assert(r[0].peakForceN<r[1].peakForceN&&r[1].peakForceN<r[2].peakForceN);}
}
for(const r of rows.filter(x=>x.sr===48000&&x.speed===1))console.log('G2_GROUP '+JSON.stringify(r));
for(const r of checks)console.log('G2_GROUP_CONVERGENCE '+JSON.stringify(r));
mkdirSync('/tmp/g2-group',{recursive:true});writeFileSync('/tmp/g2-group/report.json',JSON.stringify({scope:'shared hammer, fixed supports, hypothetical string counts and split stiffness; no bridge, polarization or audio',rows,checks},null,2));
console.log('G2_GROUP_GATE '+JSON.stringify({singleParity:3,physicalCases:rows.length,convergence:checks.length,passed:checks.filter(x=>x.pass).length}));
if(!checks.every(x=>x.pass))process.exitCode=1;
