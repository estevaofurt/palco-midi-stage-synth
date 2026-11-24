import {MechanicalReference,midpointFrequency} from './mechanical-reference.mjs';
import {modalCoefficients,advanceMode,modeEnergy,coupledPair,pairEnergy} from './exact-modal.mjs';
function runChecks(Reference,midpointFrequency){
  const a=(v,m)=>{if(!v)throw Error(m)},near=(x,y,t)=>Math.abs(x-y)<t;
  const reject=fn=>{let bad=false;try{fn()}catch(e){bad=true}a(bad,'expected rejection')};
  const make=(frequencyHz=261.6255653,dampingNsM=0,dt=1/48000,massKg=.002)=>modalCoefficients({massKg,frequencyHz,dampingNsM,dt});
  const w=2*Math.PI*261.6255653,crit=2*.002*w;
  const phase=[261.6255653,1000,5000,10000,16000].map(f=>{
    const p=make(f);let x=1e-5,v=0,err=0;const omega=2*Math.PI*f;
    for(let i=1;i<=4800;i++){({x,v}=advanceMode(p,x,v));err=Math.max(err,Math.hypot(x-1e-5*Math.cos(omega*i*p.dt),(v+1e-5*omega*Math.sin(omega*i*p.dt))/omega)/1e-5);}
    return {frequencyHz:f,exactMaxRelativeStateError:err,midpointCents:1200*Math.log2(midpointFrequency(f,48000)/f)};
  });
  const k=2400,c=.04,initial={xa:1e-4,va:0,xb:0,vb:0},duration=.02;
  function pairAt(rate){
    const p=make(261.6255653,.015,1/rate),q=make(1100,.04,1/rate,.004);
    let s=initial,e0=pairEnergy(p,q,s,k),work=0,loss=0,maxIncrease=0,maxBalance=0,minLocal=Infinity;
    for(let i=0;i<Math.round(duration*rate);i++){
      const next=coupledPair(p,q,s,{springNPerM:k,dampingNsM:c});
      const e=pairEnergy(p,q,next,k),prev=pairEnergy(p,q,s,k);
      maxIncrease=Math.max(maxIncrease,e-prev);work+=next.workJ;loss+=next.localLossJ+next.edgeLossJ;
      maxBalance=Math.max(maxBalance,Math.abs(e-e0-work+loss));minLocal=Math.min(minLocal,next.localLossJ);s=next;
    }
    return {s,e0,loss,maxIncrease,maxBalance,minLocal};
  }
  const refRate=1536000,ref=new Reference({dt:1/refRate,mass:[.002,.004],ground:[.002*w*w,.004*(2*Math.PI*1100)**2],damping:[.015,.04],edges:[{i:0,j:1,k,c}]});
  ref.x[0]=initial.xa;for(let i=0;i<Math.round(duration*refRate);i++)ref.step();
  const norm=s=>Math.hypot(s.xa-ref.x[0],(s.va-ref.v[0])/w,s.xb-ref.x[1],(s.vb-ref.v[1])/(2*Math.PI*1100))/initial.xa;
  const convergence=[12000,24000,48000,96000].map(rate=>{const o=pairAt(rate);return {rate,error:norm(o.s),maxIncrease:o.maxIncrease,maxBalance:o.maxBalance,minLocal:o.minLocal,lossFraction:o.loss/o.e0};});
  const quadrature=[];
  const cases=[
    ['lossless modes match exact analytic trajectories through 16 kHz',()=>a(phase.every(p=>p.exactMaxRelativeStateError<1e-9),'phase')],
    ['one second lossless energy',()=>{const p=make(16000);let x=1e-5,v=0,e=modeEnergy(p,x,v);for(let i=0;i<48000;i++)({x,v}=advanceMode(p,x,v));a(Math.abs(modeEnergy(p,x,v)/e-1)<1e-9,'energy')}],
    ['constant force analytic undamped',()=>{const p=make(),F=.1;let x=0,v=0;for(let i=0;i<480;i++)({x,v}=advanceMode(p,x,v,F));a(near(x,F/p.k*(1-Math.cos(w*.01)),1e-12)&&near(v,F/p.k*w*Math.sin(w*.01),1e-10),'force')}],
    ['static equilibrium fixed',()=>{for(const d of [0,crit,crit*2]){const p=make(261.6255653,d),x=.1/p.k,s=advanceMode(p,x,0,.1);a(near(s.x,x,1e-14)&&near(s.v,0,1e-12),'eq')}}],
    ['critical damping analytic',()=>{const p=make(261.6255653,crit),t=.01;let x=.001,v=.02;for(let i=0;i<480;i++)({x,v}=advanceMode(p,x,v));a(near(x,Math.exp(-w*t)*(.001+(.02+w*.001)*t),1e-12),'critical')}],
    ['overdamped analytic two roots',()=>{const p=make(261.6255653,2*crit),alpha=2*w,beta=Math.sqrt(alpha*alpha-w*w),r1=-alpha+beta,r2=-alpha-beta,A=(.02-r2*.001)/(r1-r2),B=.001-A,t=.01;let x=.001,v=.02;for(let i=0;i<480;i++)({x,v}=advanceMode(p,x,v));a(near(x,A*Math.exp(r1*t)+B*Math.exp(r2*t),1e-12)&&near(v,A*r1*Math.exp(r1*t)+B*r2*Math.exp(r2*t),1e-10),'over')}],
    ['near critical continuity',()=>{const p=make(261.6255653,crit);for(const f of [1-1e-9,1+1e-9]){const q=make(261.6255653,crit*f);a(near(q.A,p.A,1e-9)&&near(q.G,p.G,1e-12),'continuity')}}],
    ['low frequency force response stable',()=>{const p=make(.0001);a(near(p.G,p.dt**2/(2*p.massKg),1e-18),'small G')}],
    ['damping integral matches energy loss by Simpson quadrature',()=>{for(const d of [.04,crit,2*crit]){const p=make(261.6255653,d),x=.001,v=.02,F=.3,s=advanceMode(p,x,v,F),N=1024;let integral=d*v*v+d*s.v*s.v;for(let i=1;i<N;i++){const q=make(261.6255653,d,p.dt*i/N);const z=advanceMode(q,x,v,F);integral+=(i%2?4:2)*d*z.v*z.v;}integral*=p.dt/(3*N);const loss=modeEnergy(p,x,v)+F*(s.x-x)-modeEnergy(p,s.x,s.v);quadrature.push({damping:d,loss,integral,relativeError:Math.abs(loss-integral)/integral});a(Math.abs(loss-integral)<1e-6*Math.max(1e-12,loss),'quadrature '+JSON.stringify(quadrature.at(-1)))}}],
    ['coupling zero equals local exact transitions',()=>{const p=make(),q=make(1000,.02),s=coupledPair(p,q,initial,{springNPerM:0,dampingNsM:0});const z=advanceMode(p,initial.xa,initial.va);a(s.xa===z.x&&s.va===z.v&&s.xb===0,'zero')}],
    ['passive pair energy balance and nonnegative losses',()=>a(convergence.every(x=>x.maxIncrease<1e-12&&x.maxBalance<1e-12&&x.minLocal>=-1e-12),'pair')],
    ['driven pair work and dissipation',()=>{const p=make(261.6255653,.02),q=make(1100,.04),s=coupledPair(p,q,initial,{springNPerM:k,dampingNsM:c,forceA:.3,forceB:-.2});a(near(pairEnergy(p,q,s,k)-pairEnergy(p,q,initial,k),s.workJ-s.localLossJ-s.edgeLossJ,1e-12)&&s.xb!==0,'drive')}],
    ['coupled trajectory converges toward refined midpoint',()=>a(convergence.slice(1).every((p,i)=>convergence[i].error/p.error>3.5&&convergence[i].error/p.error<4.5),'order '+JSON.stringify(convergence))],
    ['invalid inputs rejected',()=>{reject(()=>make(0));reject(()=>make(100,-1));reject(()=>advanceMode(make(),NaN,0));reject(()=>coupledPair(make(),make(),initial,{springNPerM:-1,dampingNsM:0}));}]
  ];
  for(const [name,fn] of cases){try{fn()}catch(e){throw Error(name+': '+e.message)}}return {passed:cases.map(c=>c[0]),phase,convergence,refRate,quadrature};
}
const result=runChecks(MechanicalReference,midpointFrequency);for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));
