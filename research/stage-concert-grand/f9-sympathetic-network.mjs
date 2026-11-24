import {SharedBridgeNetwork} from './f9-shared-board.mjs';
import {solveCholesky} from './radiation-loading.mjs';
// Single struck trichord, any additional unstruck groups. All forces solved simultaneously.
export class HammerSharedNetwork extends SharedBridgeNetwork{
 constructor(bridges,board,joints){
  super(bridges,board,joints);
  this.wires=bridges[0].wires;
  const a=bridges[0].vAxis,t=this.wires.map(()=>.13);
  for(const m of a.modes)t[m.j]-=m.B*m.weight/m.A;
  this.contactCross=t.map(v=>this.gb[0]*v);
  const j=this.active.indexOf(0),alpha=j<0?0:solveCholesky(this.L,this.active.map((_,i)=>+(i===j)))[j];
  this.G=bridges[0].contactCompliance().map((row,i)=>row.map((v,k)=>v-alpha*this.contactCross[i]*this.contactCross[k]));
  this.secondaryWorkInJ=0;this.secondaryWorkOutJ=0;
 }
 contactDisplacement(j){return this.bridges[0].contactDisplacement(j);}
 contactCompliance(){return this.G.map(r=>r.slice());}
 predictJoints(fv=this.zero[0]){
  const r0=this.relative(),free=this.board.freePorts(),h=this.h;
  const rf=this.bridges.map((b,i)=>b.vAxis.b+h*b.predict(i===0?fv:this.zero[i],this.zero[i]).mv-free[i]);
  const rhs=this.active.map(i=>-this.joints[i].k*r0[i]/this.a[i]-(rf[i]-r0[i]));
  const f=this.bridges.map(()=>0),sol=this.active.length?solveCholesky(this.L,rhs):[];
  this.active.forEach((i,k)=>f[i]=sol[k]);return {f,r0};
 }
 freeContacts(){const {f}=this.predictJoints();return this.bridges[0].freeContacts().map((x,i)=>x+this.contactCross[i]*f[0]);}
 step(fv=this.zero[0]){
  if(fv.length!==this.wires.length||!fv.every(Number.isFinite))throw RangeError('hammer forces');
  const old=this.board.lossJ+this.bridges.reduce((s,b)=>s+b.lossJ,0),{f,r0}=this.predictJoints(fv),before=this.bridges.map(b=>b.vAxis.b),h=this.h;
  this.bridges.forEach((b,i)=>b.step(i===0?fv:this.zero[i],this.zero[i],f[i],0));this.board.stepPorts(f.map(x=>-x));
  const r1=this.relative(),joint=this.joints.reduce((s,j,i)=>s+j.c*(r1[i]-r0[i])**2/h,0);
  this.jointLossJ+=joint;this.lossJ+=this.board.lossJ+this.bridges.reduce((s,b)=>s+b.lossJ,0)-old+joint;
  for(let i=1;i<this.bridges.length;i++){const work=f[i]*(this.bridges[i].vAxis.b-before[i]);if(work>=0)this.secondaryWorkInJ+=work;else this.secondaryWorkOutJ-=work;}
  return f;
 }
}
// Allocation-reduced version of SharedBoard, same reciprocal responses and loss accounting.
export function fastSharedBoard(board){
 const m=board.modes,n=m.length,h=board.h,dx=new Float64Array(n),base=new Float64Array(n),rhs=new Float64Array(n),weights=board.weights,units=board.responses;
 const blocks=board.blocks.map(b=>({i:Int32Array.from(b.indices),g:Float64Array.from(b.g),L:b.L.map(x=>Float64Array.from(x)),R:b.R.map(x=>Float64Array.from(x))}));
 let cached=false;
 function calc(){for(const b of blocks){const is=b.i,g=b.g,L=b.L,N=is.length;
  for(let j=0;j<N;j++){const i=is[j],q=m[i].coeff;let t=((q.A-1)*board.x[i]+q.S*board.v[i])/g[j];for(let k=0;k<j;k++)t-=L[j][k]*rhs[k];rhs[j]=t/L[j][j];}
  for(let j=N-1;j>=0;j--){let t=rhs[j];for(let k=j+1;k<N;k++)t-=L[k][j]*rhs[k];rhs[j]=t/L[j][j];base[is[j]]=g[j]*rhs[j];}
 }cached=true;}
 board.freePorts=()=>{if(!cached)calc();return weights.map(w=>{let pos=0,inc=0;for(let i=0;i<n;i++){pos+=w[i]*board.x[i];inc+=w[i]*base[i];}return pos+inc;});};
 board.stepPorts=forces=>{if(!cached)calc();for(let i=0;i<n;i++){let v=base[i];for(let j=0;j<forces.length;j++)v+=forces[j]*units[j][i];dx[i]=v;}
 let rad=0,local=0,work=0;for(const b of blocks){const is=b.i,N=is.length;for(let j=0;j<N;j++){const i=is[j],mode=m[i],q=mode.coeff,x=board.x[i],v=board.v[i],row=b.R[j];let z=0,F=0;for(let k=0;k<N;k++)z+=row[k]*dx[is[k]]/h;for(let k=0;k<forces.length;k++)F+=weights[k][i]*forces[k];const rf=-z,f=F+rf,xn=q.A*x+q.S*v+q.G*f,vn=q.H*x+q.D*v+q.J*f;
 rad-=rf*(xn-x);local+=f*(xn-x)+.5*(v*v-vn*vn+mode.lambda*(x*x-xn*xn));work+=F*(xn-x);board.x[i]=xn;board.v[i]=vn;board.lastModalForce[i]=f;}}
 board.radiationLossJ+=rad;board.structuralLossJ+=local;board.lossJ+=rad+local;board.workJ+=work;cached=false;};
}
