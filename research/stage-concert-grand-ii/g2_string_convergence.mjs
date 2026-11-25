// G2.05b — compare identical continuous prescribed force on different grids and bands.
import assert from 'node:assert/strict';
import {StringPilot,PILOT_KEYS} from './g2_string_pilot.mjs';
import {stringMode,spatialWeight} from '../stage-concert-grand/stiff-string.mjs';
const OUT='/tmp/g2-string-convergence';
import {mkdirSync,writeFileSync} from 'node:fs';
const LIMITS=Object.freeze({xRel:.02,vRel:.05,workRel:.05,energyRel:.05,complianceRel:.02,peakXRel:.02});
const pulses=[{start:0,duration:.003,amplitude:.3},{start:.05,duration:.0015,amplitude:.15}];
function integral(t,p){
 const u=Math.max(0,Math.min(p.duration,t-p.start));
 return p.amplitude*(u/2-p.duration*Math.sin(2*Math.PI*u/p.duration)/(4*Math.PI));
}
function forceAverage(t0,t1){return pulses.reduce((a,p)=>a+(integral(t1,p)-integral(t0,p))/(t1-t0),0);}
function run(key,sr,cutoffHz){
 const s=new StringPilot(key,sr,{cutoffHz}), stride=sr/300, x=[],v=[];
 assert(Number.isInteger(stride));
 let peakX=0,peakV=0,minLoss=0;
 for(let i=0;i<sr*.2;i++){
  const e=s.energy(),w=s.workJ;
  s.step(forceAverage(i/sr,(i+1)/sr));
  const X=s.displacement(),V=s.velocity();
  peakX=Math.max(peakX,Math.abs(X));peakV=Math.max(peakV,Math.abs(V));
  minLoss=Math.min(minLoss,s.workJ-w+e-s.energy());
  if((i+1)%stride===0){x.push(X);v.push(V);}
 }
 assert(x.length===60&&v.length===60);
 const compliance=s.info.reduce((a,m,i)=>a+s.weights[i]**2/m.stiffnessNPerM,0);
 assert(s.lossJ>=0&&minLoss>=-1e-12&&Math.abs(s.workJ-s.lossJ-s.energy())<1e-10);
 return {key,sr,cutoffHz,modes:s.modes.length,x,v,peakX,peakV,work:s.workJ,energy:s.energy(),loss:s.lossJ,minLoss,compliance};
}
function rel(a,b){return Math.abs(a-b)/Math.max(Math.abs(b),1e-30);}
function relRms(a,b){return Math.sqrt(a.reduce((s,x,i)=>s+(x-b[i])**2,0)/Math.max(b.reduce((s,x)=>s+x*x,0),1e-60));}
function compare(a,b,kind){
 const errors={xRel:relRms(a.x,b.x),vRel:relRms(a.v,b.v),workRel:rel(a.work,b.work),energyRel:rel(a.energy,b.energy),complianceRel:rel(a.compliance,b.compliance),peakXRel:rel(a.peakX,b.peakX)};
 const failed=Object.keys(LIMITS).filter(k=>!Number.isFinite(errors[k])||errors[k]>LIMITS[k]);
 return {key:a.key,kind,candidate:{sr:a.sr,cutoffHz:a.cutoffHz,modes:a.modes},reference:{sr:b.sr,cutoffHz:b.cutoffHz,modes:b.modes},errors,failed,pass:failed.length===0};
}
const rows=[],summaries=[];
for(const key of PILOT_KEYS){
 const a=run(key,44100,12000),b=run(key,48000,12000),c=run(key,96000,12000),d=run(key,96000,16000),e=run(key,96000,20000),f=run(key,96000,8000);
 rows.push(compare(a,c,'time'),compare(b,c,'time'),compare(c,e,'band12'),compare(d,e,'band16'),compare(f,e,'band8'));
 for(const q of [a,b,c,d,e,f]){const {x,v,...summary}=q;summaries.push(summary);}
}
const result={scope:'prescribed smooth force, single polarization, fixed supports; common 300Hz snapshots plus native-rate peak and energy; not convergence of audio or hammer contact; 20k reference is finite',limits:LIMITS,rows,summaries,requiredPass:rows.filter(r=>['time','band12'].includes(r.kind)).every(r=>r.pass)};
mkdirSync(OUT,{recursive:true});writeFileSync(OUT+'/report.json',JSON.stringify(result,null,2));
for(const row of rows)console.log('G2_CONVERGENCE '+JSON.stringify(row));
console.log('G2_CONVERGENCE_GATE '+JSON.stringify({requiredPass:result.requiredPass,required:rows.filter(r=>['time','band12'].includes(r.kind)).length,passed:rows.filter(r=>['time','band12'].includes(r.kind)&&r.pass).length}));
if(!result.requiredPass)process.exitCode=1;
