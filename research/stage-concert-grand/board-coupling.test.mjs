import {solidWire} from '../c3x-physical/c4-wire-consistency.mjs';
import {makeDesign} from './c4-design.mjs';
import {stringMode,spatialWeight} from './stiff-string.mjs';
import {plateDesign,plateModes,patchWeight} from './orthotropic-plate.mjs';
import {ribDesign,ribbedModes} from './ribbed-plate.mjs';
import {PolarizedBridge,PolarizedHammer} from './polarized-bridge.mjs';
import {BoardPort,BoardCoupledBridge} from './board-coupling.mjs';
function checks(hp){
 const a=(v,m)=>{if(!v)throw Error(m)},p=hp.plateDesign(),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>hp.ribDesign(p,{xM})),patch={xM:.83,yM:.46,dxM:.04,dyM:.025};
 const wires=[-.5,0,.5].map(c=>hp.makeDesign(hp.solidWire,{f1Hz:440*2**(-9/12+c/1200)}));
 const basis=Object.fromEntries([1000,2000,4000].map(f=>[f,hp.ribbedModes(p,ribs,{basisHz:f},hp).modes]));
 const make=({rate=96000,basisHz=4000,boardCut=1000,jointK=1e7,jointC=1,loss=true}={})=>{
   const b=new hp.PolarizedBridge(wires,{sampleRate:rate,stiffness:[0,2e6],damping:loss?[0,5]:[0,0],...(loss?{}:{verticalLoss:[0,0],horizontalLoss:[0,0]})},hp);
   const board=new BoardPort(p,basis[basisHz].filter(m=>m.frequencyHz<boardCut),patch,b.h,loss?{}:{loss0:0,lossSlope:0},hp);
   return new BoardCoupledBridge(b,board,{jointK,jointC:loss?jointC:0});
 };
 const b=make(),f=[.1,.2,.3];b.bridge.vAxis.x[0]=1e-5;b.board.x[0]=1e-6;const G=b.contactCompliance(),pred=b.freeContacts().map((v,i)=>v+G[i].reduce((s,c,j)=>s+c*f[j],0));b.step(f);const affine=Math.max(...pred.map((v,i)=>Math.abs(v-b.contactDisplacement(i))));
 function impact(rate,velocity=1,opts={}){
  const b=make({rate,...opts}),m=new hp.PolarizedHammer(b,{velocityMps:velocity}),e0=m.energy();
  let peak=0,maxBoard=0,maxBridge=0,maxBalance=0,maxIncrease=0,prev=e0,res=0,last=0,maxWork=0,maxJoint=0;
  for(let i=0;i<Math.round(.012*rate);i++){
   const y=b.wires.map((_,j)=>b.contactDisplacement(j)),w=b.workJ,q=m.step(),e=m.energy();peak=Math.max(peak,q.sum);last=q.sum;maxBoard=Math.max(maxBoard,Math.abs(b.board.position()));maxBridge=Math.max(maxBridge,Math.abs(b.bridge.vAxis.b));maxJoint=Math.max(maxJoint,Math.abs(b.lastJointForce));maxBalance=Math.max(maxBalance,Math.abs(e+b.lossJ+m.lossJ-e0));maxIncrease=Math.max(maxIncrease,e-prev);prev=e;res=Math.max(res,m.lastResidual);const work=q.forces.reduce((s,f,j)=>s+f*(b.contactDisplacement(j)-y[j]),0);maxWork=Math.max(maxWork,Math.abs(b.workJ-w-work));
  }
  return {rate,velocity,opts,modeCount:b.board.modes.length,peak,maxBoard,maxBridge,maxJoint,boardEnergy:b.board.energy(),boardLoss:b.board.lossJ,boardWork:b.board.workJ,jointLoss:b.jointLossJ,maxBalance,maxIncrease,res,last,rebounce:m.v,maxWork,wireEnergy:wires.reduce((s,_,j)=>s+b.bridge.wireEnergy('v',j)+b.bridge.wireEnergy('h',j),0)};
 }
 function transfer(from,loss=true,jointK=1e7){
  const b=make({rate:48000,loss,jointK,jointC:jointK===0?0:1});
  if(from==='board')b.board.v[0]=Math.sqrt(2*24.935874721567115e-6);else b.bridge.vAxis.x[0]=1e-4;
  const e0=b.energy(),initialBoard=b.board.energy(),initialJoint=.5*b.k*b.relative()**2;let maxOther=0,maxBalance=0,maxIncrease=0,prev=e0;
  for(let i=0;i<4800;i++){b.step();const e=b.energy(),other=from==='board'?b.bridge.energy():b.board.energy();maxOther=Math.max(maxOther,other);maxBalance=Math.max(maxBalance,Math.abs(e+b.lossJ-e0));maxIncrease=Math.max(maxIncrease,e-prev);prev=e;}
  return {from,loss,jointK,e0,initialBoard,initialJoint,maxOther,maxBalance,maxIncrease,boardWork:b.board.workJ,boardLoss:b.board.lossJ};
 }
 const dyn=[.5,1,2.5].map(v=>impact(96000,v)),rates=[impact(48000),dyn[1],impact(192000)],enrich=[impact(96000,1,{basisHz:1000}),impact(96000,1,{basisHz:2000}),dyn[1]],band=[impact(96000,1,{boardCut:500}),dyn[1],impact(96000,1,{boardCut:1500})],trans=[transfer('wire'),transfer('board'),transfer('wire',false),transfer('wire',true,0)];
 const iso=make({jointK:0,jointC:0}),base=iso.bridge;const old=new hp.PolarizedBridge(wires,{sampleRate:96000,stiffness:[0,2e6],damping:[0,5]},hp);
 let parity=0;for(let i=0;i<200;i++){const f=[.1*Math.sin(i*.1),0,0];iso.step(f);old.step(f);parity=Math.max(parity,Math.abs(base.vAxis.b-old.vAxis.b),Math.abs(base.contactDisplacement(0)-old.contactDisplacement(0)));}
 const x=make(),y=make();let reciprocal=0;for(let i=0;i<200;i++){const f=i<20?.1:0;x.step([0,0,0],[0,0,0],f);y.step([0,0,0],[0,0,0],0,0,f);reciprocal=Math.max(reciprocal,Math.abs(x.board.position()-y.bridge.vAxis.b));}
 const forced=make();for(let i=0;i<300;i++)forced.step([.1*Math.sin(i*.1),0,0],[0,0,0],.02*Math.cos(i*.04),0,.03*Math.sin(i*.05));
 const workResidual=Math.abs(forced.energy()+forced.lossJ-forced.workJ);
 const all=[...dyn,...rates,...enrich,...band];
 const cases=[
 ['affine hammer contact prediction',()=>a(affine<1e-15,'affine')],
 ['reciprocal contact compliance',()=>a(G.every((row,i)=>row.every((v,j)=>v>=0&&Math.abs(v-G[j][i])<1e-18)),'G')],
 ['zero joint recovers bridge and silent board',()=>a(parity<1e-15&&iso.board.energy()===0,'parity')],
 ['wire excites board and board excites wire',()=>a(trans[0].maxOther>1e-12&&trans[1].maxOther>1e-12&&trans[1].initialBoard===trans[1].e0&&trans[1].initialJoint===0&&trans[3].maxOther===0,'transfer')],
 ['lossless coupled system conserves energy',()=>a(trans[2].maxBalance<1e-12&&trans[2].maxIncrease<1e-12,'lossless')],
 ['free coupled motion passive',()=>a(trans.every(q=>q.maxBalance<1e-12&&q.maxIncrease<1e-12),'passivity')],
 ['reciprocal bridge board port response',()=>a(reciprocal<1e-13,'reciprocal '+reciprocal)],
 ['external port work balances stored and lost energy',()=>a(workResidual<1e-12,'forced')],
 ['hammer impacts passive and contact solved',()=>a(all.every(q=>q.maxBalance<1e-10&&q.maxIncrease<1e-10&&q.res<1e-8&&q.maxWork<1e-12),'impact')],
 ['board receives work and dissipates energy',()=>a(all.every(q=>q.boardEnergy>0&&q.boardLoss>0&&Math.abs(q.boardEnergy+q.boardLoss-q.boardWork)<1e-12),'board')],
 ['hammer release and rebound',()=>a(all.every(q=>q.last===0&&q.rebounce<0),'release')],
 ['touch dynamics preserved',()=>a(dyn.slice(1).every((q,i)=>q.peak>dyn[i].peak&&q.maxBoard>dyn[i].maxBoard),'dynamics')],
 ['basis and band variation finite',()=>a([...enrich,...band].every(q=>q.modeCount>0&&Number.isFinite(q.maxBoard)),'band')],
 ['temporal peak refinement',()=>a(Math.abs(rates[1].peak-rates[2].peak)<Math.abs(rates[0].peak-rates[2].peak),'rates')]
 ];
 for(const [n,f] of cases){try{f()}catch(e){throw Error(n+': '+e.message)}}
 return {passed:cases.map(c=>c[0]),affine,reciprocal,parity,workResidual,dyn,rates,enrich,band,trans,gb:b.gb,gp:b.board.G};
}
const result=checks({solidWire,makeDesign,stringMode,spatialWeight,plateDesign,plateModes,patchWeight,ribDesign,ribbedModes,PolarizedBridge,PolarizedHammer});for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));
