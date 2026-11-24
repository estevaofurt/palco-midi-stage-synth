import {ResistiveBoard,solveCholesky,cholesky} from './radiation-loading.mjs';
import {ribbedPatchWeight} from './ribbed-plate.mjs';
// F9.12 laboratory: reciprocal shared board with multiple vertical force ports.
export class SharedBoard extends ResistiveBoard{
 constructor(p,modes,patches,h,options,hp){
  if(!Array.isArray(patches)||patches.length<1||patches.length>8)throw RangeError('ports');
  super(p,modes,patches[0],h,options,hp);
  this.weights=patches.map(patch=>modes.map(m=>ribbedPatchWeight(p,m,patch,hp.patchWeight)));
  this.responses=this.weights.map((_,j)=>this.incrementPorts(this.weights.map((_,i)=>+(i===j)),true));
  this.portG=this.weights.map(w=>this.responses.map(dx=>w.reduce((s,x,i)=>s+x*dx[i],0)));
  for(let i=0;i<this.portG.length;i++)for(let j=0;j<i;j++)if(Math.abs(this.portG[i][j]-this.portG[j][i])>1e-12*Math.max(1e-20,Math.abs(this.portG[i][j]),Math.abs(this.portG[j][i])))throw Error('nonreciprocal board');
 }
 incrementPorts(forces,responseOnly=false){
  const dx=new Float64Array(this.modes.length);
  for(const b of this.blocks){
   const rhs=b.indices.map((i,j)=>{const m=this.modes[i],q=m.coeff,F=this.weights.reduce((s,w,k)=>s+w[i]*forces[k],0);return ((responseOnly?0:(q.A-1)*this.x[i]+q.S*this.v[i])+q.G*F)/b.g[j];});
   const y=solveCholesky(b.L,rhs);b.indices.forEach((i,j)=>dx[i]=b.g[j]*y[j]);
  }return dx;
 }
 positions(){return this.weights.map(w=>w.reduce((s,x,i)=>s+x*this.x[i],0));}
 freePorts(){const dx=this.incrementPorts(this.weights.map(()=>0));return this.positions().map((p,j)=>p+this.weights[j].reduce((s,w,i)=>s+w*dx[i],0));}
 stepPorts(forces){
  if(forces.length!==this.weights.length||!forces.every(Number.isFinite))throw RangeError('port forces');
  const dx=this.incrementPorts(forces),h=this.h;let rad=0,local=0,work=0;
  for(const b of this.blocks)for(let j=0;j<b.indices.length;j++){
   const i=b.indices[j],m=this.modes[i],q=m.coeff,x=this.x[i],v=this.v[i],rf=-b.R[j].reduce((s,a,k)=>s+a*dx[b.indices[k]]/h,0),F=this.weights.reduce((s,w,k)=>s+w[i]*forces[k],0),f=F+rf,xn=q.A*x+q.S*v+q.G*f,vn=q.H*x+q.D*v+q.J*f;
   rad-=rf*(xn-x);local+=f*(xn-x)+.5*(v*v-vn*vn+m.lambda*(x*x-xn*xn));work+=F*(xn-x);this.x[i]=xn;this.v[i]=vn;this.lastModalForce[i]=f;
  }
  this.radiationLossJ+=rad;this.structuralLossJ+=local;this.lossJ+=rad+local;this.workJ+=work;
 }
}
export class SharedBridgeNetwork{
 constructor(bridges,board,joints){
  if(bridges.length!==board.weights.length||joints.length!==bridges.length||bridges.some(b=>b.h!==board.h)||joints.some(j=>![j.k,j.c].every(x=>Number.isFinite(x)&&x>=0)))throw RangeError('network');
  this.bridges=bridges;this.board=board;this.h=board.h;this.joints=joints;this.lossJ=0;this.jointLossJ=0;
  this.gb=bridges.map(b=>this.h*this.h/2*b.hAxis.schur/b.det);
  this.active=joints.map((j,i)=>j.k/2+j.c/this.h>0?i:-1).filter(i=>i>=0);
  this.a=joints.map(j=>j.k/2+j.c/this.h);
  const matrix=this.active.map(i=>this.active.map(j=>.5*(board.portG[i][j]+board.portG[j][i])+(i===j?this.gb[i]+1/this.a[i]:0)));
  this.L=matrix.length?cholesky(matrix):[];
  this.zero=bridges.map(b=>b.wires.map(()=>0));
 }
 relative(){const p=this.board.positions();return this.bridges.map((b,i)=>b.vAxis.b-p[i]);}
 energy(){const r=this.relative();return this.board.energy()+this.bridges.reduce((s,b,i)=>s+b.energy()+.5*this.joints[i].k*r[i]**2,0);}
 step(){
  const r0=this.relative(),free=this.board.freePorts(),h=this.h,old=this.board.lossJ+this.bridges.reduce((s,b)=>s+b.lossJ,0);
  const rf=this.bridges.map((b,i)=>b.vAxis.b+h*b.predict(this.zero[i],this.zero[i]).mv-free[i]);
  const rhs=this.active.map(i=>-this.joints[i].k*r0[i]/this.a[i]-(rf[i]-r0[i]));
  const f=this.bridges.map(()=>0),sol=this.active.length?solveCholesky(this.L,rhs):[];
  this.active.forEach((i,k)=>f[i]=sol[k]);
  this.bridges.forEach((b,i)=>b.step(this.zero[i],this.zero[i],f[i],0));this.board.stepPorts(f.map(x=>-x));
  const r1=this.relative(),joint=this.joints.reduce((s,j,i)=>s+j.c*(r1[i]-r0[i])**2/h,0);
  this.jointLossJ+=joint;this.lossJ+=this.board.lossJ+this.bridges.reduce((s,b)=>s+b.lossJ,0)-old+joint;
  return f;
 }
}
export function seedPartial(bridge,wireIndex,partial,energyJ){
 if(!Number.isFinite(energyJ)||energyJ<=0)throw RangeError('seed energy');
 const a=bridge.vAxis,i=a.modes.findIndex(m=>m.j===wireIndex&&m.n===partial);if(i<0)throw RangeError('partial missing');
 if(bridge.energy()!==0)throw Error('seed requires resting bridge');
 a.v[i]=Math.sqrt(2*energyJ/a.modes[i].m);
}
