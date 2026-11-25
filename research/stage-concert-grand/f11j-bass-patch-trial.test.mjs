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
import {renderBassPilot} from './f11d-bass-render.mjs';
import {renderBassPatchTrial,PATCH_VARIANTS} from './f11j-bass-patch-trial.mjs';
let n=0;const check=(m,b)=>{if(!b)throw Error(m);n++},rejects=f=>{try{f();return false}catch{return true}};
const exact=(a,b)=>a.channels.every((c,j)=>c.length===b.channels[j].length&&c.every((v,i)=>Object.is(v,b.channels[j][i])));
for(const midi of [43,48]){
 const opts={midi,midiVelocity:76,seconds:.05};
 const ref=renderBassPilot(hp,{...opts,count:2}),a=renderBassPatchTrial(hp,{...opts,variant:'A'});
 check('exact A '+midi,exact(a,ref)&&JSON.stringify(a.checkpoint.state)===JSON.stringify(ref.checkpoint.state));
 for(const variant of ['LL','LM']){
  const q=renderBassPatchTrial(hp,{...opts,variant});
  check('board coefficients '+midi+variant,JSON.stringify(q.meta.boardSignature)===JSON.stringify(a.meta.boardSignature));
  check('same wires/loss '+midi+variant,JSON.stringify(q.meta.wires)===JSON.stringify(a.meta.wires)&&JSON.stringify(q.meta.actualStringLoss)===JSON.stringify(a.meta.actualStringLoss));
  check('changed port '+midi+variant,q.meta.patchActual.xM===PATCH_VARIANTS[variant]&&q.meta.portWeights.some((w,i)=>w!==a.meta.portWeights[i])&&!exact(q,a));
  check('passive '+midi+variant,q.meta.maxBalance<1e-9&&q.meta.maxIncrease<1e-9&&q.meta.reboundMps<0);
  const next=renderBassPatchTrial(hp,{...opts,variant,prior:q.checkpoint});
  check('continuous '+midi+variant,next.checkpoint.elapsed===.1&&next.meta.maxBalance<1e-9&&next.meta.peakForce===0);
  check('guard '+midi+variant,rejects(()=>renderBassPatchTrial(hp,{...opts,variant:'A',prior:q.checkpoint})));
 }
}
check('reject outside scope',rejects(()=>renderBassPatchTrial(hp,{midi:36})));
console.log('F11J_PATCH_TESTS '+n);
