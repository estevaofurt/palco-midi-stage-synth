import {solidWire} from '../c3x-physical/c4-wire-consistency.mjs';
import {makeDesign} from './c4-design.mjs';
import {stringMode,spatialWeight} from './stiff-string.mjs';
import {MovingBridge} from './moving-bridge.mjs';
function checks(hp){
  const a=(v,m)=>{if(!v)throw Error(m)},near=(x,y,t)=>Math.abs(x-y)<t;
  const wires=[-.5,0,.5].map(c=>hp.makeDesign(hp.solidWire,{f1Hz:440*2**(-9/12+c/1200)}));
  const make=(o={},w=wires)=>new MovingBridge(w,o,hp);
  function run(rate,k=1e6,loss=true,cut=4000){
    const s=make({sampleRate:rate,bridgeK:k,maxFrequencyHz:cut,...(loss?{}:{bridgeC:0,sigma0:0,sigma2:0})});
    s.x[0]=1e-4;const initial=s.energy();let maxIncrease=0,maxResidual=0,maxBridge=0,maxOther=0,prev=initial,transferBack=0;
    for(let i=0;i<Math.round(.04*rate);i++){const before=s.wireEnergy(1);s.step();const e=s.energy();maxIncrease=Math.max(maxIncrease,e-prev);prev=e;maxResidual=Math.max(maxResidual,Math.abs(e+s.lossJ-initial));maxBridge=Math.max(maxBridge,Math.abs(s.b));maxOther=Math.max(maxOther,s.wireEnergy(1)+s.wireEnergy(2));transferBack=Math.max(transferBack,s.wireEnergy(1)-before);}
    return {rate,k,cut,initial,maxIncrease,maxResidual,maxBridge,maxOther,transferBack,bridgeLossJ:s.bridgeLossJ,stringLossJ:s.stringLossJ,energyJ:s.energy(),b:s.b,vb:s.vb,x0:s.x[0],v0:s.v[0],xOther:s.x[s.modes.findIndex(m=>m.j===1)],vOther:s.v[s.modes.findIndex(m=>m.j===1)]};
  }
  const results=[48000,96000,192000,384000].map(rate=>run(rate)),rigid=run(192000,1e14),lossless=run(96000,1e6,false);
  const s=make(),mobility=[100,200,261,262,300,500,1000,3000,8000,12000].map(f=>s.mobility(f));
  const ref=results.at(-1),errors=results.slice(0,-1).map(q=>({rate:q.rate,error:Math.hypot(q.x0-ref.x0,(q.v0-ref.v0)/1644,q.xOther-ref.xOther,(q.vOther-ref.vOther)/1644,q.b-ref.b,(q.vb-ref.vb)/1644)/1e-4}));
  // Static forcing: diagonal K in lifted coordinates, bridge force includes contact shape.
  const staticNet=make({maxFrequencyHz:4000});staticNet.b=.13/staticNet.kB;for(let i=0;i<staticNet.modes.length;i++){const m=staticNet.modes[i];if(m.j===0)staticNet.x[i]=m.weight/m.k;}
  const staticBefore=staticNet.contactDisplacement(0);staticNet.step([1,0,0]);
  const cases=[
    ['positive lifted mass matrix and step Schur',()=>a(s.massSchur>0&&s.schur>0,'SPD')],
    ['physical bridge and wire masses included',()=>a(near(s.mB,.025+wires.reduce((t,w)=>t+w.massKg/3,0),1e-15),'mass')],
    ['static lift stiffness equals tension over length',()=>a(near(s.kB,1e6+wires.reduce((t,w)=>t+w.tensionN/w.lengthM,0),1e-8),'K')],
    ['static equilibrium with distributed contact force',()=>a(near(staticNet.contactDisplacement(0),staticBefore,1e-15)&&Math.abs(staticNet.vb)<1e-12,'static')],
    ['zero state stays zero',()=>{const m=make();m.step();a(m.energy()===0,'zero')}],
    ['lossless coupled energy conserved',()=>a(lossless.maxResidual<1e-12&&lossless.maxIncrease<1e-12&&lossless.bridgeLossJ===0,'lossless')],
    ['damped network passive across rates',()=>a(results.every(q=>q.maxIncrease<1e-12&&q.maxResidual<1e-12&&q.bridgeLossJ>0&&q.stringLossJ>0),'passivity')],
    ['initial excitation transfers to initially idle strings',()=>a(results.every(q=>q.maxOther>1e-9&&q.transferBack>0&&q.maxBridge>0),'transfer')],
    ['rigid bridge limit suppresses motion and inter-string transfer',()=>a(rigid.maxBridge<results[2].maxBridge*.001&&rigid.maxOther<results[2].maxOther*.001,'rigid '+JSON.stringify(rigid))],
    ['forced system work balance',()=>{const m=make({maxFrequencyHz:4000});for(let i=0;i<500;i++)m.step([.1*Math.sin(i*.1),0,0],.02*Math.cos(i*.04));a(near(m.energy()+m.lossJ,m.workJ,1e-12),'work')}],
    ['reciprocity of wire contact response',()=>{const x=make({maxFrequencyHz:4000}),y=make({maxFrequencyHz:4000});for(let i=0;i<200;i++){const f=i<25?.1:0;x.step([f,0,0]);y.step([0,f,0]);a(near(x.contactDisplacement(1),y.contactDisplacement(0),1e-13),'reciprocity')}}],
    ['mobility positive real for damped model',()=>a(mobility.every(v=>v.real>=0&&Number.isFinite(v.magnitude)),'mobility')],
    ['refining timestep reduces state error',()=>a(errors[2].error<errors[1].error&&errors[1].error<errors[0].error,'refinement '+JSON.stringify(errors))],
    ['invalid parameter rejected',()=>{let bad=false;try{make({bridgeMassKg:-1})}catch(e){bad=true}a(bad,'invalid')}]
  ];
  for(const [n,f] of cases){try{f()}catch(e){throw Error(n+': '+e.message)}}
  return {passed:cases.map(c=>c[0]),modes:s.modes.length,bridgeMass:s.mB,bridgeK:s.kB,massSchur:s.massSchur,results,rigid,lossless,mobility,errors};
}
const result=checks({solidWire,makeDesign,stringMode,spatialWeight});for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));
