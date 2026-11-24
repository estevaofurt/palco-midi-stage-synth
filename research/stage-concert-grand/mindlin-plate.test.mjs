import {plateDesign,plateModes,patchWeight} from './orthotropic-plate.mjs';
import {ribDesign,ribbedModes,ribbedPatchWeight,generalizedEigen} from './ribbed-plate.mjs';
import {BoardPort,BoardCoupledBridge} from './board-coupling.mjs';
import {PolarizedBridge,PolarizedHammer} from './polarized-bridge.mjs';
import {stringMode,spatialWeight} from './stiff-string.mjs';
import {makeDesign} from './c4-design.mjs';
import {solidWire} from '../c3x-physical/c4-wire-consistency.mjs';
import {mindlinModes} from './mindlin-plate.mjs';
function study(hp){
 const a=(x,msg)=>{if(!x)throw Error(msg)},p=hp.plateDesign(),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>hp.ribDesign(p,{xM})),patch={xM:.83,yM:.46,dxM:.04,dyM:.025};
 const build=(cut,rs=ribs,o={})=>mindlinModes(p,rs,{basisHz:cut,...o},hp);
 const old=hp.ribbedModes(p,ribs,{basisHz:4000},hp),ref=build(4000),sets=[build(500),build(1000),build(2000),ref];
 const bare=build(4000,[]),base=hp.plateModes(p,4000);
 const comparison=[1,10,30,60,100,200,300,400].map(i=>({rank:i,kirchhoff:old.modes[i-1].frequencyHz,mindlin:ref.modes[i-1].frequencyHz,deltaPct:100*(ref.modes[i-1].frequencyHz/old.modes[i-1].frequencyHz-1)}));
 const bands=[250,500,1000,1500,2000,4000].map(cut=>({cut,old:old.modes.filter(m=>m.frequencyHz<cut).length,new:ref.modes.filter(m=>m.frequencyHz<cut).length}));
 const convergence=sets.map(s=>({basis:s.basisCount,residual:s.residual,orthogonality:s.orthogonality,first:s.modes[0].frequencyHz,maxFirst10Pct:100*Math.max(...s.modes.slice(0,10).map((q,i)=>Math.abs(q.frequencyHz/ref.modes[i].frequencyHz-1))),count1k:s.modes.filter(m=>m.frequencyHz<1000).length}));
 const weight=m=>hp.ribbedPatchWeight(p,m,patch,hp.patchWeight);
 const compliance=sets.map(s=>({basis:s.basisCount,flex:s.modes.reduce((v,m)=>v+weight(m)**2/m.lambda,0)}));
 const shear=[.5,1,2].map(s=>{const q=build(2000,ribs,{GyzPa:.06e9*s});return {GyzGPa:.06*s,first:q.modes[0].frequencyHz,rank60:q.modes[59].frequencyHz,count1k:q.modes.filter(m=>m.frequencyHz<1000).length};});
 const port=new hp.BoardPort(p,ref.modes.filter(m=>m.frequencyHz<1500),patch,1/96000,{},hp);let maxIncrease=0,prev=0;
 for(let i=0;i<1200;i++){const f=i<48?.1*Math.sin(Math.PI*i/48):0;port.step(f);const e=port.energy();if(i>=48)maxIncrease=Math.max(maxIncrease,e-prev);prev=e;}
 const portResidual=Math.abs(port.energy()+port.lossJ-port.workJ);
 const limit=build(500,[],{shearScale:100,rotaryScale:.01}),kl=hp.plateModes(p,500);
 const limitErr=Math.max(...kl.slice(0,10).map((m,i)=>Math.abs(limit.modes[i].frequencyHz/m.frequencyHz-1)));
 const cases=[
 ['three fields per original sine pair',()=>a(ref.modes.length===3*ref.basisCount,'count')],
 ['positive eigenfrequencies',()=>a(ref.modes.every(m=>m.lambda>0&&Number.isFinite(m.frequencyHz)),'positive')],
 ['mass normalization and eigen residual',()=>a([...sets,bare].every(s=>s.residual<1e-6&&s.orthogonality<1e-9),'eigen '+JSON.stringify(convergence))],
 ['low shear-free thin limit reproduces Kirchhoff',()=>a(limitErr<.001,'limit '+limitErr)],
 ['bare bending modes below thin plate variational bound',()=>a(base.every((q,i)=>bare.modes[i].frequencyHz<=q.frequencyHz*(1+1e-8)),'bare bound')],
 ['reinforced eigenvalues below constrained Kirchhoff model',()=>a(old.modes.every((q,i)=>ref.modes[i].frequencyHz<=q.frequencyHz*(1+1e-8)),'rib bound')],
 ['nested Ritz basis eigenvalues nonincreasing',()=>a(sets.slice(1).every((s,i)=>sets[i].modes.every((q,j)=>s.modes[j].frequencyHz<=q.frequencyHz*(1+1e-7))),'nested')],
 ['static flexibility nondecreasing under enrichment',()=>a(compliance.slice(1).every((q,i)=>q.flex>=compliance[i].flex-1e-14),'flex')],
 ['greater transverse shear stiffness does not lower eigenvalues',()=>a(shear[0].first<=shear[1].first&&shear[1].first<=shear[2].first&&shear[0].rank60<=shear[1].rank60&&shear[1].rank60<=shear[2].rank60,'shear')],
 ['existing F6.3 board port accepts mass-normalized modes',()=>a(port.energy()>0&&port.lossJ>0&&portResidual<1e-12&&maxIncrease<1e-14,'port')],
 ['invalid shear rejected',()=>{let bad=false;try{build(500,ribs,{GyzPa:0})}catch(e){bad=true}a(bad,'invalid')}]
 ];
 for(const [n,f] of cases){try{f()}catch(e){throw Error(n+': '+e.message)}}
 return {passed:cases.map(c=>c[0]),comparison,bands,convergence,compliance,shear,limitErr,portResidual,maxIncrease,portModes:port.modes.length};
}
const result=study({plateDesign,plateModes,patchWeight,ribDesign,ribbedModes,ribbedPatchWeight,generalizedEigen,BoardPort});for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));

