// F4.1: discrete unilateral nonlinear felt, shared hammer free mass and three vertical contacts. Offline hypotheses.
export function feltPotential(d,k,p){return k*Math.max(0,d)**(p+1)/(p+1);}

export function feltSecant(a,b,k,p){
  if(a<=0&&b<=0)return 0;
  const hi=Math.max(a,b),lo=Math.min(a,b);
  if(hi===lo)return k*hi**p;
  if(lo<=0)return feltPotential(hi,k,p)/(hi-lo);
  const t=(lo-hi)/hi;
  return t===0?k*hi**p:k*hi**p*Math.expm1((p+1)*Math.log1p(t))/((p+1)*t);
}

export function solveContact(d0,free,g,h,k,p,eta){
  if(![d0,free,g,h,k,p,eta].every(Number.isFinite)||g<=0||h<=0||k<=0||p<1||eta<0)throw new RangeError('contact input');
  const law=d=>feltSecant(d0,d,k,p)*Math.max(0,1+eta*(d-d0)/h);
  let lo=0,hi=law(free);
  if(!Number.isFinite(hi))throw new RangeError('contact overflow');
  if(hi===0)return 0;
  for(let i=0;i<40;i++){const f=(lo+hi)/2;if(f>law(free-g*f))hi=f;else lo=f;}
  return (lo+hi)/2;
}

export class HammerTrichord {
  constructor(tri,{massKg=.010,kNPerMPower=2e9,power=2.5,rateFactorSPerM=.12,initialGapM=.0002,initialVelocityMps=1,gapOffsetsM=[0,0,0]}={}){
    if(![massKg,kNPerMPower,initialVelocityMps].every(v=>Number.isFinite(v)&&v>0)||!Number.isFinite(power)||power<1||power>5||!Number.isFinite(rateFactorSPerM)||rateFactorSPerM<0||!Number.isFinite(initialGapM)||initialGapM<0||!Array.isArray(gapOffsetsM)||gapOffsetsM.length!==3||gapOffsetsM.some(v=>!Number.isFinite(v)||v<0))throw new RangeError('hammer setup');
    this.tri=tri;this.massKg=massKg;this.k=kNPerMPower;this.p=power;this.eta=rateFactorSPerM;this.h=tri.strings[0].vertical.dt;this.gaps=gapOffsetsM.slice();
    this.x=-initialGapM;this.v=initialVelocityMps;this.contactLossJ=0;this.impulseNs=0;this.time=0;
    this.g=tri.strings.map(s=>s.vertical.modes.reduce((a,m,i)=>a+s.weightsV[i]**2*m.coeff.G,0));
    this.lastForces=[0,0,0];this.lastResidual=0;
    if(this.g.some(v=>!Number.isFinite(v)||v<=0))throw new RangeError('contact compliance');
  }
  compression(){return this.tri.strings.map((s,i)=>this.x-this.gaps[i]-s.vertical.projection(s.weightsV));}
  energy(){return .5*this.massKg*this.v**2+this.tri.energy()+this.compression().reduce((a,d)=>a+feltPotential(d,this.k,this.p),0);}
  step(){
    const h=this.h,hm=h*h/(2*this.massKg),x0=this.x,v0=this.v,d0=this.compression();
    const free=this.tri.strings.map((s,i)=>{
      let x=0;for(let n=0;n<s.vertical.modes.length;n++){const p=s.vertical.modes[n].coeff;x+=s.weightsV[n]*(p.A*s.vertical.x[n]+p.S*s.vertical.v[n]);}
      return x0+h*v0-this.gaps[i]-x;
    });
    const contactsAt=sum=>free.map((d,i)=>solveContact(d0[i],d-hm*sum,this.g[i],h,this.k,this.p,this.eta));
    let lo=0,hi=contactsAt(0).reduce((a,c)=>a+c,0),forces;
    if(hi===0)forces=[0,0,0];
    else{for(let i=0;i<36;i++){const mid=(lo+hi)/2,f=contactsAt(mid).reduce((a,c)=>a+c,0);if(mid>f)hi=mid;else lo=mid;}forces=contactsAt((lo+hi)/2);}
    const sum=forces.reduce((a,b)=>a+b,0);
    this.x=x0+h*v0-hm*sum;this.v=v0-h*sum/this.massKg;
    this.tri.step(forces.map(verticalN=>({verticalN,horizontalN:0})));
    const d1=this.compression();
    let loss=0,res=0;
    for(let i=0;i<3;i++){const change=d1[i]-d0[i],elastic=feltSecant(d0[i],d1[i],this.k,this.p);loss+=forces[i]*change-(feltPotential(d1[i],this.k,this.p)-feltPotential(d0[i],this.k,this.p));res=Math.max(res,Math.abs(forces[i]-elastic*Math.max(0,1+this.eta*change/h)));}
    this.contactLossJ+=loss;this.impulseNs+=h*sum;this.lastForces=forces;this.lastResidual=res;this.time+=h;
    return {forces,sum,compression:d1,loss};
  }
}
