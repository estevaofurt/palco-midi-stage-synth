import {cholesky,solveCholesky} from './radiation-loading.mjs';
// F9.14: passive viscous point contact, using existing vertical contact ports.
// Prescribed key/pedal control. Not a measured felt or pedal mechanism.
export const DAMPER_C=1;
export const DAMPER_RAMP_S=.025;
export function damperCoefficient(t,{keyReleaseS=.5,pedalReleaseS=1.5,pedal=0}={}){
 if(!Number.isFinite(t)||t<0||!Number.isFinite(keyReleaseS)||keyReleaseS<.025||!Number.isFinite(pedalReleaseS)||pedalReleaseS<keyReleaseS||!Number.isFinite(pedal)||pedal<0||pedal>1)throw RangeError('damper schedule');
 const ramp=x=>Math.max(0,Math.min(1,x/DAMPER_RAMP_S));
 return DAMPER_C*ramp(t-keyReleaseS)*(1-pedal*(1-ramp(t-pedalReleaseS)));
}
export function viscousStep(network,c){
 if(!Number.isFinite(c)||c<0)throw RangeError('damper coefficient');
 if(c===0){network.step();return 0;}
 const before=network.wires.map((_,i)=>network.contactDisplacement(i)),free=network.freeContacts(),G=network.contactCompliance(),h=network.h;
 const A=G.map((r,i)=>r.map((x,j)=>.5*(x+G[j][i])+(i===j?h/c:0)));
 const f=solveCholesky(cholesky(A),before.map((x,i)=>x-free[i]));network.step(f);
 let diss=0,work=0;
 for(let i=0;i<f.length;i++){const d=network.contactDisplacement(i)-before[i];diss+=c*d*d/h;work+=f[i]*d;}
 if(!Number.isFinite(diss)||Math.abs(work+diss)>1e-11)throw Error('damper work residual');
 return diss;
}
