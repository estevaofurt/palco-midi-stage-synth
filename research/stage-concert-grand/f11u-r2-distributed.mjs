// Diagnostic distributed modal velocity damping, split passive midpoint update.
// Positions unchanged; bridge generalized momentum conserved by the damping substep.
// This is not yet a calibrated spatial felt contact.
export function dampAxis(axis,rate){
 if(!Number.isFinite(rate)||rate<0)throw RangeError('modal damping rate');
 if(!rate)return 0;
 const h=axis.h,b0=axis.vb;
 let rhs=axis.mB*b0,schur=axis.mB;
 for(let i=0;i<axis.modes.length;i++){
  const m=axis.modes[i],a=m.m*(1+h*rate),p=m.m*axis.v[i]+m.cross*b0;
  rhs+=m.cross*axis.v[i]-m.cross*p/a;schur-=m.cross*m.cross/a;
 }
 if(!(schur>0))throw Error('damping mass Schur');
 const b=rhs/schur;let loss=0;
 for(let i=0;i<axis.modes.length;i++){
  const m=axis.modes[i],v=(m.m*axis.v[i]+m.cross*(b0-b))/(m.m*(1+h*rate));
  loss+=h*2*m.m*rate*v*v;axis.v[i]=2*v-axis.v[i];
 }
 axis.vb=2*b-b0;
 return loss;
}
export function distributedStep(net,levels,rate,both=true){
 net.step();let loss=0;
 for(let g=0;g<net.bridges.length;g++){
  const b=net.bridges[g],r=rate*levels[g];
  loss+=dampAxis(b.vAxis,r);
  if(both)loss+=dampAxis(b.hAxis,r);
 }
 return loss;
}
