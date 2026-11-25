import assert from 'node:assert/strict';
import {HammerPilot,HAMMER,SPEEDS} from './g2_hammer_pilot.mjs';
import {PILOT_KEYS,pilotCutoffHz} from './g2_string_pilot.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
const rows=[],checks=[];
function run(key,sr,speed,cutoffHz=pilotCutoffHz(key),params=HAMMER){
 const a=new HammerPilot(key,sr,{speedMps:speed,cutoffHz,params}),initial=a.energy();
 let peakForce=0,peakCompression=0,maxResidual=0,minLoss=0,maxBalance=0,first=-1,last=-1,openAfter=false,contactSteps=0,separationVelocity=null;
 for(let i=0;i<Math.round(sr*.04);i++){
  const before=a.compression();
  a.step();
  const after=a.compression(),f=a.forceN;
  assert(Number.isFinite(f)&&f>=0);
  if(before<=0&&after<=0)assert.equal(f,0);
  if(f>1e-8){if(first<0)first=i;last=i;contactSteps++;}
  if(first>=0&&f<=1e-8&&after<=0&&a.v<0){openAfter=true;if(separationVelocity===null)separationVelocity=a.v;}
  peakForce=Math.max(peakForce,f);peakCompression=Math.max(peakCompression,after);
  maxResidual=Math.max(maxResidual,a.residualN);minLoss=Math.min(minLoss,a.stepLossJ);
  maxBalance=Math.max(maxBalance,Math.abs(initial-a.energy()-a.contactLossJ-a.string.lossJ));
 }
 assert(peakForce>0&&peakCompression>0&&first>=0&&openAfter&&a.forceN===0&&a.compression()<0);
 assert(maxResidual<=1e-7*Math.max(1,peakForce));assert(minLoss>=-1e-11);
 assert(a.contactLossJ>=-1e-11&&a.string.lossJ>=-1e-11);assert(maxBalance<=Math.max(1e-10,initial*1e-7));
 assert(a.string.energy()>0);
 const row={key,sr,speed,cutoffHz,modes:a.string.modes.length,initialJ:initial,peakForceN:peakForce,peakCompressionM:peakCompression,contactSpanMs:(last-first+1)*1000/sr,activeContactMs:contactSteps*1000/sr,separationVelocityMps:separationVelocity,impulseNs:a.impulseNs,hammerFinalJ:.5*params.massKg*a.v*a.v,stringFinalJ:a.string.energy(),feltLossJ:a.contactLossJ,stringLossJ:a.string.lossJ,maxBalanceJ:maxBalance,maxResidualN:maxResidual,minStepFeltLossJ:minLoss};
 console.log('G2_HAMMER '+JSON.stringify(row));rows.push(row);return row;
}
for(const key of PILOT_KEYS){
 for(const sr of [44100,48000,96000]){
  const a=SPEEDS.map(v=>run(key,sr,v));
  assert(a[0].peakForceN<a[1].peakForceN&&a[1].peakForceN<a[2].peakForceN);
  assert(a[0].initialJ<a[1].initialJ&&a[1].initialJ<a[2].initialJ);
 }
 // Conservative elastic control: no artificial contact loss without eta.
 const c=run(key,96000,1,pilotCutoffHz(key),{...HAMMER,rateFactorSPerM:0});
 assert(Math.abs(c.feltLossJ)<1e-10);
}
function compare(a,b,kind){
 const metrics=['peakForceN','peakCompressionM','impulseNs','stringFinalJ','feltLossJ'];
 const errors=Object.fromEntries(metrics.map(k=>[k,Math.abs(a[k]-b[k])/Math.max(Math.abs(b[k]),1e-20)]));
 const durationErrorMs=Math.abs(a.contactSpanMs-b.contactSpanMs);
 const pass=Object.values(errors).every(x=>x<=.10)&&durationErrorMs<=.10;
 return {kind,key:a.key,speed:a.speed,fromRate:a.sr,toRate:b.sr,fromCutoff:a.cutoffHz,toCutoff:b.cutoffHz,errors,durationErrorMs,pass};
}
for(const key of PILOT_KEYS)for(const speed of SPEEDS){
 const a=rows.find(r=>r.key===key&&r.sr===44100&&r.speed===speed),b=rows.find(r=>r.key===key&&r.sr===48000&&r.speed===speed),c=rows.find(r=>r.key===key&&r.sr===96000&&r.speed===speed);
 checks.push(compare(a,c,'time'),compare(b,c,'time'));
 const d=run(key,96000,speed,20000);
 checks.push(compare(c,d,'band'));
}
for(const q of checks)console.log('G2_HAMMER_CONVERGENCE '+JSON.stringify(q));
const result={scope:'single string, diagnostic hammer parameters shared across registers, physical velocities not MIDI, no body or pressure',rows,checks,gate:checks.every(q=>q.pass)};
mkdirSync('/tmp/g2-hammer',{recursive:true});writeFileSync('/tmp/g2-hammer/report.json',JSON.stringify(result,null,2));
console.log('G2_HAMMER_GATE '+JSON.stringify({physicalCases:rows.length,convergenceCases:checks.length,passed:checks.filter(x=>x.pass).length,gate:result.gate}));
if(!result.gate)process.exitCode=1;
