import assert from 'node:assert/strict';
import {makeProfileHammer} from './g2_hammer_profile.mjs';
import {PILOT_KEYS,StringPilot} from './g2_string_pilot.mjs';
import {SPEEDS} from './g2_hammer_pilot.mjs';
import {LOSS_CASES,cloneFree,exactFree,measureFree,envelopeT60} from './g2_decay.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
const rows=[],times=[0,.02,.08,.25,.5,1,2,3,5,10,15,20,25,30,35,40];
for(const key of PILOT_KEYS)for(const speed of SPEEDS){
 const h=makeProfileHammer(key,48000,{speedMps:speed});
 for(let i=0;i<1920;i++)h.step();
 assert(h.forceN===0&&h.compression()<0&&h.v<0);
 for(const [id,loss] of Object.entries(LOSS_CASES)){
  const q=cloneFree(h.string,loss),iter=cloneFree(h.string,loss),E0=q.energy();
  assert(Math.abs(E0-h.string.energy())<1e-12);
  let maxInc=0,maxX=0,maxV=0;
  for(let k=0;k<4800;k++){const before=iter.energy();iter.step(0);maxInc=Math.max(maxInc,iter.energy()-before);}
  for(let i=0;i<q.modes.length;i++){const a=exactFree(q.modes[i],.1),b=iter.modes[i];maxX=Math.max(maxX,Math.abs(a.x-b.x));maxV=Math.max(maxV,Math.abs(a.v-b.velocity()));}
  assert(maxInc<=1e-12&&maxX<1e-10&&maxV<1e-8);
  assert(Math.abs(E0-iter.energy()-iter.lossJ)<1e-10);
  const windows=times.map(t=>measureFree(q,t));
  for(let k=1;k<windows.length;k++)assert(windows[k].energyJ<=windows[k-1].energyJ+1e-12);
  for(const [i,m] of q.modes.entries()){const t=envelopeT60(m.sigma);const a=exactFree(m,t),amp=Math.hypot(m.x,m.y);if(amp>1e-30)assert(Math.abs(a.envelopeM/amp-.001)<1e-12);}
  const partials=q.info.slice(0,8).map((m,i)=>({n:m.n,fHz:m.frequencyHz,sigma:m.sigma,t60EnvelopeS:envelopeT60(m.sigma),energy0J:q.modes[i].energy()}));
  const at=t=>windows.find(w=>w.timeS===t).energyDb;
  const earlySlope=(at(3)-at(.25))/2.75,lateSlope=(at(30)-at(10))/20;
  rows.push({key,speed,id,loss,initialJ:E0,partials,windows,earlySlopeDbPerS:earlySlope,lateSlopeDbPerS:lateSlope,maxInc,maxX,maxV});
 }
}
assert.throws(()=>new StringPilot(60,48000,{sigma0PerS:-1}),/loss/);
assert.equal(envelopeT60(0),Infinity);
for(const r of rows.filter(x=>x.speed===1))console.log('G2_DECAY '+JSON.stringify({key:r.key,id:r.id,t60F1:r.partials[0].t60EnvelopeS,t60H4:r.partials[3].t60EnvelopeS,at3:r.windows.find(w=>w.timeS===3).energyDb,at15:r.windows.find(w=>w.timeS===15).energyDb,at30:r.windows.find(w=>w.timeS===30).energyDb,early:r.earlySlopeDbPerS,late:r.lateSlopeDbPerS}));
mkdirSync('/tmp/g2-decay',{recursive:true});writeFileSync('/tmp/g2-decay/report.json',JSON.stringify({scope:'mechanical free decay from matched physical state at 40ms; not sound pressure or audible sustain; elapsed time relative to detached state',rows},null,2));
console.log('G2_DECAY_PASS',rows.length);
