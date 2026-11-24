import {MechanicalReference,midpointFrequency,phaseBudget} from './mechanical-reference.mjs';
import {SharedPassivePianoBridge} from '../shared-passive-piano-bridge.mjs';
import {PassiveStringBridgeCell} from '../passive-string-bridge-cell.mjs';
function auditExisting(Shared,Cell){
  const a=new Shared({sampleRate:48000,keys:[48,60,72],coupling:.35}),n=a.n;
  const edges=Array.from(a.coupling,(k,i)=>({i,j:n,k}));edges.push({i:n,j:n+1,k:a.boardSpring});
  const b=new MechanicalReference({dt:a.dt,mass:[...a.mass,...a.bmass],ground:[...a.ground,...a.bground],damping:[...a.damping,...a.bdamper],edges});
  a.x[0]=b.x[0]=1e-5;a.bx[1]=b.x[n+1]=2e-6;
  const force=new Float64Array(n+2);let maxX=0,maxV=0;
  for(let i=0;i<4800;i++){
    a.forces[0]=force[0]=i<240?.1*Math.sin(Math.PI*i/240):0;
    a.forces[3]=force[3]=i<100?.05:0;
    a.step();b.step(force);
    for(let j=0;j<n+2;j++){maxX=Math.max(maxX,Math.abs((j<n?a.x[j]:a.bx[j-n])-b.x[j]));maxV=Math.max(maxV,Math.abs((j<n?a.v[j]:a.bv[j-n])-b.v[j]));}
  }
  const old=new Cell({sampleRate:48000,key:60,coupling:.12});
  const c=new MechanicalReference({dt:old.dt,mass:old.mass,ground:[0,0,0,0],damping:old.damping});
  // Reconstruct ground and edges from original matrix; factorization must match exact K.
  const g=Array.from({length:4},(_,i)=>Array.from({length:4},(_,j)=>old.stiffness[i*4+j]).reduce((x,y)=>x+y,0));
  const e=[];for(let i=0;i<4;i++)for(let j=i+1;j<4;j++)if(old.stiffness[i*4+j]<0)e.push({i,j,k:-old.stiffness[i*4+j]});
  const d=new MechanicalReference({dt:old.dt,mass:old.mass,ground:g,damping:old.damping,edges:e});
  old.x[0]=d.x[0]=1e-5;let cellX=0,cellV=0;
  for(let i=0;i<2400;i++){const f=i<100?.2:0;old.step(f);d.step([f,0,0,0]);for(let j=0;j<4;j++){cellX=Math.max(cellX,Math.abs(old.x[j]-d.x[j]));cellV=Math.max(cellV,Math.abs(old.v[j]-d.v[j]));}}
  return {shared:{maxX,maxV,energyDifference:Math.abs(a.energy()-b.energy()),workDifference:Math.abs(a.externalWork-b.workJ),lossDifference:Math.abs(a.dissipated-b.lossJ)},cell:{maxX:cellX,maxV:cellV}};
}
function runChecks(Shared,Cell){
  const a=(v,m)=>{if(!v)throw Error(m)},near=(x,y,t)=>Math.abs(x-y)<t;
  const reject=fn=>{let bad=false;try{fn()}catch(e){bad=true}a(bad,'expected rejection')};
  const make=(rate=48000,c=0)=>new MechanicalReference({dt:1/rate,mass:[.002],ground:[.002*(2*Math.PI*261.6255653)**2],damping:[c]});
  const convergence=[12000,24000,48000,96000].map(rate=>{const m=make(rate),w=2*Math.PI*261.6255653,t=.01;m.x[0]=.001;for(let i=0;i<rate*t;i++)m.step();return {rate,error:Math.hypot(m.x[0]-.001*Math.cos(w*t),(m.v[0]+.001*w*Math.sin(w*t))/w)/.001};});
  const legacy=auditExisting(Shared,Cell);
  const cases=[
    ['free mass constant velocity',()=>{const m=new MechanicalReference({dt:.001,mass:[.01],ground:[0],damping:[0]});m.v[0]=.2;for(let i=0;i<100;i++)m.step();a(near(m.x[0],.02,1e-12),'free') }],
    ['constant force analytic free mass',()=>{const m=new MechanicalReference({dt:.001,mass:[.01],ground:[0],damping:[0]});for(let i=0;i<100;i++)m.step([.03]);a(near(m.x[0],.015,1e-12)&&near(m.v[0],.3,1e-12),'force')}],
    ['zero state remains zero',()=>{const m=make();for(let i=0;i<100;i++)m.step();a(m.energy()===0,'zero')}],
    ['lossless long-run energy',()=>{const m=make();m.x[0]=1e-4;const e=m.energy();for(let i=0;i<48000;i++)m.step();a(Math.abs(m.energy()/e-1)<1e-9,'energy')}],
    ['damped energy monotonically decreases',()=>{const m=make(48000,.02);m.x[0]=1e-4;let e=m.energy(),e0=e;for(let i=0;i<4800;i++){m.step();const next=m.energy();a(next<=e+1e-14&&m.lossJ>=0,'passivity');e=next;}a(near(e+m.lossJ,e0,1e-12),'balance')}],
    ['driven energy balance',()=>{const m=make(48000,.02);for(let i=0;i<4800;i++)m.step([.1*Math.sin(i*.1)]);a(near(m.energy()+m.lossJ,m.workJ,1e-12),'work')}],
    ['edge exchanges equal and opposite momentum',()=>{const m=new MechanicalReference({dt:.0001,mass:[.002,.005],ground:[0,0],damping:[0,0],edges:[{i:0,j:1,k:800,c:.05}]});m.x[0]=.001;for(let i=0;i<1000;i++)m.step();a(near(.002*m.v[0]+.005*m.v[1],0,1e-12)&&m.x[1]!==0,'momentum')}],
    ['edge damping included in loss',()=>{const m=new MechanicalReference({dt:.0001,mass:[.002,.005],ground:[0,0],damping:[0,0],edges:[{i:0,j:1,k:800,c:.05}]});m.x[0]=.001;const e=m.energy();for(let i=0;i<1000;i++)m.step();a(m.lossJ>0&&near(e,m.energy()+m.lossJ,1e-12),'edge loss')}],
    ['second order convergence against analytic oscillator',()=>a(convergence.slice(1).every((q,i)=>convergence[i].error/q.error>3.9&&convergence[i].error/q.error<4.1),'order')],
    ['discrete phase agrees with exact midpoint oscillator',()=>{const m=make(48000);m.x[0]=1e-4;const f=midpointFrequency(261.6255653,48000);for(let i=0;i<480;i++)m.step();a(near(m.x[0],1e-4*Math.cos(2*Math.PI*f*.01),1e-13),'phase')}],
    ['phase lag grows with frequency',()=>a(midpointFrequency(10000,48000)/10000<midpointFrequency(1000,48000)/1000,'lag')],
    ['substeps meet tolerance and minimality',()=>{const q=phaseBudget(10000,48000,1);a(q.substeppedCents>=-1&&q.minSubsteps>1&&1200*Math.log2(midpointFrequency(10000,48000,q.minSubsteps-1)/10000)<-1,'budget')}],
    ['existing shared solver matches dense state',()=>a(legacy.shared.maxX<1e-12&&legacy.shared.maxV<1e-9,'shared state')],
    ['existing shared work and loss agree',()=>a(legacy.shared.workDifference<1e-12&&legacy.shared.lossDifference<1e-12&&legacy.shared.energyDifference<1e-12,'shared energy')],
    ['existing cell matches dense state',()=>a(legacy.cell.maxX<1e-12&&legacy.cell.maxV<1e-9,'cell state')],
    ['invalid inputs rejected',()=>{reject(()=>new MechanicalReference({dt:0,mass:[1],ground:[0],damping:[0]}));reject(()=>new MechanicalReference({dt:.01,mass:[-1],ground:[0],damping:[0]}));reject(()=>new MechanicalReference({dt:.01,mass:[1],ground:[0],damping:[-1]}));reject(()=>new MechanicalReference({dt:.01,mass:[1],ground:[0],damping:[0],edges:[{i:0,j:0,k:1}]}));reject(()=>make().step([NaN]));reject(()=>phaseBudget(1,48000,0));}]
  ];
  for(const [name,fn] of cases){try{fn()}catch(e){throw Error(name+': '+e.message)}}
  return {passed:cases.map(c=>c[0]),convergence,legacy,phase:[261.6255653,1000,5000,10000,16000].map(f=>phaseBudget(f,48000))};
}
const result=runChecks(SharedPassivePianoBridge,PassiveStringBridgeCell);for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));
