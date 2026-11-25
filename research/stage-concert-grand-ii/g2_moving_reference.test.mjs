import assert from 'node:assert/strict';
import {movingReference,denseStep,state,SUPPORT} from './g2_moving_reference.mjs';
import {PILOT_KEYS} from './g2_string_pilot.mjs';
import {LOSS_CASES} from './g2_decay.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
const parity=[],rows=[],reciprocity=[],convergence=[];
for(const key of PILOT_KEYS){
 // Small enough for independent dense oracle; same lifted physics.
 const b=movingReference(key,96000,{cutoffHz:4500}),n=b.wires.length;
 let maxX=0,maxV=0;
 for(let i=0;i<20;i++){
  const fv=Array.from({length:n},(_,j)=>.1*Math.sin(i*.3+j)),fh=Array.from({length:n},(_,j)=>.04*Math.cos(i*.2+j));
  const bv=.03*Math.sin(i*.4),bh=.02*Math.cos(i*.3),a=denseStep(b,fv,fh,bv,bh);b.step(fv,fh,bv,bh);const z=state(b);
  for(let j=0;j<z.x.length;j++){maxX=Math.max(maxX,Math.abs(a.x[j]-z.x[j]));maxV=Math.max(maxV,Math.abs(a.v[j]-z.v[j]));}
 }
 assert(maxX<1e-12&&maxV<1e-9);assert(Math.abs(b.energy()+b.lossJ-b.workJ)<1e-10);
 parity.push({key,maxX,maxV});
 // Reciprocal contact-to-contact and bridge-axis impulse response.
 const a=movingReference(key,192000),c=movingReference(key,192000),zero=Array(n).fill(0);let error=0,peak=0;
 for(let i=0;i<1920;i++){
  const f=i<40?.1*Math.sin(Math.PI*(i+.5)/40)**2:0;
  a.step([f,...zero.slice(1)],zero);c.step(zero,zero,0,f);
  error=Math.max(error,Math.abs(a.hAxis.b-c.contactDisplacement(0)));peak=Math.max(peak,Math.abs(a.hAxis.b));
 }
 assert(peak>0&&error<1e-12);
 reciprocity.push({key,error,peak});
}
function run(key,sr,lossId,support,id){
 const b=movingReference(key,sr,{loss:LOSS_CASES[lossId],support}),n=b.wires.length,z=Array(n).fill(0);
 b.vAxis.x[0]=1e-4;const E=b.energy();let maxInc=0,maxBalance=0,maxB=0,maxH=0,maxOther=0,minStringLoss=0,minBridgeLoss=0;
 const trace=[];
 for(let i=0;i<sr*.04;i++){
  const e=b.energy(),sl=b.stringLossJ,bl=b.bridgeLossJ;b.step(z,z);
  maxInc=Math.max(maxInc,b.energy()-e);maxBalance=Math.max(maxBalance,Math.abs(E-b.energy()-b.lossJ));
  minStringLoss=Math.min(minStringLoss,b.stringLossJ-sl);minBridgeLoss=Math.min(minBridgeLoss,b.bridgeLossJ-bl);
  maxB=Math.max(maxB,Math.abs(b.vAxis.b));maxH=Math.max(maxH,Math.abs(b.hAxis.b));maxOther=Math.max(maxOther,b.wireEnergy('v',1));
  if((i+1)%(sr/1000)===0)trace.push([b.vAxis.b,b.hAxis.b]);
 }
 assert(maxInc<=1e-12&&maxBalance<1e-10&&minStringLoss>=-1e-12&&minBridgeLoss>=-1e-12);
 assert(Math.abs(b.lossJ-b.stringLossJ-b.bridgeLossJ)<1e-10);
 if(id==='lossless')assert(Math.abs(b.energy()-E)<1e-10&&Math.abs(b.lossJ)<1e-10);
 else assert(b.stringLossJ>0&&b.bridgeLossJ>0);
 if(id==='normal')assert(maxB>0&&maxH>0&&maxOther>0);
 const mobility=[100,261,500,1046,3000,8000].map(f=>b.mobility(f));
 if(id==='normal')assert(mobility.every(m=>m.vv[0]>=-1e-12&&m.hh[0]>=-1e-12&&m.realDet>=-1e-12&&Number.isFinite(m.crossMagnitude)));
 const row={key,sr,lossId,id,E0:E,remainingJ:b.energy(),maxB,maxH,maxOther,maxBalance,maxInc,minStringLoss,minBridgeLoss,stringLossJ:b.stringLossJ,bridgeLossJ:b.bridgeLossJ,trace,mobility};rows.push(row);return row;
}
for(const key of PILOT_KEYS){
 for(const lossId of ['control','baseHalf']){
  const a=run(key,48000,lossId,SUPPORT,'normal'),b=run(key,96000,lossId,SUPPORT,'normal'),c=run(key,192000,lossId,SUPPORT,'normal'),d=run(key,384000,lossId,SUPPORT,'normal');
  const err=q=>Math.sqrt(q.trace.reduce((s,x,i)=>s+(x[0]-d.trace[i][0])**2+(x[1]-d.trace[i][1])**2,0)/d.trace.reduce((s,x)=>s+x[0]**2+x[1]**2,0));
  const errors=[a,b,c].map(err);
  // Fine reference must approach the finest trajectory; coarse errors are descriptive.
  assert(errors[2]<errors[1]);assert(errors[2]<.1);
  convergence.push({key,lossId,rates:[48000,96000,192000],errors});
 }
 const normal=rows.find(r=>r.key===key&&r.sr===192000&&r.lossId==='control'&&r.id==='normal');
 const rigid=run(key,192000,'control',{...SUPPORT,stiffness:[1e14,1e14]},'rigid');
 assert(rigid.maxB<normal.maxB*.01&&rigid.maxOther<normal.maxOther*.01);
 // lossless reference with explicitly zero local and support loss
 const b=movingReference(key,192000,{loss:{sigma0PerS:0,sigma2M2PerS:0},support:{...SUPPORT,damping:[0,0]}}),z=Array(b.wires.length).fill(0);
 b.vAxis.x[0]=1e-4;const E=b.energy();let maxBalance=0;
 for(let i=0;i<7680;i++){b.step(z,z);maxBalance=Math.max(maxBalance,Math.abs(b.energy()-E));}
 assert(maxBalance<1e-10&&Math.abs(b.lossJ)<1e-10);
 rows.push({key,id:'lossless',sr:192000,E0:E,remainingJ:b.energy(),maxBalance});
}
for(const r of rows.filter(x=>x.id==='normal'&&x.sr===192000))console.log('G2_MOVING '+JSON.stringify({...r,trace:undefined,mobility:undefined}));
for(const r of convergence)console.log('G2_MOVING_CONVERGENCE '+JSON.stringify(r));
mkdirSync('/tmp/g2-moving',{recursive:true});writeFileSync('/tmp/g2-moving/report.json',JSON.stringify({scope:'lifted midpoint offline physical control, not selected G2 exact modal production integrator; no sound pressure',parity,rows,reciprocity,convergence},null,2));
console.log('G2_MOVING_PASS '+JSON.stringify({physical:rows.length,dense:parity.length,reciprocity:reciprocity.length,convergence:convergence.length}));
