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
import {fft,waveBytes} from './f8-render.mjs';
const hp={fft,solidWire,makeDesign,stringMode,spatialWeight,plateDesign,plateModes,patchWeight,ribDesign,generalizedEigen,mindlinModes,PolarizedBridge,PolarizedHammer,BoardCoupledBridge,radiationGrid,surfaceShape,radiationKernel,ResistiveBoard,relaxMemory};

import {buildChord} from './f11u-r8-board.mjs';
import {boardResponse} from './f11u-r9-transfer.mjs';
import {kernelResponse} from './surface-radiation.mjs';
import {ribbedPatchWeight} from './ribbed-plate.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
const [out='/tmp/r9']=process.argv.slice(2);
const notes=[48,60,67],{p,modes,board,patches}=buildChord(hp,{notes,variant:'K750',layout:'wide',lossFactor:1,spread:.5,angle:.5});
const listeners=[{x:.90,y:.38,z:.3},{x:1.20,y:.38,z:.3}];
const kernels=listeners.map(l=>{const grid=hp.radiationGrid(p,l,{nx:64,ny:50});return modes.map(m=>hp.radiationKernel(grid,(x,y)=>hp.surfaceShape(m,x,y),48000));});
const db=v=>20*Math.log10(Math.max(v,1e-30));
const rows=[];
for(let g=0;g<notes.length;g++){
 const midi=notes[g],f0=440*2**((midi-69)/12),patch=patches[g];
 for(const [dx,dy] of [[0,0],[-.04,0],[.04,0],[0,-.04],[0,.04]]){
  const loc={...patch,xM:patch.xM+dx,yM:patch.yM+dy};
  const weights=modes.map(m=>ribbedPatchWeight(p,m,loc,hp.patchWeight));
  const bands=[];
  for(let k=1;k<=8;k++){
   const samples=[-.01,-.005,0,.005,.01].map(d=>boardResponse(board,weights,k*f0*(1+d),kernels,kernelResponse));
   bands.push({partial:k,nominalHz:k*f0,pressureRms:Math.sqrt(samples.reduce((s,x)=>s+x.stereoMagnitude**2,0)/samples.length),mobilityRms:Math.sqrt(samples.reduce((s,x)=>s+x.mobility.magnitude**2,0)/samples.length),samples});
  }
  rows.push({midi,dx,dy,loc,pressureRelativeDb:bands.map(b=>db(b.pressureRms/bands[0].pressureRms)),fundamentalPressureDb:db(bands[0].pressureRms),bands});
 }
}
const result={scope:'continuous board-only harmonic response per unit force; frozen radiation resistance blocks; not full piano transfer or measured microphone calibration',listeners,rows};
mkdirSync(out,{recursive:true});writeFileSync(out+'/transfer.json',JSON.stringify(result,null,2));
console.log('R9_TRANSFER_RESULT '+JSON.stringify(rows.map(({midi,dx,dy,pressureRelativeDb,fundamentalPressureDb})=>({midi,dx,dy,pressureRelativeDb,fundamentalPressureDb}))));
