import {dampAxis} from './f11u-r2-distributed.mjs';
const a={h:1/96000,mB:.1,vb:.3,modes:[{m:.02,cross:.01},{m:.03,cross:-.008}],v:[.7,-.5]};
const energy=()=>.5*a.mB*a.vb*a.vb+a.modes.reduce((s,m,i)=>s+.5*m.m*a.v[i]**2+m.cross*a.v[i]*a.vb,0);
const momentum=()=>a.mB*a.vb+a.modes.reduce((s,m,i)=>s+m.cross*a.v[i],0);
const e=energy(),p=momentum();let loss=0;
for(let i=0;i<9600;i++)loss+=dampAxis(a,40);
if(Math.abs(e-energy()-loss)>1e-12||Math.abs(p-momentum())>1e-12||loss<=0)throw Error('passivity or momentum');
const before=JSON.stringify(a);if(dampAxis(a,0)!==0||JSON.stringify(a)!==before)throw Error('zero damping parity');
console.log('F11U_R2_UNIT_PASS',loss);
