// G2.11a isolated octave experiment. Preserve anchor matrices and board basis exactly.
import {readFileSync,writeFileSync} from 'node:fs';
import {PolarizedBridge} from '../stage-concert-grand/polarized-bridge.mjs';
import {stringMode,spatialWeight} from '../stage-concert-grand/stiff-string.mjs';
import {denseMatrices} from './g2_moving_reference.mjs';
import {wireFor,DESIGN} from './g2_string_pilot.mjs';
import {buildBoard,PATCHES,weights} from './g2_board_pilot.mjs';
import {LOSS_CASES} from './g2_decay.mjs';
const root='/tmp/g2-shared-board';
const base=JSON.parse(readFileSync(root+'/model.json','utf8'));
const a=wireFor(60),b=wireFor(84);
const keys=[48,...Array.from({length:13},(_,i)=>60+i),84];
const interp=(x,y,t)=>x+(y-x)*t;
const geometric=(x,y,t)=>x*Math.pow(y/x,t);
const params=key=>{
 const t=(key-60)/24;
 return {key,lengthM:geometric(a.lengthM,b.lengthM,t),diameterM:interp(a.diameterM,b.diameterM,t),
   massKg:interp(.010,.006,t),cutoffHz:12000,patch:{key,xM:interp(PATCHES[1].xM,PATCHES[2].xM,t),yM:interp(PATCHES[1].yM,PATCHES[2].yM,t),dxM:.04,dyM:.025}};
};
function wire(p,cents){
 const L=p.lengthM,d=p.diameterM,youngPa=200e9,densityKgM3=7850,areaM2=Math.PI*d*d/4,linearDensityKgM=densityKgM3*areaM2,EI=youngPa*Math.PI*d**4/64;
 const f1Hz=440*2**((p.key-69)/12+cents/1200),tensionN=4*L*L*linearDensityKgM*f1Hz**2-Math.PI**2*EI/L**2;
 if(!(tensionN>0&&Number.isFinite(tensionN)))throw Error('tension');
 return {midi:p.key,lengthM:L,diameterM:d,youngPa,densityKgM3,areaM2,linearDensityKgM,EI,tensionN,f1Hz,B:Math.PI**2*EI/(tensionN*L**2),stressPa:tensionN/areaM2};
}
const helpers={stringMode,spatialWeight:(m,L,x,_width)=>spatialWeight(m,L,x,DESIGN.widthM)};
const l=[LOSS_CASES.control.sigma0PerS,LOSS_CASES.control.sigma2M2PerS];
const groups=keys.map(key=>{
 const old=base.groups.find(x=>x.key===key);
 if(old)return {...old,massKg:({48:.012,60:.010,84:.006})[key],anchor:true};
 const p=params(key),wires=[-.5,0,.5].map(c=>wire(p,c));
 const bridge=new PolarizedBridge(wires,{sampleRate:96000,maxFrequencyHz:p.cutoffHz,massKg:.025,stiffness:[0,2e6],damping:[0,5],angleRad:0,verticalLoss:l,horizontalLoss:l},helpers);
 const {M,C,K,ports,N,n}=denseMatrices(bridge),arr=x=>x.map(y=>Array.from(y));
 return {key,N,n,M:arr(M),C:arr(C),K:arr(K),ports:arr(ports),massKg:p.massKg,anchor:false,geometry:p,wires};
});
const board=buildBoard('control',6000),orig=base.boards.find(x=>x.basis===6000);
const cols=keys.map(key=>PATCHES.some(p=>p.key===key)?null:weights(board,params(key).patch));
const modes=orig.modes.map((m,i)=>{
 if(Math.abs(board.modes[i].frequencyHz-m.f)>1e-8)throw Error('board basis mismatch');
 return {...m,w:keys.map((key,j)=>cols[j]===null?m.w[PATCHES.findIndex(p=>p.key===key)]:cols[j][i])};
});
if(groups.length!==15||groups.filter(g=>!g.anchor).length!==12)throw Error('scope');
writeFileSync(root+'/octave.json',JSON.stringify({groups,boards:[{...orig,modes}],playable:keys.filter(k=>k>=60&&k<=72),scope:'provisional geometry interpolation; 13 playable keys plus 2 passive anchor groups'}));
console.log('G2_11_EXPORT '+JSON.stringify({keys,playable:keys.filter(k=>k>=60&&k<=72),groups:groups.map(g=>({key:g.key,n:g.n,mass:g.massKg,geometry:g.geometry,stress:g.wires?.[1].stressPa}))}));
