import {polarizationLedger,validateAngle} from './f9-aftersound-ledger.mjs';
import {writeFileSync,mkdirSync} from 'node:fs';
import {compareBlocks,resistancePower,dbRatio} from './f9-radiation-load-audit.mjs';
import {boardMobility} from './f9-loaded-mobility.mjs';
import {modalBoardResponse,complexSurface,pressureResponse,responseDifference} from './f9-radiation-convergence.mjs';
import {boardResolution,resolutionMetrics} from './f9-board-resolution-parameters.mjs';
import {stringLossCase} from './f9-string-loss-parameters.mjs';

import {solidWire} from '../c3x-physical/c4-wire-consistency.mjs';
import {makeDesign} from './c4-design.mjs';
import {stringMode,spatialWeight} from './stiff-string.mjs';
import {plateDesign,plateModes,patchWeight} from './orthotropic-plate.mjs';
import {ribDesign,generalizedEigen} from './ribbed-plate.mjs';
import {mindlinModes} from './mindlin-plate.mjs';
import {PolarizedBridge,PolarizedHammer} from './polarized-bridge.mjs';
import {BoardCoupledBridge} from './board-coupling.mjs';
import {radiationGrid,surfaceShape,radiationKernel} from './surface-radiation.mjs';
import {ResistiveBoard,radiationResistance} from './radiation-loading.mjs';
import {relaxMemory} from './felt-memory.mjs';
import {fft} from './f8-render.mjs';
const hp={fft,solidWire,makeDesign,stringMode,spatialWeight,plateDesign,plateModes,patchWeight,ribDesign,generalizedEigen,mindlinModes,PolarizedBridge,PolarizedHammer,BoardCoupledBridge,radiationGrid,surfaceShape,radiationKernel,ResistiveBoard,relaxMemory};

const p=hp.plateDesign(),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>hp.ribDesign(p,{xM})),patch={xM:.83,yM:.46,dxM:.04,dyM:.025},wires=[-.5,0,.5].map(c=>hp.makeDesign(hp.solidWire,{f1Hz:440*2**(-9/12+c/1200)}));

const {modes,...quality}=resolutionMetrics(mindlinModes(p,ribs,{basisHz:4000},hp),3000);
const levels=[{nt:12,np:24},{nt:24,np:48},{nt:48,np:96}];
const boards=levels.map(radiation=>new ResistiveBoard(p,modes,patch,1/96000,{loss0:1,lossSlope:.00025,radiation},hp));
const [coarse,medium,fine]=boards,coarseMatrix=compareBlocks(fine.blocks,coarse.blocks),mediumMatrix=compareBlocks(fine.blocks,medium.blocks);
const grids=[{x:.90,y:.38,z:1},{x:1.20,y:.38,z:1}].map(l=>radiationGrid(p,l,{nx:128,ny:100}));
const rows=Array.from({length:10},(_,i)=>{
 const h=i+1,f=stringMode(wires[1],h).frequencyHz,w=2*Math.PI*f;
 // Diagnostic only: use same blocks but R evaluated at the forced frequency.
 // Not a causal time-domain realization; do not use these blocks in the stepper.
 const exactBlocks=medium.blocks.map(b=>({...b,R:radiationResistance(p,b.indices.map(j=>modes[j]),f,levels[1])}));
 const exact={modes:medium.modes,blocks:exactBlocks};
 const candidates=[coarse,medium,fine,exact],responses=candidates.map(b=>modalBoardResponse(b,f));
 const fixedVelocity=responses[2].acceleration.map(([re,im])=>[im/w,-re/w]);
 const values=responses.map((q,j)=>{
  const b=candidates[j],velocity=q.acceleration.map(([re,im])=>[im/w,-re/w]),actual=resistancePower(b.blocks,velocity),fixed=resistancePower(b.blocks,fixedVelocity);
  if(!actual.passive||!fixed.passive||Math.abs(actual.power-q.radiationW)>1e-10||Math.abs(q.powerResidualW)>1e-10||q.maxRelativeResidual>1e-9||q.inputW<0)throw Error('power/passivity gate');
  const field=complexSurface(modes,q.acceleration),pressure=grids.map(grid=>pressureResponse(grid,field,f));
  return {Y:q.Y,inputW:q.inputW,radiationW:q.radiationW,structuralW:q.structuralW,fixedVelocityRadiationW:fixed.power,powerResidualW:q.powerResidualW,maxRelativeResidual:q.maxRelativeResidual,pressure};
 });
 const difference=(a,b)=>({mobility:responseDifference(a.Y,b.Y),radiationPowerDb:dbRatio(b.radiationW,a.radiationW),fixedVelocityPowerDb:dbRatio(b.fixedVelocityRadiationW,a.fixedVelocityRadiationW),pressure:a.pressure.map((p,j)=>responseDifference(p,b.pressure[j]))});
 return {h,f,values,coarseVsFine:difference(values[2],values[0]),mediumVsFine:difference(values[2],values[1]),forcedFrequencyVsMedium:difference(values[1],values[3])};
});
const result={scope:'reference B board alone, forced continuous unit peak force, resistance quadrature and block-center approximation; not full impedance, not free decay',quality,levels,coarseMatrix,mediumMatrix,rows};
const dir=process.argv[2]??'f916d-output';mkdirSync(dir,{recursive:true});
writeFileSync(dir+'/load-audit.json',JSON.stringify(result,null,2),{flag:'wx'});
console.log('F916D_LOAD '+JSON.stringify(result));
