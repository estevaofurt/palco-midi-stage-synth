import {polarizationLedger,validateAngle} from './f9-aftersound-ledger.mjs';
import {renderStringLoss} from './f9-string-loss.mjs';
import {stringLossCase} from './f9-string-loss-parameters.mjs';
import {renderUnison} from './f9-unison.mjs';
import {solidWire} from '../c3x-physical/c4-wire-consistency.mjs';
import {makeDesign} from './c4-design.mjs';
import {stringMode,spatialWeight} from './stiff-string.mjs';
import {plateDesign,plateModes,patchWeight} from './orthotropic-plate.mjs';
import {ribDesign,generalizedEigen} from './ribbed-plate.mjs';
import {mindlinModes} from './mindlin-plate.mjs';
import {PolarizedBridge,PolarizedHammer} from './polarized-bridge.mjs';
import {BoardCoupledBridge} from './board-coupling.mjs';
import {radiationGrid,surfaceShape,radiationKernel} from './surface-radiation.mjs';
import {ResistiveBoard} from './radiation-loading.mjs';
import {relaxMemory} from './felt-memory.mjs';
import {fft} from './f8-render.mjs';
const hp={fft,solidWire,makeDesign,stringMode,spatialWeight,plateDesign,plateModes,patchWeight,ribDesign,generalizedEigen,mindlinModes,PolarizedBridge,PolarizedHammer,BoardCoupledBridge,radiationGrid,surfaceShape,radiationKernel,ResistiveBoard,relaxMemory};
import {renderBassSupportTrial,SUPPORT_VARIANTS} from './f11o-bass-support-trial.mjs';
import {scanRadiation} from './f11m-radiated-mobility.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
const [out='f11o-support']=process.argv.slice(2);
const cases=[];let kernels=null,signature=null;
for(const midi of [36,43,48])for(const variant of Object.keys(SUPPORT_VARIANTS)){
 let joint=null;
 class Capture extends hp.BoardCoupledBridge{constructor(...a){super(...a);joint=this;}}
 const q=renderBassSupportTrial({...hp,BoardCoupledBridge:Capture},{midi,variant,midiVelocity:76,seconds:.05});
 if(!joint||q.meta.maxBalance>1e-9||q.meta.maxIncrease>1e-9)throw Error('capture');
 const sig=JSON.stringify(q.meta.boardSignature);
 if(signature!==null&&sig!==signature)throw Error('board changed');
 if(!kernels){
  const p=hp.plateDesign();
  kernels=[{x:.90,y:.38,z:1},{x:1.20,y:.38,z:1}].map(l=>{const grid=hp.radiationGrid(p,l,{nx:64,ny:50});return joint.board.modes.map(m=>hp.radiationKernel(grid,(x,y)=>hp.surfaceShape(m,x,y),48000));});
  signature=sig;
 }
 const f1=q.meta.wire.f1Hz,B=q.meta.wire.B;
 const bands=[1,2].map(h=>{
  const center=h*f1*Math.sqrt((1+B*h*h)/(1+B)),scan=scanRadiation(joint.bridge,joint.board,joint,kernels,center,80,.05);
  const samples=scan.samples.map(p=>({hz:p.f,cents:1200*Math.log2(p.f/center),pressure:p.magnitude}));
  const dominant=samples.reduce((a,b)=>b.pressure>a.pressure?b:a);
  const inside=samples.filter(p=>Math.abs(p.cents)<=5),outside=samples.filter(p=>Math.abs(p.cents)>5);
  if(!inside.length||!outside.length||samples.some(p=>!Number.isFinite(p.pressure)))throw Error('invalid scan');
  const near=Math.max(...inside.map(p=>p.pressure)),far=Math.max(...outside.map(p=>p.pressure));
  return {h,center,stepHz:scan.stepHz,dominant,near,far,offToNear:near>0?far/near:null,peaks:scan.peaks.map(p=>({hz:p.f,cents:p.cents,pressure:p.magnitude})),samples};
 });
 cases.push({midi,variant,support:q.meta.support,bands});
}
const summary=cases.map(c=>({midi:c.midi,variant:c.variant,bands:c.bands.map(b=>{
 const ref=cases.find(x=>x.midi===c.midi&&x.variant==='A').bands.find(x=>x.h===b.h);
 return {h:b.h,dominant:b.dominant,offToNear:b.offToNear,nearRatio:ref.near>0?b.near/ref.near:null,pass:Math.abs(b.dominant.cents)<=5&&ref.near>0&&b.near/ref.near>=.7};
})}));
const variants=Object.keys(SUPPORT_VARIANTS).map(variant=>({variant,passCount:summary.filter(c=>c.variant===variant).flatMap(c=>c.bands).filter(b=>b.pass).length,expected:6}));
mkdirSync(out,{recursive:true});
writeFileSync(out+'/support-screen.json',JSON.stringify({scope:'linear forced response only; thresholds are triage, not acoustic approval; pressure is not sustain',cases,summary,variants},null,2),{flag:'wx'});
console.log('F11O_SUPPORT_SCREEN '+JSON.stringify({summary,variants}));
