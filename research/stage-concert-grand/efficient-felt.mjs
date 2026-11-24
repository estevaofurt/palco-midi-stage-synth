import {MemoryHammer,frozenMemoryForce,relaxMemory} from './felt-memory.mjs';
// F4.3: contraction-bounded contact solver, exact same constitutive model, bisection fallback.
export function solveThreeContacts(d0,free,g,hm,z,p,{referenceOnly=false}={}){
  let evaluations=0;
  const law=(i,d)=>{evaluations++;return frozenMemoryForce(d0[i],d,z[i],p);};
  const initial=free.map((d,i)=>law(i,d));
  if(!initial.every(f=>Number.isFinite(f)&&f>=0)||!Number.isFinite(hm)||hm<=0||!g.every(v=>Number.isFinite(v)&&v>0))throw new RangeError('contact inputs');
  if(initial.every(f=>f===0))return {forces:initial,evaluations,method:'open',bound:0};
  // For nonnegative force, compression is no greater than free. Secant derivative
  // bounded by maximum derivative of the point force on that interval.
  const bound=Math.max(...free.map((d,i)=>{
    const top=Math.max(0,d,d0[i]),mem=Math.max(0,d-z[i],d0[i]-z[i]);
    return (g[i]+3*hm)*p.power*(p.ke*top**(p.power-1)+p.km*mem**(p.power-1));
  }));
  if(!referenceOnly&&bound<=.5){
    let f=initial;
    for(let j=0;j<64;j++){
      const sum=f.reduce((a,b)=>a+b,0),next=free.map((d,i)=>law(i,d-g[i]*f[i]-hm*sum));
      const residual=Math.max(...next.map((v,i)=>Math.abs(v-f[i])));
      if(residual<=1e-11)return {forces:f,evaluations,method:'contraction',bound};
      f=next;
    }
  }
  const contactsAt=sum=>free.map((d,i)=>{
    const x=d-hm*sum;let lo=0,hi=law(i,x);
    if(hi===0)return 0;
    for(let j=0;j<36;j++){const m=(lo+hi)/2;if(m>law(i,x-g[i]*m))hi=m;else lo=m;}
    return (lo+hi)/2;
  });
  let lo=0,hi=contactsAt(0).reduce((a,b)=>a+b,0);
  for(let j=0;j<32;j++){const m=(lo+hi)/2,f=contactsAt(m).reduce((a,b)=>a+b,0);if(m>f)hi=m;else lo=m;}
  return {forces:contactsAt((lo+hi)/2),evaluations,method:'bisection',bound};
}

export class EfficientMemoryHammer extends MemoryHammer {
  constructor(tri,{referenceOnly=false,...params}={}){
    super(tri,params);this.referenceOnly=referenceOnly;this.evaluations=0;this.methods={open:0,contraction:0,bisection:0};
  }
  step(){
    const h=this.h,hm=h*h/(2*this.massKg),x0=this.x,v0=this.v,d0=this.compression(),p=this.felt;
    let loss=0;
    const relax=ds=>{for(let i=0;i<3;i++){const q=relaxMemory(ds[i],this.z[i],h/2,p);this.z[i]=q.z;loss+=q.lossJ;this.maxRelaxResidualJ=Math.max(this.maxRelaxResidualJ,Math.abs(q.residualJ));}};
    relax(d0);
    const free=this.tri.strings.map((s,i)=>{
      let x=0;for(let n=0;n<s.vertical.modes.length;n++){const c=s.vertical.modes[n].coeff;x+=s.weightsV[n]*(c.A*s.vertical.x[n]+c.S*s.vertical.v[n]);}
      return x0+h*v0-this.gaps[i]-x;
    });
    const result=solveThreeContacts(d0,free,this.g,hm,this.z,p,{referenceOnly:this.referenceOnly});
    this.evaluations+=result.evaluations;this.methods[result.method]++;
    const forces=result.forces,sum=forces.reduce((a,b)=>a+b,0);
    this.x=x0+h*v0-hm*sum;this.v=v0-h*sum/this.massKg;
    this.tri.step(forces.map(verticalN=>({verticalN,horizontalN:0})));
    const d1=this.compression();
    this.lastResidual=Math.max(...forces.map((f,i)=>Math.abs(f-frozenMemoryForce(d0[i],d1[i],this.z[i],p))));
    relax(d1);this.contactLossJ+=loss;this.impulseNs+=h*sum;this.lastForces=forces;this.time+=h;
    return {forces,sum,compression:d1,loss};
  }
}
