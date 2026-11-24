
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

const p=hp.plateDesign(),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>hp.ribDesign(p,{xM})),patches=[{xM:.83,yM:.46,dxM:.04,dyM:.025},{xM:.96,yM:.46,dxM:.04,dyM:.025}];
const modes=hp.mindlinModes(p,ribs,{basisHz:4000},hp).modes.filter(m=>m.frequencyHz<1200),f0=440*2**(-9/12);
const wires=[-.5,0,.5].map(c=>hp.makeDesign(hp.solidWire,{f1Hz:f0*2**(c/1200)}));
const secondary=(cents)=>{const proto=hp.makeDesign(hp.solidWire,{lengthM:1.3,f1Hz:f0/2});const target=f0*2**(cents/1200),k=2*Math.PI/proto.lengthM,mu=proto.linearDensityKgM,T=(mu*(2*Math.PI*target)**2-proto.EI*k**4)/(k*k);
 const wire=hp.solidWire({lengthM:proto.lengthM,diameterM:.00096,youngPa:200e9,densityKgM3:7850,tensionN:T});return wire;};
const opts={sampleRate:96000,maxFrequencyHz:3000,stiffness:[0,2e6],damping:[0,5],angleRad:.5,...stringLossCase('both-half')};
const boardOpts={loss0:1,lossSlope:.00025,radiation:{scale:1}},joint={k:1e7,c:1};
const makeBridge=w=>new hp.PolarizedBridge(w,opts,hp);
function run(cents,connected,seconds){
 const source=makeBridge(wires),other=makeBridge([secondary(cents)]),board=new SharedBoard(p,modes,patches,source.h,boardOpts,hp),net=new SharedBridgeNetwork([source,other],board,[joint,connected?joint:{k:0,c:0}]);
 seedPartial(source,1,1,1e-4);
 const E0=net.energy(),count=Math.round(seconds/net.h),windows=[];let maxResidual=0,maxIncrease=0,prev=E0,peakOther=0,boardRms=0,n=0;
 for(let i=0;i<count;i++){net.step();const E=net.energy(),otherJ=other.wireEnergy('v',0)+other.wireEnergy('h',0);maxResidual=Math.max(maxResidual,Math.abs(E+net.lossJ-E0));maxIncrease=Math.max(maxIncrease,E-prev);prev=E;peakOther=Math.max(peakOther,otherJ);const v=board.modes.reduce((s,m,j)=>s+m.w*board.v[j],0);boardRms+=v*v;n++;
  if((i+1)%9600===0||i===count-1){windows.push({timeS:(i+1)*net.h,secondaryWireJ:otherJ,sourceWireJ:wires.reduce((s,_,j)=>s+source.wireEnergy('v',j)+source.wireEnergy('h',j),0),boardPortVelocityRmsMps:Math.sqrt(boardRms/n),energyJ:E,lossJ:net.lossJ});boardRms=0;n=0;}
 }
 if(maxResidual>1e-10||maxIncrease>1e-10)throw Error('network passivity');
 return {cents,connected,seconds,modeCount:modes.length,secondaryP2Hz:hp.stringMode(secondary(cents),2).frequencyHz,initialEnergyJ:E0,peakOtherJ:peakOther,maxResidual,maxIncrease,windows};
}

let count=0;const check=(m,b)=>{if(!b)throw Error(m);count++;};
const a=makeBridge(wires),b=makeBridge(wires),oldBoard=new hp.ResistiveBoard(p,modes,patches[0],a.h,boardOpts,hp),newBoard=new SharedBoard(p,modes,[patches[0]],b.h,boardOpts,hp);
const old=new hp.BoardCoupledBridge(a,oldBoard,{jointK:joint.k,jointC:joint.c}),next=new SharedBridgeNetwork([b],newBoard,[joint]);
seedPartial(a,1,1,1e-4);seedPartial(b,1,1,1e-4);
for(let i=0;i<960;i++){old.step();next.step();}
check('one port parity',Math.abs(old.energy()-next.energy())<1e-13&&Math.abs(a.vAxis.b-b.vAxis.b)<1e-11&&Math.abs(old.lossJ-next.lossJ)<1e-13);
check('one port board state',oldBoard.x.every((v,i)=>Math.abs(v-newBoard.x[i])<1e-11));
const off=run(0,false,.05),on=run(0,true,.05);
check('disconnected secondary stays at rest',off.peakOtherJ===0);
check('connected secondary receives energy',on.peakOtherJ>0);
check('passivity',[off,on].every(q=>q.maxResidual<1e-10&&q.maxIncrease<1e-10));
check('secondary resonant frequency',Math.abs(on.secondaryP2Hz-f0)<1e-8);
check('reciprocity',Math.abs(newBoard.portG[0][0]-oldBoard.G)<1e-16);
console.log('F9.12 shared board tests passed:',count);console.log('F912_SMOKE '+JSON.stringify({off,on}));
