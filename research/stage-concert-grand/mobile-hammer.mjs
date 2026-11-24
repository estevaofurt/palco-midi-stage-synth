import {memoryEnergy,relaxMemory,frozenMemoryForce} from './felt-memory.mjs';
// F5.2: shared nonlinear hammer coupled to moving boundary through reciprocal contact compliance.
export function contactCompliance(bridge){
  const n=bridge.wires.length,h=bridge.h,d=Array(n).fill(0),t=Array(n).fill(.13);
  for(const m of bridge.modes){d[m.j]+=m.weight*m.weight/m.A;t[m.j]-=m.B*m.weight/m.A;}
  return d.map((v,i)=>d.map((_,j)=>h*h/2*((i===j?v:0)+t[i]*t[j]/bridge.schur)));
}

export function freeContacts(bridge){
  const h=bridge.h,v0=bridge.vb;
  let rhs=bridge.mB*v0-h*bridge.kB*bridge.b/2;
  const rr=bridge.modes.map((m,i)=>{const v=m.m*bridge.v[i]+m.cross*v0-h*m.k*bridge.x[i]/2;rhs+=m.cross*bridge.v[i]-m.B*v/m.A;return v;});
  const midB=rhs/bridge.schur,positions=bridge.wires.map((_,j)=>bridge.contactDisplacement(j)+.13*h*midB);
  for(let i=0;i<rr.length;i++){const m=bridge.modes[i];positions[m.j]+=h*m.weight*(rr[i]-m.B*midB)/m.A;}
  return positions;
}

export function solveCoupledContact(d0,free,C,z,p){
  const n=d0.length;
  if(n!==3||free.length!==n||z.length!==n||C.length!==n||C.some((row,i)=>row.length!==n||row.some((v,j)=>!Number.isFinite(v)||v<0||Math.abs(v-C[j][i])>1e-15)||row[i]<=0))throw new RangeError('nonnegative symmetric compliance required');
  const law=(i,x)=>frozenMemoryForce(d0[i],x,z[i],p),initial=free.map((x,i)=>law(i,x));
  if(initial.some(x=>!Number.isFinite(x)||x<0))throw new RangeError('contact force');
  const residual=f=>Math.max(...f.map((v,i)=>Math.abs(v-law(i,free[i]-C[i].reduce((s,c,j)=>s+c*f[j],0)))));
  if(initial.every(x=>x===0))return {forces:initial,residual:0,method:'open',iterations:0};
  const bound=Math.max(...free.map((x,i)=>{const hi=Math.max(0,x,d0[i]),hm=Math.max(0,x-z[i],d0[i]-z[i]);return C[i].reduce((s,c)=>s+c,0)*p.power*(p.ke*hi**(p.power-1)+p.km*hm**(p.power-1));}));
  let f=initial.slice();
  if(bound<=.5){for(let i=0;i<64;i++){const q=f.map((_,j)=>law(j,free[j]-C[j].reduce((s,c,k)=>s+c*f[k],0))),err=Math.max(...q.map((v,j)=>Math.abs(v-f[j])));if(err<1e-10)return {forces:f,residual:err,method:'contraction',iterations:i+1};f=q;}}
  // Nonnegative symmetric positive-definite physical compliance; coordinate roots.
  // Stop on full residual, not only coordinate changes. Fail closed if not converged.
  for(let sweep=0;sweep<256;sweep++){
    for(let i=0;i<n;i++){const x=free[i]-C[i].reduce((s,c,j)=>s+(j===i?0:c*f[j]),0);let lo=0,hi=law(i,x);for(let k=0;k<44;k++){const m=(lo+hi)/2;if(m>law(i,x-C[i][i]*m))hi=m;else lo=m;}f[i]=(lo+hi)/2;}
    const e=residual(f);if(e<1e-9)return {forces:f,residual:e,method:'coordinate',iterations:sweep+1};
  }
  throw Error('coupled contact did not converge');
}

export class MobileMemoryHammer {
  constructor(bridge,{massKg=.01,velocityMps=1,gapM=.0002,offsets=[0,0,0],felt={ke:1.4e9,km:.6e9,kr:1000,viscosity:1,power:2.5}}={}){
    if(bridge.wires.length!==3||![massKg,velocityMps].every(v=>Number.isFinite(v)&&v>0)||!Number.isFinite(gapM)||gapM<0||offsets.length!==3||offsets.some(v=>!Number.isFinite(v)||v<0))throw new RangeError('hammer setup');
    this.bridge=bridge;this.h=bridge.h;this.massKg=massKg;this.x=-gapM;this.v=velocityMps;this.offsets=offsets.slice();this.felt={...felt};relaxMemory(0,0,this.h/2,this.felt);
    this.z=[0,0,0];this.lossJ=0;this.impulseNs=0;this.time=0;this.lastResidual=0;this.methods={open:0,contraction:0,coordinate:0};
    const hm=this.h*this.h/(2*massKg);this.G=contactCompliance(bridge);this.C=this.G.map(row=>row.map(v=>v+hm));
  }
  compression(){return this.offsets.map((g,i)=>this.x-g-this.bridge.contactDisplacement(i));}
  energy(){return .5*this.massKg*this.v*this.v+this.bridge.energy()+this.compression().reduce((s,d,i)=>s+memoryEnergy(d,this.z[i],this.felt),0);}
  step(){
    const h=this.h,d0=this.compression(),free=freeContacts(this.bridge).map((x,i)=>this.x+h*this.v-this.offsets[i]-x),p=this.felt;
    let loss=0;const zmid=this.z.map((z,i)=>{const q=relaxMemory(d0[i],z,h/2,p);loss+=q.lossJ;return q.z;});
    const q=solveCoupledContact(d0,free,this.C,zmid,p),f=q.forces,sum=f.reduce((a,b)=>a+b,0);this.methods[q.method]++;
    this.x+=h*this.v-h*h*sum/(2*this.massKg);this.v-=h*sum/this.massKg;this.bridge.step(f);
    const d1=this.compression();this.lastResidual=Math.max(...f.map((v,i)=>Math.abs(v-frozenMemoryForce(d0[i],d1[i],zmid[i],p))));
    this.z=zmid.map((z,i)=>{const q=relaxMemory(d1[i],z,h/2,p);loss+=q.lossJ;return q.z;});
    this.lossJ+=loss;this.impulseNs+=h*sum;this.time+=h;
    return {forces:f,sum,compression:d1,loss};
  }
}
