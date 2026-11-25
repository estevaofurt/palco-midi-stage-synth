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
import {renderS50Scale} from './f11a-s50-scale.mjs';
import {VariableHammer,solveNoteContact} from './f11d-variable-hammer.mjs';
import {solveCoupledContact} from './mobile-hammer.mjs';
import {feltParameters} from './f9-felt-sensitivity.mjs';
import {bassWires,renderBassPilot,BASS_NOTES} from './f11d-bass-render.mjs';
let n=0;const check=(m,b)=>{if(!b)throw Error(m);n++},rejects=f=>{try{f();return false}catch{return true}};
const felt=feltParameters(1.5);
const d=[0,0,0],free=[.0001,.00012,.00009],C=d.map((_,i)=>d.map((_,j)=>i===j?1e-8:1e-9));
check('exact three-string solver',JSON.stringify(solveNoteContact(d,free,C,d,felt))===JSON.stringify(solveCoupledContact(d,free,C,d,felt)));
for(const count of [1,2]){
 const q=solveNoteContact(d.slice(0,count),free.slice(0,count),C.slice(0,count).map(x=>x.slice(0,count)),d.slice(0,count),felt);
 check('contact convergence '+count,q.forces.length===count&&q.forces.every(x=>x>0)&&q.residual<1e-9);
}
check('zero force open',solveNoteContact([-.001],[-.001],[[1e-8]],[0],felt).forces[0]===0);
check('invalid compliance',rejects(()=>solveNoteContact([0],[.001],[[-1]],[0],felt)));
const ref=renderS50Scale(hp,{midi:60,midiVelocity:76,seconds:.025});
const ref2=renderS50Scale({...hp,PolarizedHammer:VariableHammer},{midi:60,midiVelocity:76,seconds:.025});
check('exact S50 pressure',ref.channels.every((c,j)=>c.every((v,i)=>Object.is(v,ref2.channels[j][i]))));
check('exact S50 state',JSON.stringify(ref.checkpoint.state)===JSON.stringify(ref2.checkpoint.state));
const cases=[];
for(const midi of BASS_NOTES)for(const count of [1,2]){
 const wires=bassWires(midi,count);
 check('wires '+midi+'/'+count,wires.length===count&&wires.every(w=>Math.abs(stringMode(w,1).frequencyHz-w.f1Hz)<1e-10));
 const q=renderBassPilot(hp,{midi,count,midiVelocity:76,seconds:.05});cases.push(q);
 check('passive '+midi+'/'+count,q.meta.maxBalance<1e-9&&q.meta.maxIncrease<1e-9&&q.meta.reboundMps<0&&q.meta.peakForce>0);
 check('board unchanged '+midi+'/'+count,JSON.stringify(q.meta.boardSignature)===JSON.stringify(ref.meta.boardSignature));
 check('memory size '+midi+'/'+count,q.checkpoint.state[5].z.length===count);
}
for(const count of [1,2]){
 const a=cases[count-1],q=renderBassPilot(hp,{midi:36,count,midiVelocity:76,seconds:.05,prior:a.checkpoint});
 check('continuity '+count,q.checkpoint.elapsed===.1&&q.meta.maxBalance<1e-9&&q.meta.peakForce===0);
}
check('note guard',rejects(()=>renderBassPilot(hp,{midi:43,count:1,prior:cases[0].checkpoint})));
check('count guard',rejects(()=>renderBassPilot(hp,{midi:36,count:2,prior:cases[0].checkpoint})));
check('velocity guard',rejects(()=>renderBassPilot(hp,{midi:36,count:1,midiVelocity:127,prior:cases[0].checkpoint})));
console.log('F11D_BASS_TESTS '+n);
