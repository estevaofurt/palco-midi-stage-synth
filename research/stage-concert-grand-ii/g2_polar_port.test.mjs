import assert from 'node:assert/strict';
import {PolarPort,LOADS} from './g2_polar_port.mjs';
import {GroupHammer} from './g2_group_hammer.mjs';
import {PILOT_KEYS} from './g2_string_pilot.mjs';
import {LOSS_CASES,exactFree} from './g2_decay.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
const rows=[],transfers=[];
for(const key of PILOT_KEYS)for(const sr of [48000,96000]){
 const group=new GroupHammer(key,sr,{speedMps:1,spreadCents:.5});
 for(let i=0;i<sr*.04;i++)group.step();
 assert(group.force.every(f=>f===0)&&group.strings.every((_,j)=>group.compression(j)<0));
 for(const lossId of ['control','baseHalf'])for(const [id,load] of Object.entries(LOADS)){
  const q=new PolarPort(group,LOSS_CASES[lossId],load),E0=q.energy();
  assert(Math.abs(E0-group.stringEnergy())<1e-12);
  let maxBalance=0,maxStepBalance=0,minLocal=0,minLoad=0,maxIncrease=0,peakHorizontal=0,maxOpenX=0,maxOpenV=0;
  const start=q.axes[0].map(z=>z.s.modes.map(m=>exactFree(m,.25)));
  for(let i=0;i<sr*.25;i++){
   const e=q.energy(),r=q.step();maxStepBalance=Math.max(maxStepBalance,Math.abs(r));
   maxBalance=Math.max(maxBalance,Math.abs(E0-q.energy()-q.localLossJ-q.loadLossJ));
   minLocal=Math.min(minLocal,q.stepLocalJ);minLoad=Math.min(minLoad,q.stepLoadJ);
   maxIncrease=Math.max(maxIncrease,q.energy()-e);peakHorizontal=Math.max(peakHorizontal,q.axisEnergy(1));
  }
  assert(maxBalance<1e-10&&maxStepBalance<1e-12&&minLocal>=-1e-12&&minLoad>=-1e-12&&maxIncrease<=1e-12);
  assert(q.maxPortResidualN<1e-7);
  if(id==='open'){
   assert(q.loadLossJ===0);
   for(let j=0;j<start.length;j++)for(let i=0;i<start[j].length;i++){
    const a=start[j][i],b=q.axes[0][j].s.modes[i];maxOpenX=Math.max(maxOpenX,Math.abs(a.x-b.x));maxOpenV=Math.max(maxOpenV,Math.abs(a.v-b.velocity()));
   }
   assert(maxOpenX<1e-10&&maxOpenV<1e-8);
  }else assert(q.loadLossJ>0);
  if(id==='rotated')assert(peakHorizontal/E0>1e-10);else assert(peakHorizontal===0);
  const r={key,sr,lossId,id,E0,remainingJ:q.energy(),verticalJ:q.axisEnergy(0),horizontalJ:q.axisEnergy(1),peakHorizontalFraction:peakHorizontal/E0,loadFraction:q.loadLossJ/E0,localFraction:q.localLossJ/E0,maxBalance,maxStepBalance,minLocal,minLoad,maxIncrease,maxPortResidualN:q.maxPortResidualN,maxOpenX,maxOpenV};rows.push(r);
  if(sr===48000)console.log('G2_POLAR '+JSON.stringify(r));
 }
 // Independent reciprocal transfer proof: excite only string 0 / vertical fundamental.
 for(const id of ['open','aligned','rotated']){
  const q=new PolarPort(group,LOSS_CASES.control,LOADS[id]);
  for(const axis of q.axes)for(const z of axis)for(const m of z.s.modes)m.init(0,0);
  q.axes[0][0].s.modes[0].init(1e-4,0);
  const E0=q.energy();let other=0,horizontal=0;
  for(let i=0;i<sr*.1;i++){
   q.step();other=Math.max(other,q.axes[0][1].s.energy()/E0);horizontal=Math.max(horizontal,q.axisEnergy(1)/E0);
  }
  assert(Math.abs(E0-q.energy()-q.localLossJ-q.loadLossJ)<1e-10);
  if(id==='open')assert(other===0&&horizontal===0);else assert(other>1e-10);
  if(id==='rotated')assert(horizontal>1e-10);else assert(horizontal===0);
  transfers.push({key,sr,id,otherPeakFraction:other,horizontalPeakFraction:horizontal});
 }
}
for(const r of transfers)console.log('G2_POLAR_TRANSFER '+JSON.stringify(r));
assert.throws(()=>new PolarPort(new GroupHammer(60),LOSS_CASES.control,{strong:-1,weak:0,angle:0}),/passive/);
mkdirSync('/tmp/g2-polar',{recursive:true});writeFileSync('/tmp/g2-polar/report.json',JSON.stringify({scope:'post-strike fixed-support string modes with reciprocal dissipative internal port, no moving boundary or acoustic output',rows,transfers},null,2));
console.log('G2_POLAR_PASS '+JSON.stringify({physical:rows.length,transfer:transfers.length}));
