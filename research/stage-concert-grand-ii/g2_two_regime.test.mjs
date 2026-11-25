import assert from 'node:assert/strict';
import {TwoRegimeProof,REGIMES} from './g2_two_regime.mjs';
import {PILOT_KEYS,wireFor} from './g2_string_pilot.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
const rows=[];
const times=[0,.02,.08,.25,.5,1,2,3,5,10,15,20,25,30,35,40];
for(const key of PILOT_KEYS)for(const sr of [48000,96000])for(const [id,config] of Object.entries(REGIMES)){
 const f=wireFor(key).f1Hz, q=new TwoRegimeProof(f,sr,config),iter=new TwoRegimeProof(f,sr,config),initial=q.sample(0),E0=q.energy();
 assert(Math.abs(initial.x-1e-4)<1e-15&&Math.abs(initial.energyJ-E0)<1e-15);
 let maxInc=0,maxX=0,maxE=0;
 for(let i=0;i<sr/5;i++){
  const e=iter.energy();iter.step();maxInc=Math.max(maxInc,iter.energy()-e);
  if((i+1)%(sr/100)===0){const t=(i+1)/sr,a=q.sample(t);maxX=Math.max(maxX,Math.abs(a.x-iter.projection()));maxE=Math.max(maxE,Math.abs(a.energyJ-iter.energy()));}
 }
 assert(maxInc<=1e-12&&maxX<1e-10&&maxE<1e-10);
 const windows=times.map(t=>{const a=q.sample(t);return {timeS:t,energyJ:a.energyJ,energyDb:10*Math.log10(a.energyJ/E0),envelopeDb:20*Math.log10(a.envelopeM/initial.envelopeM)};});
 for(let i=1;i<windows.length;i++)assert(windows[i].energyJ<=windows[i-1].energyJ+1e-12);
 const at=t=>windows.find(w=>w.timeS===t).envelopeDb;
 const early=(at(1)-at(.25))/.75,late=(at(30)-at(10))/20;
 if(id==='mixed'){assert(early<-5);assert(late>-2&&late<-1.5);assert(late-early>3);}
 else {const target=-20/Math.LN10*(id==='fastOnly'?config.fast:id==='slowOnly'?config.slow:config.fast);assert(Math.abs(early-target)<1e-8&&Math.abs(late-target)<1e-8);}
 const row={key,sr,id,config,earlySlopeDbPerS:early,lateSlopeDbPerS:late,windows,maxInc,maxX,maxE};rows.push(row);
 console.log('G2_TWO_REGIME '+JSON.stringify({key,sr,id,early,late,db3:at(3),db15:at(15),db30:at(30),maxInc,maxX,maxE}));
}
mkdirSync('/tmp/g2-two-regime',{recursive:true});writeFileSync('/tmp/g2-two-regime/report.json',JSON.stringify({scope:'abstract orthogonal dissipative modes with coherent displacement projection; no acoustic pressure, no real unison, no fitting',rows},null,2));
console.log('G2_TWO_REGIME_PASS',rows.length);
