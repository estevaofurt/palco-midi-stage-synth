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
import {renderBassPatchTrial} from './f11j-bass-patch-trial.mjs';
import {scanRadiation} from './f11m-radiated-mobility.mjs';
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
const [out='f11m-radiation']=process.argv.slice(2);
const base=JSON.parse(readFileSync(new URL('../../audio/analysis_f11g_bass_trials_ci.json',import.meta.url))).cases;
const spatial=JSON.parse(readFileSync(new URL('../../audio/analysis_f11j_bass_patch_ci.json',import.meta.url))).cases;
const cases=[];
for(const midi of [43,48])for(const variant of ['A','LL','LM']){
 let joint=null;
 class Capture extends hp.BoardCoupledBridge{constructor(...a){super(...a);joint=this;}}
 const q=renderBassPatchTrial({...hp,BoardCoupledBridge:Capture},{midi,variant,midiVelocity:76,seconds:.05});
 if(!joint||q.meta.maxBalance>1e-9||q.meta.maxIncrease>1e-9)throw Error('capture');
 const observed=(variant==='A'?base:spatial).find(c=>c.midi===midi&&c.variant===variant);
 if(!observed)throw Error('missing acoustic reference');
 const f1=q.meta.wire.f1Hz,B=q.meta.wire.B;
 const p=hp.plateDesign(),kernels=[{x:.90,y:.38,z:1},{x:1.20,y:.38,z:1}].map(l=>{const grid=hp.radiationGrid(p,l,{nx:64,ny:50});return joint.board.modes.map(m=>hp.radiationKernel(grid,(x,y)=>hp.surfaceShape(m,x,y),48000));});
 const bands=[1,2].map(h=>scanRadiation(joint.bridge,joint.board,joint,kernels,h*f1*Math.sqrt((1+B*h*h)/(1+B))));
 cases.push({midi,variant,bands,observed:observed.pitch.map(w=>({startS:w.startS,partials:w.partials.slice(0,2)})),boardSignature:q.meta.boardSignature});
}
mkdirSync(out,{recursive:true});
writeFileSync(out+'/radiated-response.json',JSON.stringify({scope:'continuous mechanical forced response with renderer radiation kernels; coherent stereo pressure per equal vertical contact force, not transient pitch or exact discrete response',cases},null,2),{flag:'wx'});
console.log('F11M_RADIATION_RESULT '+JSON.stringify(cases.map(q=>({midi:q.midi,variant:q.variant,bands:q.bands.map(b=>({center:b.center,peaks:b.peaks.map(p=>({f:p.f,cents:p.cents,pressure:p.magnitude,stereo:p.stereo.map(s=>({magnitude:s.magnitude,coherence:s.coherence,topModes:s.topModes.slice(0,2)}))}))})),observed:q.observed.map(w=>({startS:w.startS,hz:w.partials.map(p=>p.peak?.hz)}))}))));
