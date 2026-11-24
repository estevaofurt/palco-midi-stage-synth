import {solidWire} from '../c3x-physical/c4-wire-consistency.mjs';
import {makeDesign} from './c4-design.mjs';
import {stringMode,spatialWeight} from './stiff-string.mjs';
import {plateDesign,plateModes,patchWeight} from './orthotropic-plate.mjs';
import {ribDesign,generalizedEigen} from './ribbed-plate.mjs';
import {mindlinModes} from './mindlin-plate.mjs';
import {PolarizedBridge,PolarizedHammer} from './polarized-bridge.mjs';
import {BoardPort,BoardCoupledBridge} from './board-coupling.mjs';
import {radiationGrid,surfaceShape,radiationKernel} from './surface-radiation.mjs';
import {pressureTrace} from './vibroacoustic-observer.mjs';
import {radiationResistance,ResistiveBoard} from './radiation-loading.mjs';
function checks(hp){
 const a=(v,m)=>{if(!v)throw Error(m)},p=hp.plateDesign(),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>hp.ribDesign(p,{xM})),patch={xM:.83,yM:.46,dxM:.04,dyM:.025},wires=[-.5,0,.5].map(c=>hp.makeDesign(hp.solidWire,{f1Hz:440*2**(-9/12+c/1200)}));
 const basis=hp.mindlinModes(p,ribs,{basisHz:4000},hp).modes,ms=basis.filter(m=>m.frequencyHz<1500),listener={x:1.05,y:.38,z:1};
 const R=radiationResistance(p,ms.slice(0,8),261.63),diag=R.map((row,i)=>row[i]),psdMin=Math.min(...Array.from({length:64},(_,i)=>{const v=R.map((_,j)=>Math.sin((i+1)*(j+1)));return v.reduce((s,x,j)=>s+x*R[j].reduce((t,y,k)=>t+y*v[k],0),0);}));
 const angular=[6,12,24].map(nt=>radiationResistance(p,ms.slice(0,8),261.63,{nt,np:2*nt})[0][0]);
 const onShell=[0,9,29,59,99,139].map(i=>({rank:i+1,f:ms[i].frequencyHz,R:radiationResistance(p,[ms[i]],ms[i].frequencyHz)[0][0]}));
 function run(rate,cut=1500,scale=1,duration=.024){
  const modes=basis.filter(m=>m.frequencyHz<cut),bridge=new hp.PolarizedBridge(wires,{sampleRate:rate,stiffness:[0,2e6],damping:[0,5]},hp),board=new ResistiveBoard(p,modes,patch,bridge.h,{radiation:{scale}},hp),b=new hp.BoardCoupledBridge(bridge,board),hammer=new hp.PolarizedHammer(b);
  const steps=Math.round(rate*duration),factor=rate/48000,trace=modes.map(()=>new Float64Array(steps/factor)),v0=new Float64Array(modes.length),initial=hammer.energy();let maxBalance=0,maxIncrease=0,prev=initial,peak=0,last=0;
  for(let i=0;i<steps;i++){v0.set(board.v);const s=hammer.step(),e=hammer.energy();peak=Math.max(peak,s.sum);last=s.sum;maxBalance=Math.max(maxBalance,Math.abs(e+b.lossJ+hammer.lossJ-initial));maxIncrease=Math.max(maxIncrease,e-prev);prev=e;
   for(let j=0;j<modes.length;j++)trace[j][Math.floor(i/factor)]+=(board.v[j]-v0[j])*48000;
  }
  const pressure=hp.pressureTrace(p,modes,trace,48000,listener,{nx:48,ny:38},hp);
  return {rate,cut,scale,count:modes.length,peak,maxBalance,maxIncrease,last,boardEnergy:board.energy(),radiationLoss:board.radiationLossJ,structuralLoss:board.structuralLossJ,boardResidual:Math.abs(board.energy()+board.lossJ-board.workJ),peakPa:pressure.reduce((s,v)=>Math.max(s,Math.abs(v)),0),pressure};
 }
 const cases=[run(96000),run(192000),run(192000,2000),run(192000,3000),run(96000,1500,0)];
 const err=(x,y)=>Math.sqrt(x.reduce((s,v,i)=>s+(v-y[i])**2,0)/y.reduce((s,v)=>s+v*v,0));
 const old=new hp.BoardPort(p,ms,patch,1/96000,{},hp),zero=new ResistiveBoard(p,ms,patch,1/96000,{radiation:{scale:0}},hp);let parity=0;
 for(let i=0;i<256;i++){const f=.1*Math.sin(i*.1);old.step(f);zero.step(f);parity=Math.max(parity,Math.abs(old.position()-zero.position()));}
 const b=new ResistiveBoard(p,ms,patch,1/96000,{},hp);b.x[0]=1e-5;b.v[2]=.01;const predicted=b.free()+b.G*.2;b.step(.2);const affine=Math.abs(predicted-b.position());
 const decay=new ResistiveBoard(p,ms,patch,1/48000,{},hp);decay.v[0]=.01;const initial=decay.energy();let maxIncrease=0,prev=initial;for(let i=0;i<4800;i++){decay.step(0);const e=decay.energy();maxIncrease=Math.max(maxIncrease,e-prev);prev=e;}
 const tests=[
 ['radiation Gram matrix symmetric and PSD sampled vectors',()=>a(psdMin>=-1e-12&&R.every((row,i)=>row.every((v,j)=>v===R[j][i]))&&diag.every(v=>v>=0),'PSD')],
 ['angular quadrature refinement',()=>a(Math.abs(angular[1]/angular[2]-1)<.03,'angular')],
 ['on shell resistance finite positive',()=>a(onShell.every(q=>q.R>0&&Number.isFinite(q.R)),'onshell')],
 ['zero loading matches original BoardPort',()=>a(parity<1e-13&&zero.radiationLossJ===0,'parity')],
 ['loaded board affine port response',()=>a(affine<1e-15,'affine '+affine)],
 ['free loaded board dissipates and balances',()=>a(maxIncrease<1e-12&&decay.radiationLossJ>0&&Math.abs(decay.energy()+decay.lossJ-initial)<1e-12,'decay')],
 ['full hammer system passive with separate losses',()=>a(cases.every(q=>q.maxBalance<1e-10&&q.maxIncrease<1e-10&&q.boardResidual<1e-12&&q.radiationLoss>=0&&q.structuralLoss>=0&&q.last===0),'coupled '+JSON.stringify(cases.map(({pressure,...q})=>q)))],
 ['loaded impacts have nonzero radiative work',()=>a(cases.slice(0,4).every(q=>q.radiationLoss>0)&&cases[4].radiationLoss===0,'loading')],
 ['pressure comparisons finite',()=>a([err(cases[0].pressure,cases[1].pressure),err(cases[1].pressure,cases[2].pressure),err(cases[2].pressure,cases[3].pressure)].every(Number.isFinite),'pressure')]
 ];
 for(const [n,f] of tests){try{f()}catch(e){throw Error(n+': '+e.message)}}
 return {passed:tests.map(t=>t[0]),angular,onShell,psdMin,parity,affine,decay:{initial,final:decay.energy(),rad:decay.radiationLossJ,structural:decay.structuralLossJ},cases:cases.map(({pressure,...q})=>q),timeError:err(cases[0].pressure,cases[1].pressure),bandErrors:[err(cases[1].pressure,cases[2].pressure),err(cases[2].pressure,cases[3].pressure)],loadError:err(cases[0].pressure,cases[4].pressure)};
}
const result=checks({solidWire,makeDesign,stringMode,spatialWeight,plateDesign,plateModes,patchWeight,ribDesign,generalizedEigen,mindlinModes,PolarizedBridge,PolarizedHammer,BoardPort,BoardCoupledBridge,radiationGrid,surfaceShape,radiationKernel,pressureTrace});for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));
