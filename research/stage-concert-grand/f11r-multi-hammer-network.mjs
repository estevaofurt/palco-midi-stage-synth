import {SharedBridgeNetwork} from './f9-shared-board.mjs';
import {solveCholesky,cholesky} from './radiation-loading.mjs';
import {frozenMemoryForce,relaxMemory,memoryEnergy} from './felt-memory.mjs';
// All contacts solved against the same board state and all other hammers.
// Passive shared-board laboratory, not an optimized product engine.
export class MultiHammerNetwork extends SharedBridgeNetwork{
 constructor(bridges,board,joints){
  super(bridges,board,joints);
  this.contacts=bridges.flatMap((b,g)=>b.wires.map((_,j)=>({g,j})));
  this.cross=bridges.map((b,g)=>{const a=b.vAxis,t=b.wires.map(()=>.13);for(const m of a.modes)t[m.j]-=m.B*m.weight/m.A;return t.map(v=>this.gb[g]*v);});
  const inv=this.active.map((_,i)=>solveCholesky(this.L,this.active.map((_,j)=>+(i===j))));
  const local=bridges.map(b=>b.contactCompliance());
  this.G=this.contacts.map(({g,j})=>this.contacts.map(({g:k,j:l})=>{
   const a=this.active.indexOf(g),b=this.active.indexOf(k);
   return (g===k?local[g][j][l]:0)-(a<0||b<0?0:this.cross[g][j]*inv[a][b]*this.cross[k][l]);
  }));
  for(let i=0;i<this.G.length;i++)for(let j=0;j<i;j++){const a=this.G[i][j],b=this.G[j][i];if(Math.abs(a-b)>1e-15)throw Error('contact reciprocity');this.G[i][j]=this.G[j][i]=(a+b)/2;}
  cholesky(this.G);
 }
 displacement(){return this.contacts.map(({g,j})=>this.bridges[g].contactDisplacement(j));}
 predictJoints(forces=this.zero){
  const r0=this.relative(),free=this.board.freePorts(),h=this.h;
  const rf=this.bridges.map((b,i)=>b.vAxis.b+h*b.predict(forces[i],this.zero[i]).mv-free[i]);
  const rhs=this.active.map(i=>-this.joints[i].k*r0[i]/this.a[i]-(rf[i]-r0[i]));
  const f=this.bridges.map(()=>0),sol=this.active.length?solveCholesky(this.L,rhs):[];
  this.active.forEach((i,k)=>f[i]=sol[k]);return {f,r0};
 }
 freeContacts(){const {f}=this.predictJoints();const free=this.bridges.map(b=>b.freeContacts());return this.contacts.map(({g,j})=>free[g][j]+this.cross[g][j]*f[g]);}
 step(forces=this.zero){
  if(forces.length!==this.bridges.length||forces.some((f,i)=>f.length!==this.zero[i].length||!f.every(Number.isFinite)))throw RangeError('forces');
  const old=this.board.lossJ+this.bridges.reduce((s,b)=>s+b.lossJ,0),{f,r0}=this.predictJoints(forces),h=this.h;
  this.bridges.forEach((b,i)=>b.step(forces[i],this.zero[i],f[i],0));this.board.stepPorts(f.map(x=>-x));
  const r1=this.relative(),loss=this.joints.reduce((s,j,i)=>s+j.c*(r1[i]-r0[i])**2/h,0);
  this.jointLossJ+=loss;this.lossJ+=this.board.lossJ+this.bridges.reduce((s,b)=>s+b.lossJ,0)-old+loss;
 }
}
export function solveMultiContact(d0,free,C,z,params){
 const n=d0.length;
 if(!n||free.length!==n||z.length!==n||params.length!==n||C.length!==n||C.some((r,i)=>r.length!==n||r.some((v,j)=>!Number.isFinite(v)||Math.abs(v-C[j][i])>1e-15)||r[i]<=0))throw RangeError('contact matrix');
 const law=(i,x)=>frozenMemoryForce(d0[i],x,z[i],params[i]),f=Array(n).fill(0);
 const residual=()=>Math.max(...f.map((v,i)=>Math.abs(v-law(i,free[i]-C[i].reduce((s,c,j)=>s+c*f[j],0)))));
 for(let sweep=0;sweep<256;sweep++){
  for(let i=0;i<n;i++){
   const x=free[i]-C[i].reduce((s,c,j)=>s+(j===i?0:c*f[j]),0);
   let lo=0,hi=law(i,x);if(!Number.isFinite(hi)||hi<0)throw Error('force bound');
   for(let k=0;k<44;k++){const m=(lo+hi)/2;if(m>law(i,x-C[i][i]*m))hi=m;else lo=m;}f[i]=(lo+hi)/2;
  }
  const err=residual();if(err<1e-9)return {forces:f,residual:err};
 }
 throw Error('multi contact convergence');
}
export class SimultaneousHammers{
 constructor(network,options){
  if(options.length!==network.bridges.length)throw RangeError('hammer count');
  this.network=network;this.h=network.h;this.lossJ=0;this.lastResidual=0;
  this.hammers=options.map(({massKg=.01,velocityMps=1,gapM=.0002,felt})=>{
   if(![massKg,velocityMps].every(x=>Number.isFinite(x)&&x>0)||!Number.isFinite(gapM)||gapM<0)throw RangeError('hammer');
   relaxMemory(0,0,this.h/2,felt);return {massKg,x:-gapM,v:velocityMps,felt};
  });
  this.z=network.contacts.map(()=>0);
  this.C=network.G.map((r,i)=>r.map((v,j)=>v+(network.contacts[i].g===network.contacts[j].g?this.h*this.h/(2*this.hammers[network.contacts[i].g].massKg):0)));
  cholesky(this.C);
 }
 compression(){return this.network.displacement().map((x,i)=>this.hammers[this.network.contacts[i].g].x-x);}
 energy(){return this.network.energy()+this.hammers.reduce((s,h)=>s+.5*h.massKg*h.v*h.v,0)+this.compression().reduce((s,d,i)=>s+memoryEnergy(d,this.z[i],this.hammers[this.network.contacts[i].g].felt),0);}
 step(){
  const h=this.h,contacts=this.network.contacts,d0=this.compression(),p=contacts.map(({g})=>this.hammers[g].felt);
  const free=this.network.freeContacts().map((x,i)=>{const a=this.hammers[contacts[i].g];return a.x+h*a.v-x;});
  const zmid=this.z.map((z,i)=>{const q=relaxMemory(d0[i],z,h/2,p[i]);this.lossJ+=q.lossJ;return q.z;});
  const q=solveMultiContact(d0,free,this.C,zmid,p),forces=this.network.zero.map(r=>r.slice());
  contacts.forEach(({g,j},i)=>forces[g][j]=q.forces[i]);
  this.hammers.forEach((a,g)=>{const sum=forces[g].reduce((s,f)=>s+f,0);a.x+=h*a.v-h*h*sum/(2*a.massKg);a.v-=h*sum/a.massKg;});
  this.network.step(forces);
  const d1=this.compression();
  this.lastResidual=Math.max(...q.forces.map((v,i)=>Math.abs(v-frozenMemoryForce(d0[i],d1[i],zmid[i],p[i]))));
  this.z=zmid.map((z,i)=>{const q=relaxMemory(d1[i],z,h/2,p[i]);this.lossJ+=q.lossJ;return q.z;});
  return forces;
 }
}
