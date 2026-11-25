
import {SharedBoard,SharedBridgeNetwork,seedPartial} from './f9-shared-board.mjs';
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

import {MultiHammerNetwork,SimultaneousHammers,solveMultiContact} from './f11r-multi-hammer-network.mjs';
import {bassWires} from './f11d-bass-render.mjs';
import {scaleWire} from './f11a-s50-scale.mjs';
import {VariableHammer} from './f11d-variable-hammer.mjs';
import {feltParameters} from './f9-felt-sensitivity.mjs';
import {hammerSpeed} from './f9-midi-velocity.mjs';
import {fastSharedBoard} from './f9-sympathetic-network.mjs';
const p=hp.plateDesign(),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>hp.ribDesign(p,{xM})),patches=[{xM:.83,yM:.46,dxM:.04,dyM:.025},{xM:.96,yM:.46,dxM:.04,dyM:.025}];
const modes=hp.mindlinModes(p,ribs,{basisHz:4000},hp).modes.filter(m=>m.frequencyHz<1200);
const opts={sampleRate:96000,maxFrequencyHz:3000,stiffness:[0,2e6],damping:[0,5],angleRad:.5,verticalLoss:[.1,.0002],horizontalLoss:[.05,.00012]};
const boardOpts={loss0:3,lossSlope:.00075,radiation:{scale:1}},joint={k:1e7,c:1},felt=feltParameters(1.5),hammer={velocityMps:hammerSpeed(76),felt};
const bass=bassWires(48,2),mid=[-.5,0,.5].map(c=>scaleWire(hp,64,c));
const make=w=>new hp.PolarizedBridge(w,opts,hp);
const build=(groups,joints)=>{const bridges=groups.map(make),board=new SharedBoard(p,modes,patches.slice(0,groups.length),bridges[0].h,boardOpts,hp),net=new MultiHammerNetwork(bridges,board,joints);fastSharedBoard(board);return net;};
let n=0;const check=(m,b)=>{if(!b)throw Error(m);n++};
const trial=build([bass,mid],[joint,joint]),h=new SimultaneousHammers(trial,[hammer,hammer]);
check('mixed contacts',trial.contacts.length===5);
check('cross coupling nonzero',trial.G[0].slice(2).some(x=>Math.abs(x)>1e-20));
check('reciprocal matrix',trial.G.every((r,i)=>r.every((x,j)=>x===trial.G[j][i])));
const free=trial.freeContacts(),forces=[[1,2],[3,4,5]],flat=forces.flat(),pred=free.map((v,i)=>v+trial.G[i].reduce((s,c,j)=>s+c*flat[j],0));
trial.step(forces);
check('full compliance prediction',trial.displacement().every((x,i)=>Math.abs(x-pred[i])<1e-14));
const one=build([bass],[joint]),single=new SimultaneousHammers(one,[hammer]),bridge=make(bass),board=new hp.ResistiveBoard(p,modes,patches[0],bridge.h,boardOpts,hp),old=new VariableHammer(new hp.BoardCoupledBridge(bridge,board),hammer);
let err=0,peak=0;
for(let i=0;i<960;i++){single.step();old.step();err=Math.max(err,Math.abs(single.energy()-old.energy()));peak=Math.max(peak,Math.abs(single.hammers[0].v-old.v));}
check('single hammer parity',err<1e-10&&peak<1e-8);
function run(joints){
 const net=build([bass,mid],joints),h=new SimultaneousHammers(net,[hammer,hammer]),e0=h.energy();let prev=e0,balance=0,increase=0,residual=0,peaks=[0,0];
 for(let i=0;i<1920;i++){const f=h.step();f.forEach((row,g)=>peaks[g]=Math.max(peaks[g],row.reduce((s,x)=>s+x,0)));const e=h.energy();balance=Math.max(balance,Math.abs(e+net.lossJ+h.lossJ-e0));increase=Math.max(increase,e-prev);prev=e;residual=Math.max(residual,h.lastResidual);}
 return {balance,increase,residual,peaks,rebound:h.hammers.map(x=>x.v),boardEnergy:net.board.energy()};
}
const on=run([joint,joint]),off=run([joint,{k:0,c:0}]);
check('two simultaneous hammer strikes',on.peaks.every(x=>x>0)&&on.rebound.every(x=>x<0));
check('energy balance',on.balance<1e-9&&off.balance<1e-9&&on.increase<1e-9&&off.increase<1e-9);
check('contact residual',on.residual<1e-8&&off.residual<1e-8);
check('shared board response differs',Math.abs(on.boardEnergy-off.boardEnergy)>1e-12);
const q=solveMultiContact([0,0],[.0002,.0002],[[1e-8,-1e-9],[-1e-9,1e-8]],[0,0],[felt,felt]);
check('signed off diagonal',q.forces.every(x=>x>0)&&q.residual<1e-9);
console.log('F11R_MULTI_TESTS '+n);
console.log('F11R_MULTI_RESULT '+JSON.stringify({modeCount:modes.length,onePort:{err,peak},on,off}));
