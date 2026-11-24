// F2.2 exact local linear transition for constant force and passive two-mode coupling prototype. Offline; not an audio engine.
export function modalCoefficients({massKg,frequencyHz,dampingNsM,dt}){
  if(![massKg,frequencyHz,dt].every(v=>Number.isFinite(v)&&v>0)||!Number.isFinite(dampingNsM)||dampingNsM<0)throw new RangeError('invalid mode');
  const w=2*Math.PI*frequencyHz,alpha=dampingNsM/(2*massKg),a=alpha*dt,b=(w*dt)**2,k=massKg*w*w;
  if(![w,alpha,a,b,k].every(Number.isFinite)||k<=0||a>50||b>100)throw new RangeError('outside reference numerical domain');
  const z=a*a-b;let C,S;
  if(Math.abs(z)<1e-8){C=Math.exp(-a)*(1+z/2+z*z/24);S=Math.exp(-a)*dt*(1+z/6+z*z/120);}
  else if(z<0){const t=Math.sqrt(-z);C=Math.exp(-a)*Math.cos(t);S=Math.exp(-a)*dt*Math.sin(t)/t;}
  else {const t=Math.sqrt(z),slow=-b/(a+t),fast=-a-t;const e1=Math.exp(slow),e2=Math.exp(fast);C=(e1+e2)/2;S=dt*(e1-e2)/(2*t);}
  const A=C+alpha*S,D=C-alpha*S,H=-w*w*S;
  let G;
  if(Math.max(a,Math.sqrt(b))<.05){
    let prev=0,cur=.5,sum=cur;
    for(let n=1;n<18;n++){const next=(-2*a*(n+1)*cur-b*prev)/((n+2)*(n+1));sum+=next;prev=cur;cur=next;}
    G=dt*dt*sum/massKg;
  }else if(z>1e-8){
    const t=Math.sqrt(z),slow=-b/(a+t),fast=-a-t;
    G=dt*dt*(Math.expm1(slow)/slow-Math.expm1(fast)/fast)/(2*t*massKg);
  }else G=(1-A)/k;
  const J=S/massKg;
  if(![A,S,H,D,G,J].every(Number.isFinite)||G<0)throw new RangeError('invalid transition');
  return {massKg,frequencyHz,dampingNsM,dt,k,A,S,H,D,G,J};
}

export function advanceMode(p,x,v,force=0){
  if(![x,v,force].every(Number.isFinite))throw new RangeError('state or force');
  const xn=p.A*x+p.S*v+p.G*force,vn=p.H*x+p.D*v+p.J*force;
  if(![xn,vn].every(Number.isFinite))throw new RangeError('nonfinite state');
  return {x:xn,v:vn};
}

export function modeEnergy(p,x,v){return .5*(p.massKg*v*v+p.k*x*x);}

export function coupledPair(p,q,state,{springNPerM,dampingNsM,forceA=0,forceB=0}){
  if(p.dt!==q.dt||![springNPerM,dampingNsM].every(v=>Number.isFinite(v)&&v>=0))throw new RangeError('invalid coupling');
  const {xa,va,xb,vb}=state,h=p.dt,k=springNPerM,c=dampingNsM,r0=xa-xb;
  const a=advanceMode(p,xa,va,forceA),b=advanceMode(q,xb,vb,forceB),rf=a.x-b.x;
  const f=-(k*(r0+rf)/2+c*(rf-r0)/h)/(1+(k/2+c/h)*(p.G+q.G));
  const an=advanceMode(p,xa,va,forceA+f),bn=advanceMode(q,xb,vb,forceB-f);
  const da=an.x-xa,db=bn.x-xb,r1=an.x-bn.x;
  const lossA=(forceA+f)*da+modeEnergy(p,xa,va)-modeEnergy(p,an.x,an.v);
  const lossB=(forceB-f)*db+modeEnergy(q,xb,vb)-modeEnergy(q,bn.x,bn.v);
  return {xa:an.x,va:an.v,xb:bn.x,vb:bn.v,interactionForceN:f,workJ:forceA*da+forceB*db,localLossJ:lossA+lossB,edgeLossJ:c*(r1-r0)**2/h};
}

export function pairEnergy(p,q,s,k){return modeEnergy(p,s.xa,s.va)+modeEnergy(q,s.xb,s.vb)+.5*k*(s.xa-s.xb)**2;}
