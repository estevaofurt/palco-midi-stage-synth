import {MovingBridge} from './moving-bridge.mjs';
import {solveCoupledContact} from './mobile-hammer.mjs';
import {memoryEnergy,relaxMemory,frozenMemoryForce} from './felt-memory.mjs';
// F5.3 two physical polarizations and rotated passive bridge tensors; offline reference.
export function rotatedTensor(a,b,angle){
  if(![a,b,angle].every(Number.isFinite)||a<0||b<0)throw new RangeError('tensor');
  const c=Math.cos(angle),s=Math.sin(angle);
  return {vv:a*c*c+b*s*s,hh:a*s*s+b*c*c,vh:(a-b)*c*s};
}

export class PolarizedBridge {
  constructor(wires,{sampleRate=192000,maxFrequencyHz=16000,massKg=.025,stiffness=[1e6,2e6],damping=[20,5],angleRad=.25,verticalLoss=[.4,.0002],horizontalLoss=[.2,.00012]}={},helpers){
    this.K=rotatedTensor(...stiffness,angleRad);this.C=rotatedTensor(...damping,angleRad);
    this.h=1/sampleRate;this.wires=wires;this.workJ=0;this.lossJ=0;this.bridgeLossJ=0;this.stringLossJ=0;
    const common={sampleRate,maxFrequencyHz,bridgeMassKg:massKg};
    this.vAxis=new MovingBridge(wires,{...common,bridgeK:this.K.vv,bridgeC:this.C.vv,sigma0:verticalLoss[0],sigma2:verticalLoss[1]},helpers);
    this.hAxis=new MovingBridge(wires,{...common,bridgeK:this.K.hh,bridgeC:this.C.hh,sigma0:horizontalLoss[0],sigma2:horizontalLoss[1]},helpers);
    const h=this.h;this.crossA=h*this.C.vh/2+h*h*this.K.vh/4;
    this.det=this.vAxis.schur*this.hAxis.schur-this.crossA*this.crossA;
    if(!(this.det>0&&Number.isFinite(this.det)))throw new RangeError('bridge Schur');
  }
  energy(){return this.vAxis.energy()+this.hAxis.energy()+this.K.vh*this.vAxis.b*this.hAxis.b;}
  wireEnergy(axis,j){return (axis==='v'?this.vAxis:this.hAxis).wireEnergy(j);}
  contactDisplacement(j){return this.vAxis.contactDisplacement(j);}
  predict(fv,fh,bv=0,bh=0){
    const h=this.h;
    const reduce=(a,f,b,other)=>{
      let rhs=a.mB*a.vb+h*(b+.13*f.reduce((s,v)=>s+v,0)-a.kB*a.b-this.K.vh*other.b)/2;
      const rr=a.modes.map((m,i)=>{const v=m.m*a.v[i]+m.cross*a.vb+h*(m.weight*f[m.j]-m.k*a.x[i])/2;rhs+=m.cross*a.v[i]-m.B*v/m.A;return v;});
      return {rhs,rr};
    };
    const v=reduce(this.vAxis,fv,bv,this.hAxis),u=reduce(this.hAxis,fh,bh,this.vAxis);
    return {mv:(v.rhs*this.hAxis.schur-this.crossA*u.rhs)/this.det,mh:(u.rhs*this.vAxis.schur-this.crossA*v.rhs)/this.det,rv:v.rr,rh:u.rr};
  }
  freeContacts(){
    const zero=this.wires.map(()=>0),q=this.predict(zero,zero),a=this.vAxis,h=this.h;
    const y=this.wires.map((_,j)=>a.contactDisplacement(j)+.13*h*q.mv);
    for(let i=0;i<a.modes.length;i++){const m=a.modes[i];y[m.j]+=h*m.weight*(q.rv[i]-m.B*q.mv)/m.A;}
    return y;
  }
  contactCompliance(){
    const a=this.vAxis,n=this.wires.length,d=Array(n).fill(0),t=Array(n).fill(.13);
    for(const m of a.modes){d[m.j]+=m.weight*m.weight/m.A;t[m.j]-=m.B*m.weight/m.A;}
    return d.map((v,i)=>d.map((_,j)=>this.h*this.h/2*((i===j?v:0)+t[i]*t[j]*this.hAxis.schur/this.det)));
  }
  step(fv=this.wires.map(()=>0),fh=this.wires.map(()=>0),bv=0,bh=0){
    if(fv.length!==this.wires.length||fh.length!==this.wires.length||![...fv,...fh,bv,bh].every(Number.isFinite))throw new RangeError('forces');
    const {mv,mh}=this.predict(fv,fh,bv,bh),h=this.h,v=this.vAxis,u=this.hAxis;
    const crossV=-this.K.vh*(u.b+h*mh/2)-this.C.vh*mh,crossH=-this.K.vh*(v.b+h*mv/2)-this.C.vh*mv;
    const w0=v.workJ+u.workJ,d0=v.lossJ+u.lossJ,s0=v.stringLossJ+u.stringLossJ;
    v.step(fv,bv+crossV);u.step(fh,bh+crossH);
    this.workJ+=v.workJ+u.workJ-w0-h*(crossV*mv+crossH*mh);
    this.lossJ+=v.lossJ+u.lossJ-d0+2*h*this.C.vh*mv*mh;
    this.stringLossJ+=v.stringLossJ+u.stringLossJ-s0;
    this.bridgeLossJ+=h*(this.C.vv*mv*mv+2*this.C.vh*mv*mh+this.C.hh*mh*mh);
  }
  mobility(f){
    if(!Number.isFinite(f)||f<=0)throw new RangeError('frequency');
    const w=2*Math.PI*f;
    const diag=a=>{let re=a.kB-w*w*a.mB,im=w*a.cB;
      for(const m of a.modes){const ar=m.k-w*w*m.m,ai=w*m.c,br=-w*w*m.cross,bi=w*m.cc,den=ar*ar+ai*ai;if(den===0)throw new RangeError('singular');const nr=br*br-bi*bi,ni=2*br*bi;re-=(nr*ar+ni*ai)/den;im-=(ni*ar-nr*ai)/den;}return [re,im];};
    const mul=([a,b],[c,d])=>[a*c-b*d,a*d+b*c],sub=([a,b],[c,d])=>[a-c,b-d],div=([a,b],[c,d])=>[(a*c+b*d)/(c*c+d*d),(b*c-a*d)/(c*c+d*d)];
    const v=diag(this.vAxis),u=diag(this.hAxis),c=[this.K.vh,w*this.C.vh],det=sub(mul(v,u),mul(c,c));
    const vv=div(mul([0,w],u),det),hh=div(mul([0,w],v),det),vh=div(mul([0,-w],c),det);
    return {f,vv,hh,vh,realDet:vv[0]*hh[0]-vh[0]*vh[0],crossMagnitude:Math.hypot(...vh)};
  }
}

