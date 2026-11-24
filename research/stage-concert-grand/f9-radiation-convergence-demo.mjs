import {polarizationLedger,validateAngle} from './f9-aftersound-ledger.mjs';
import {writeFileSync,mkdirSync} from 'node:fs';
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
import {ResistiveBoard} from './radiation-loading.mjs';
import {relaxMemory} from './felt-memory.mjs';
import {fft} from './f8-render.mjs';
const hp={fft,solidWire,makeDesign,stringMode,spatialWeight,plateDesign,plateModes,patchWeight,ribDesign,generalizedEigen,mindlinModes,PolarizedBridge,PolarizedHammer,BoardCoupledBridge,radiationGrid,surfaceShape,radiationKernel,ResistiveBoard,relaxMemory};

const p=hp.plateDesign(),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>hp.ribDesign(p,{xM})),patch={xM:.83,yM:.46,dxM:.04,dyM:.025},wires=[-.5,0,.5].map(c=>hp.makeDesign(hp.solidWire,{f1Hz:440*2**(-9/12+c/1200)}));

const listeners=[{x:.90,y:.38,z:1},{x:1.20,y:.38,z:1}],sizes=[[64,50],[128,100],[192,150]],grids=listeners.map(l=>sizes.map(([nx,ny])=>radiationGrid(p,l,{nx,ny})));
const cases=['reference','basis8','basis12'].map(resolution=>{
 const config=boardResolution(resolution),{modes,...quality}=resolutionMetrics(mindlinModes(p,ribs,{basisHz:config.basisHz},hp),config.cutoffHz),board=new ResistiveBoard(p,modes,patch,1/96000,{loss0:1,lossSlope:.00025,radiation:{scale:1}},hp);
 const rows=Array.from({length:10},(_,i)=>{
  const h=i+1,f=stringMode(wires[1],h).frequencyHz,q=modalBoardResponse(board,f),old=boardMobility(board,f);
  if(q.Y.some((x,j)=>Math.abs(x-old.Y[j])>1e-12)||Math.abs(q.powerResidualW)>1e-10||q.maxRelativeResidual>1e-9||q.inputW<0)throw Error('forced board passivity/parity');
  const field=complexSurface(modes,q.acceleration),channels=grids.map((gs,ch)=>{
   const responses=gs.map((grid,j)=>({nx:sizes[j][0],ny:sizes[j][1],exact:pressureResponse(grid,field,f),linear48:pressureResponse(grid,field,f,48000)})),fine=responses.at(-1).exact;
   return {channel:ch,responses,coarseToFine:responseDifference(fine,responses[0].exact),mediumToFine:responseDifference(fine,responses[1].exact),coarseDelay:responseDifference(responses[0].exact,responses[0].linear48),fineDelay:responseDifference(fine,responses.at(-1).linear48)};
  });
  return {h,f,Y:q.Y,powerResidualW:q.powerResidualW,maxRelativeResidual:q.maxRelativeResidual,channels};
 });return {resolution,...config,...quality,rows};
});
const dir=process.argv[2]??'f916c-output';mkdirSync(dir,{recursive:true});
writeFileSync(dir+'/radiation.json',JSON.stringify({scope:'continuous harmonic board response to unit peak force at bridge patch, fixed mechanical radiation resistance, not struck-note pressure or full acoustic impedance',cases},null,2),{flag:'wx'});
console.log('F916C_RADIATION '+JSON.stringify(cases.map(c=>({resolution:c.resolution,modeCount:c.modeCount,rows:c.rows.map(r=>({h:r.h,f:r.f,maxRelativeResidual:r.maxRelativeResidual,powerResidualW:r.powerResidualW,channels:r.channels.map(({channel,coarseToFine,mediumToFine,coarseDelay,fineDelay})=>({channel,coarseToFine,mediumToFine,coarseDelay,fineDelay}))}))}))));
