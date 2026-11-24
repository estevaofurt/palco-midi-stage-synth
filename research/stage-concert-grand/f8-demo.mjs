import {writeFileSync,mkdirSync} from 'node:fs';
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
import {makeRenderer,waveBytes} from './f8-render.mjs';
const hp={solidWire,makeDesign,stringMode,spatialWeight,plateDesign,plateModes,patchWeight,ribDesign,generalizedEigen,mindlinModes,PolarizedBridge,PolarizedHammer,BoardCoupledBridge,radiationGrid,surfaceShape,radiationKernel,ResistiveBoard,relaxMemory};
const seconds=Number(process.argv[2]??.5),dir=process.argv[3]??'f8-output';
if(!Number.isFinite(seconds)||seconds<.1||seconds>2)throw Error('duration must be 0.1–2 s');
mkdirSync(dir,{recursive:true});const renderer=makeRenderer(hp,{seconds,rate:96000,cut:3000});const gain=.36767023440034063;
for(const [name,v,s] of [['C4_suave_R',.5,1],['C4_medio_R',1,1],['C4_forte_R',2.5,1],['C4_medio_sem_R',1,0]]){const q=renderer.render(v,s),w=waveBytes(q.channels,48000,gain);if(w.clipped)throw Error('clipping '+name);writeFileSync(dir+'/'+name+'.wav',w.bytes);console.log(JSON.stringify({name,...q.meta,pcmPeak:w.peak,clipped:w.clipped}));}