export class PolarizedHammer {
  constructor(bridge,{massKg=.01,velocityMps=1,gapM=.0002,offsets=[0,0,0],felt={ke:1.4e9,km:.6e9,kr:1000,viscosity:1,power:2.5}}={}){
    if(bridge.wires.length!==3||![massKg,velocityMps].every(v=>Number.isFinite(v)&&v>0)||!Number.isFinite(gapM)||gapM<0||offsets.length!==3||offsets.some(v=>!Number.isFinite(v)||v<0))throw new RangeError('hammer');
    this.bridge=bridge;this.h=bridge.h;this.massKg=massKg;this.x=-gapM;this.v=velocityMps;this.offsets=offsets.slice();this.felt={...felt};relaxMemory(0,0,this.h/2,this.felt);
    this.z=[0,0,0];this.lossJ=0;this.impulseNs=0;this.time=0;this.lastResidual=0;const hm=this.h*this.h/(2*massKg);this.C=bridge.contactCompliance().map(row=>row.map(v=>v+hm));
  }
  compression(){return this.offsets.map((g,i)=>this.x-g-this.bridge.contactDisplacement(i));}
  energy(){return .5*this.massKg*this.v*this.v+this.bridge.energy()+this.compression().reduce((s,d,i)=>s+memoryEnergy(d,this.z[i],this.felt),0);}
  step(){
    const h=this.h,d0=this.compression(),free=this.bridge.freeContacts().map((x,i)=>this.x+h*this.v-this.offsets[i]-x),p=this.felt;
    let loss=0;const zmid=this.z.map((z,i)=>{const q=relaxMemory(d0[i],z,h/2,p);loss+=q.lossJ;return q.z;});
    const q=solveCoupledContact(d0,free,this.C,zmid,p),f=q.forces,sum=f.reduce((a,b)=>a+b,0);
    this.x+=h*this.v-h*h*sum/(2*this.massKg);this.v-=h*sum/this.massKg;this.bridge.step(f);
    const d1=this.compression();this.lastResidual=Math.max(...f.map((v,i)=>Math.abs(v-frozenMemoryForce(d0[i],d1[i],zmid[i],p))));
    this.z=zmid.map((z,i)=>{const q=relaxMemory(d1[i],z,h/2,p);loss+=q.lossJ;return q.z;});
    this.lossJ+=loss;this.impulseNs+=h*sum;this.time+=h;return {forces:f,sum,compression:d1,loss};
  }
}
