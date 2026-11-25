import {cholesky,solveCholesky} from './radiation-loading.mjs';
// F11t: passive, coupled per-key viscous damper, experimental full CC64.
export const DAMPER_RAMP_S=.025,DAMPER_C=1;
export class PolyDamperController{
 constructor(notes,events,seconds){
  if(!Array.isArray(notes)||!notes.length||new Set(notes).size!==notes.length||!Array.isArray(events)||!Number.isFinite(seconds)||seconds<=0)throw RangeError('damper schedule');
  this.notes=notes.slice();this.held=new Set(notes);this.pedal=false;
  this.events=events.map(e=>({...e}));this.index=0;this.lastTime=0;this.levels=notes.map(()=>0);
  let last=-1,pedal=false,held=new Set(notes);
  for(const e of events){
   if(!Number.isSafeInteger(e.ms)||e.ms<0||e.ms<last||e.ms>=seconds*1000)throw RangeError('damper event time');
   last=e.ms;
   if(e.type==='off'){if(!held.delete(e.midi))throw RangeError('orphan/duplicate off');}
   else if(e.type==='pedal'){if(![0,127].includes(e.value)||Boolean(e.value)===pedal)throw RangeError('pedal transition');pedal=Boolean(e.value);}
   else throw RangeError('F11t accepts off/pedal only');
  }
 }
 targets(){return this.notes.map(m=>this.held.has(m)||this.pedal?0:DAMPER_C);}
 advance(t){
  const dt=t-this.lastTime;if(dt<0)throw RangeError('nonmonotonic damper time');
  const target=this.targets(),d=dt*DAMPER_C/DAMPER_RAMP_S;
  this.levels=this.levels.map((c,i)=>target[i]>=c?Math.min(target[i],c+d):Math.max(target[i],c-d));
  this.lastTime=t;
 }
 coefficientsAt(t){
  if(!Number.isFinite(t)||t<this.lastTime)throw RangeError('damper time');
  while(this.index<this.events.length&&this.events[this.index].ms/1000<=t){
   const e=this.events[this.index++];this.advance(e.ms/1000);
   if(e.type==='off')this.held.delete(e.midi);else this.pedal=e.value===127;
  }
  this.advance(t);return this.levels.slice();
 }
}
// Solve F = (G + h/C)^-1 (x_old - x_free) over the active wire subset.
// G includes cross-note coupling via the single soundboard.
export function viscousMultiDamperStep(net,coefficients){
 if(!Array.isArray(coefficients)||coefficients.length!==net.bridges.length||coefficients.some(c=>!Number.isFinite(c)||c<0||c>32))throw RangeError('damper coefficients');
 const active=net.contacts.map((q,i)=>coefficients[q.g]>0?i:-1).filter(i=>i>=0);
 if(!active.length){net.step();return 0;}
 const before=net.displacement(),free=net.freeContacts(),h=net.h,G=net.G;
 const A=active.map((i,p)=>active.map((j,q)=>.5*(G[i][j]+G[j][i])+(p===q?h/coefficients[net.contacts[i].g]:0)));
 const f=solveCholesky(cholesky(A),active.map(i=>before[i]-free[i]));
 const forces=net.zero.map(row=>row.slice());
 active.forEach((i,k)=>{const {g,j}=net.contacts[i];forces[g][j]=f[k];});
 net.step(forces);
 const after=net.displacement();let work=0,loss=0;
 active.forEach((i,k)=>{const dx=after[i]-before[i],c=coefficients[net.contacts[i].g];work+=f[k]*dx;loss+=c*dx*dx/h;});
 if(!Number.isFinite(loss)||Math.abs(work+loss)>1e-9*Math.max(1,Math.abs(work),Math.abs(loss)))throw Error('poly damper work residual');
 return loss;
}