function integration(hp){
 const p=hp.plateDesign(),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>hp.ribDesign(p,{xM})),patch={xM:.83,yM:.46,dxM:.04,dyM:.025},wires=[-.5,0,.5].map(c=>hp.makeDesign(hp.solidWire,{f1Hz:440*2**(-9/12+c/1200)}));
 const mind=hp.mindlinModes(p,ribs,{basisHz:4000},hp),old=hp.ribbedModes(p,ribs,{basisHz:4000},hp);
 function impact(modes,cut,rate){
   const bridge=new hp.PolarizedBridge(wires,{sampleRate:rate,stiffness:[0,2e6],damping:[0,5]},hp);
   const board=new hp.BoardPort(p,modes.filter(q=>q.frequencyHz<cut),patch,bridge.h,{},hp),b=new hp.BoardCoupledBridge(bridge,board),hammer=new hp.PolarizedHammer(b);
   const initial=hammer.energy();let peak=0,maxBoard=0,residual=0,maxIncrease=0,prev=initial,last=0,forceRes=0;
   for(let i=0;i<Math.round(.012*rate);i++){const s=hammer.step(),e=hammer.energy();peak=Math.max(peak,s.sum);last=s.sum;maxBoard=Math.max(maxBoard,Math.abs(board.position()));residual=Math.max(residual,Math.abs(e+b.lossJ+hammer.lossJ-initial));maxIncrease=Math.max(maxIncrease,e-prev);prev=e;forceRes=Math.max(forceRes,hammer.lastResidual);}
   return {cut,rate,count:board.modes.length,peak,maxBoard,energy:board.energy(),loss:board.lossJ,residual,maxIncrease,forceRes,last,rebounce:hammer.v};
 }
 const prior=impact(old.modes,1000,96000),results=[impact(mind.modes,1000,96000),impact(mind.modes,1500,96000),impact(mind.modes,2000,96000),impact(mind.modes,1500,192000)];
 const a=(v,m)=>{if(!v)throw Error(m)};
 a(Math.abs(prior.energy-0.0003504097047942483)<1e-12,'F6.3 parity');
 a(results.every(q=>q.residual<1e-10&&q.maxIncrease<1e-10&&q.forceRes<1e-8&&q.energy>0&&q.last===0&&q.rebounce<0),'coupled dynamics');
 return {passed:2,prior,results};
}
const coupled=integration({PolarizedBridge,PolarizedHammer,plateDesign,plateModes,patchWeight,ribDesign,ribbedModes,ribbedPatchWeight,generalizedEigen,BoardPort,BoardCoupledBridge,mindlinModes,stringMode,spatialWeight,makeDesign,solidWire});console.log('PASS F6.3 parity');console.log('PASS full coupled Mindlin impact');console.log(JSON.stringify(coupled,null,2));
