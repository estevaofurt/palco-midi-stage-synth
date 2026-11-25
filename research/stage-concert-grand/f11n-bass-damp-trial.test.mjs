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
import {renderBassDampTrial,DAMP_VARIANTS,TARGETS} from './f11n-bass-damp-trial.mjs';
let n=0;const check=(m,b)=>{if(!b)throw Error(m);n++},rejects=f=>{try{f();return false}catch{return true}};
const exact=(a,b)=>a.channels.every((c,j)=>c.length===b.channels[j].length&&c.every((v,i)=>Object.is(v,b.channels[j][i])));
for(const midi of [36,43,48]){
 const opts={midi,midiVelocity:76,seconds:.05};
 const ref=renderBassPilot(hp,{...opts,count:2}),a=renderBassDampTrial(hp,{...opts,variant:'A'});
 check('exact A '+midi,exact(ref,a)&&JSON.stringify(ref.checkpoint.state)===JSON.stringify(a.checkpoint.state));
 for(const variant of ['M2','M4']){
  const q=renderBassDampTrial(hp,{...opts,variant}),loss=q.meta.bassModeLoss,ids=new Set(loss.modes.map(m=>m.i));
  check('four fixed modes '+midi+variant,loss.modeCount===337&&ids.size===4&&loss.modes.every((m,j)=>Math.abs(m.hz-TARGETS[j])<.001&&m.after===m.before*DAMP_VARIANTS[variant]));
  check('only damping '+midi+variant,q.meta.boardSignature.every(([f,v],i)=>f===a.meta.boardSignature[i][0]&&v===a.meta.boardSignature[i][1]*(ids.has(i)?DAMP_VARIANTS[variant]:1)));
  check('unchanged wires and loss '+midi+variant,JSON.stringify(q.meta.wires)===JSON.stringify(a.meta.wires)&&JSON.stringify(q.meta.actualStringLoss)===JSON.stringify(a.meta.actualStringLoss));
  check('passive changed pressure '+midi+variant,q.meta.maxBalance<1e-9&&q.meta.maxIncrease<1e-9&&q.meta.reboundMps<0&&!exact(q,a));
  const next=renderBassDampTrial(hp,{...opts,variant,prior:q.checkpoint});
  check('continuous '+midi+variant,next.checkpoint.elapsed===.1&&next.meta.maxBalance<1e-9&&next.meta.peakForce===0);
  check('guard '+midi+variant,rejects(()=>renderBassDampTrial(hp,{...opts,variant:'A',prior:q.checkpoint})));
 }
}
check('outside scope',rejects(()=>renderBassDampTrial(hp,{midi:60})));
console.log('F11N_DAMP_TESTS '+n);
