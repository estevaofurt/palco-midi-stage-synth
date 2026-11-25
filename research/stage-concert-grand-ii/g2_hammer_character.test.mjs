import assert from 'node:assert/strict';
import {CANDIDATES,MemoryPilot} from './g2_hammer_character.mjs';
import {HammerPilot,SPEEDS} from './g2_hammer_pilot.mjs';
import {PILOT_KEYS} from './g2_string_pilot.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
const rows=[];
function run(key,v,c){
 const sr=96000,h=new (c.memory?MemoryPilot:HammerPilot)(key,sr,{speedMps:v,params:c.params,footprint:c.footprint}),E=h.energy();
 let peak=0,comp=0,first=-1,last=-1,res=0,balance=0,loss=0,active=0,rebound=false;
 for(let i=0;i<sr*.04;i++){
  const d0=h.compression();h.step();const f=h.forceN,d=h.compression();
  assert(Number.isFinite(f)&&f>=0);if(d0<=0&&d<=0)assert.equal(f,0);
  if(f>1e-8){if(first<0)first=i;last=i;active++;}
  if(first>=0&&f<=1e-8&&d<=0&&h.v<0)rebound=true;
  peak=Math.max(peak,f);comp=Math.max(comp,d);res=Math.max(res,h.residualN);
  balance=Math.max(balance,Math.abs(E-h.energy()-h.contactLossJ-h.string.lossJ));loss=Math.min(loss,h.stepLossJ);
 }
 assert(rebound&&first>=0&&h.forceN===0&&h.compression()<0);
 assert(res<=1e-7*Math.max(1,peak)&&loss>=-1e-11&&balance<=Math.max(1e-10,E*1e-7));
 assert(h.string.energy()>0&&h.contactLossJ>=-1e-11&&h.string.lossJ>=-1e-11);
 if(c.memory)assert(h.relaxResidualJ<1e-10);
 const modalEnergy=h.string.modes.map(m=>m.energy());
 const total=h.string.energy(),row={key,speed:v,id:c.id,massKg:h.params.massKg,K:h.params.kNPerMPower,widthM:h.string.widthM,strikeFraction:h.string.strikeFraction,initialJ:E,peakForceN:peak,compressionM:comp,spanMs:(last-first+1)*1000/sr,activeMs:active*1000/sr,impulseNs:h.impulseNs,stringEnergyJ:total,stringFraction:total/E,feltFraction:h.contactLossJ/E,fundamentalFraction:modalEnergy[0]/total,upperFraction:modalEnergy.slice(3).reduce((s,x)=>s+x,0)/total,modalEnergyJ:modalEnergy,balanceJ:balance,residualN:res,relaxResidualJ:h.relaxResidualJ??null};
 rows.push(row);return row;
}
for(const key of PILOT_KEYS)for(const c of CANDIDATES){
 const a=SPEEDS.map(v=>run(key,v,c));assert(a[0].peakForceN<a[1].peakForceN&&a[1].peakForceN<a[2].peakForceN);
}
for(const r of rows.filter(x=>x.speed===1))console.log('G2_HAMMER_CHARACTER '+JSON.stringify({...r,modalEnergyJ:undefined}));
mkdirSync('/tmp/g2-character',{recursive:true});writeFileSync('/tmp/g2-character/report.json',JSON.stringify({scope:'single-string OFAT sensitivity, same 96kHz and selected band, no acoustic or final mass/voicing claim',rows},null,2));
console.log('G2_CHARACTER_PASS',rows.length);
