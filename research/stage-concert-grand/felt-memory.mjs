import {feltPotential,feltSecant,HammerTrichord} from './hammer-contact.mjs';
// F4.2 nonlinear unilateral equilibrium and relaxing branch; split passive integration.
export function memoryEnergy(d,z,p){return feltPotential(d,p.ke,p.power)+feltPotential(d-z,p.km,p.power)+.5*p.kr*z*z;}

export function relaxMemory(d,z,h,p){
  if(![d,z,h,p.ke,p.km,p.kr,p.viscosity,p.power].every(Number.isFinite)||z<0||h<=0||p.ke<=0||p.km<0||p.kr<=0||p.viscosity<=0||p.power<1||h*p.kr>2*p.viscosity)throw new RangeError('memory domain');
  const f0=p.km*Math.max(0,d-z)**p.power;
  const residual=q=>q-z-h/p.viscosity*(feltSecant(d-z,d-q,p.km,p.power)-p.kr*(z+q)/2);
  let lo=0,hi=z+h*f0/p.viscosity;
  if(!Number.isFinite(hi))throw new RangeError('memory overflow');
  if(hi===0)return {z:0,lossJ:0,residualJ:0};
  for(let i=0;i<48;i++){const m=(lo+hi)/2;if(residual(m)>0)hi=m;else lo=m;}
  const next=(lo+hi)/2,lossJ=p.viscosity*(next-z)**2/h;
  return {z:next,lossJ,residualJ:memoryEnergy(d,z,p)-memoryEnergy(d,next,p)-lossJ};
}

export function frozenMemoryForce(d0,d1,z,p){return feltSecant(d0,d1,p.ke,p.power)+feltSecant(d0-z,d1-z,p.km,p.power);}

export function solveFrozen(d0,free,g,z,p){
  let lo=0,hi=frozenMemoryForce(d0,free,z,p);
  if(!Number.isFinite(hi)||hi<0||!Number.isFinite(g)||g<=0)throw new RangeError('contact domain');
  if(hi===0)return 0;
  for(let i=0;i<36;i++){const m=(lo+hi)/2;if(m>frozenMemoryForce(d0,free-g*m,z,p))hi=m;else lo=m;}
  return (lo+hi)/2;
}

export class MemoryHammer extends HammerTrichord {
  constructor(tri,{equilibriumK=1.4e9,memoryK=.6e9,recoveryK=1000,viscosity=1,power=2.5,...rest}={}){
    super(tri,{...rest,power,kNPerMPower:equilibriumK,rateFactorSPerM:0});
    this.felt={ke:equilibriumK,km:memoryK,kr:recoveryK,viscosity,power};
    relaxMemory(0,0,this.h/2,this.felt);this.z=[0,0,0];this.maxRelaxResidualJ=0;
  }
  energy(){return .5*this.massKg*this.v**2+this.tri.energy()+this.compression().reduce((a,d,i)=>a+memoryEnergy(d,this.z[i],this.felt),0);}
  step(){
    const h=this.h,hm=h*h/(2*this.massKg),x0=this.x,v0=this.v,d0=this.compression(),p=this.felt;
    let loss=0;
    const relax=ds=>{for(let i=0;i<3;i++){const q=relaxMemory(ds[i],this.z[i],h/2,p);this.z[i]=q.z;loss+=q.lossJ;this.maxRelaxResidualJ=Math.max(this.maxRelaxResidualJ,Math.abs(q.residualJ));}};
    relax(d0);
    const free=this.tri.strings.map((s,i)=>{
      let x=0;for(let n=0;n<s.vertical.modes.length;n++){const c=s.vertical.modes[n].coeff;x+=s.weightsV[n]*(c.A*s.vertical.x[n]+c.S*s.vertical.v[n]);}
      return x0+h*v0-this.gaps[i]-x;
    });
    const contactsAt=sum=>free.map((d,i)=>solveFrozen(d0[i],d-hm*sum,this.g[i],this.z[i],p));
    let lo=0,hi=contactsAt(0).reduce((a,b)=>a+b,0),forces;
    if(hi===0)forces=[0,0,0];
    else{for(let i=0;i<32;i++){const m=(lo+hi)/2,f=contactsAt(m).reduce((a,b)=>a+b,0);if(m>f)hi=m;else lo=m;}forces=contactsAt((lo+hi)/2);}
    const sum=forces.reduce((a,b)=>a+b,0);
    this.x=x0+h*v0-hm*sum;this.v=v0-h*sum/this.massKg;
    this.tri.step(forces.map(verticalN=>({verticalN,horizontalN:0})));
    const d1=this.compression();
    this.lastResidual=Math.max(...forces.map((f,i)=>Math.abs(f-frozenMemoryForce(d0[i],d1[i],this.z[i],p))));
    relax(d1);
    this.contactLossJ+=loss;this.impulseNs+=h*sum;this.lastForces=forces;this.time+=h;
    return {forces,sum,compression:d1,loss};
  }
}
