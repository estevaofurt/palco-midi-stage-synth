import {ModalPortNetwork} from './modal-port-network.mjs';
import {modalCoefficients,coupledPair} from './exact-modal.mjs';
import {MechanicalReference} from './mechanical-reference.mjs';
function runChecks(coeff,Pair,Reference){
  const a=(v,m)=>{if(!v)throw Error(m)},near=(x,y,t)=>Math.abs(x-y)<=t;
  const reject=fn=>{let bad=false;try{fn()}catch(e){bad=true}a(bad,'expected rejection')};
  const specs=(rate,n=4)=>Array.from({length:n},(_,i)=>({dt:1/rate,massKg:.002+.0005*i,frequencyHz:[261.6255653,540,1100,2200][i%4],dampingNsM:.015+.003*i}));
  const edges=[{i:0,j:2,k:2400,c:.04},{i:1,j:2,k:1200,c:.02},{i:2,j:3,k:1600,c:.03}];
  const ports=edges.map(({i,j,k,c})=>({weights:[{i,b:1},{i:j,b:-1}],k,c}));
  const init=net=>{net.x[0]=1e-4;net.v[1]=.015;};
  const refRate=1536000,duration=.01,rs=specs(refRate),ref=new Reference({dt:1/refRate,mass:rs.map(m=>m.massKg),ground:rs.map(m=>m.massKg*(2*Math.PI*m.frequencyHz)**2),damping:rs.map(m=>m.dampingNsM),edges});
  init(ref);for(let i=0;i<duration*refRate;i++)ref.step();
  const convergence=[12000,24000,48000,96000].map(rate=>{
    const net=new ModalPortNetwork(specs(rate),ports,coeff);init(net);const e0=net.energy();let maxIncrease=0,maxBalance=0,minLocal=Infinity;
    for(let i=0;i<rate*duration;i++){const before=net.energy(),local=net.localLossJ;net.step();const after=net.energy();maxIncrease=Math.max(maxIncrease,after-before);maxBalance=Math.max(maxBalance,Math.abs(after-e0-net.workJ+net.localLossJ+net.portLossJ));minLocal=Math.min(minLocal,net.localLossJ-local);}
    let sq=0;for(let i=0;i<net.n;i++)sq+=(net.x[i]-ref.x[i])**2+((net.v[i]-ref.v[i])/(2*Math.PI*rs[i].frequencyHz))**2;
    return {rate,error:Math.sqrt(sq)/1e-4,maxIncrease,maxBalance,minLocal,conditionUpper:net.conditionUpper};
  });
  const large=[];
  const cases=[
    ['two-mode specialization agrees with F2.2',()=>{const ms=specs(48000,2),p=ms.map(coeff),k=2400,c=.04,net=new ModalPortNetwork(ms,[{weights:[{i:0,b:1},{i:1,b:-1}],k,c}],coeff);net.x[0]=1e-4;let s={xa:1e-4,va:0,xb:0,vb:0};for(let i=0;i<1000;i++){net.force[0]=.1*Math.sin(i*.03);net.force[1]=-.03;s=Pair(p[0],p[1],s,{springNPerM:k,dampingNsM:c,forceA:net.force[0],forceB:net.force[1]});net.step();a(near(s.xa,net.x[0],1e-15)&&near(s.vb,net.v[1],1e-12),'pair')}}],
    ['zero state remains zero',()=>{const net=new ModalPortNetwork(specs(48000),ports,coeff);for(let i=0;i<100;i++)net.step();a(net.energy()===0,'zero')}],
    ['no ports independent modes',()=>{const net=new ModalPortNetwork(specs(48000),[],coeff);net.x[0]=1e-4;net.step();a(net.x[0]===net.modes[0].A*1e-4&&net.x[1]===0,'free')}],
    ['zero ports omitted',()=>a(new ModalPortNetwork(specs(48000),[{weights:[{i:0,b:1}],k:0,c:0}],coeff).p===0,'zero port')],
    ['multiple passive edges converge second order',()=>a(convergence.slice(1).every((q,i)=>convergence[i].error/q.error>3.5&&convergence[i].error/q.error<4.5),'convergence '+JSON.stringify(convergence))],
    ['free network passive and balanced',()=>a(convergence.every(q=>q.maxIncrease<1e-13&&q.maxBalance<1e-12&&q.minLocal>=-1e-13),'energy')],
    ['multi-force work and port balance',()=>{const net=new ModalPortNetwork(specs(48000),ports,coeff);let minLocal=Infinity;for(let i=0;i<4800;i++){const prev=net.localLossJ;for(let j=0;j<4;j++)net.force[j]=.05*Math.sin(i*.13+j);net.step();minLocal=Math.min(minLocal,net.localLossJ-prev);}a(near(net.energy()+net.localLossJ+net.portLossJ,net.workJ,1e-12)&&minLocal>=-1e-13&&net.portLossJ>0,'work')}],
    ['general weighted port analytic symmetric normal mode',()=>{const rate=48000,h=1/rate,m=.002,f=261.6255653,k=1200,net=new ModalPortNetwork(Array.from({length:3},()=>({dt:h,massKg:m,frequencyHz:f,dampingNsM:0})),[{weights:[{i:0,b:1},{i:1,b:-2},{i:2,b:1}],k,c:0}],coeff);net.x.set([1e-4,-2e-4,1e-4]);const w=Math.sqrt((2*Math.PI*f)**2+6*k/m);for(let i=0;i<480;i++)net.step();a(Math.abs(net.x[0]/1e-4-Math.cos(w*.01))<.005&&near(net.x[1],-2*net.x[0],1e-12),'weighted')}],
    ['orientation invariant',()=>{const ms=specs(48000),p=new ModalPortNetwork(ms,ports,coeff),q=new ModalPortNetwork(ms,ports.map(s=>({...s,weights:s.weights.map(w=>({...w,b:-w.b}))})),coeff);init(p);init(q);for(let i=0;i<1000;i++){p.step();q.step();}a(p.x.every((x,i)=>near(x,q.x[i],1e-15)),'orientation')}],
    ['duplicate ports additive',()=>{const ms=specs(48000),p=new ModalPortNetwork(ms,[ports[0],ports[0]],coeff),q=new ModalPortNetwork(ms,[{...ports[0],k:2*ports[0].k,c:2*ports[0].c}],coeff);init(p);init(q);for(let i=0;i<1000;i++){p.step();q.step();}a(p.x.every((x,i)=>near(x,q.x[i],1e-14)),'duplicate')}],
    ['lossless coupled energy',()=>{const net=new ModalPortNetwork(specs(48000).map(m=>({...m,dampingNsM:0})),ports.map(p=>({...p,c:0})),coeff);init(net);const e=net.energy();for(let i=0;i<4800;i++)net.step();a(Math.abs(net.energy()/e-1)<1e-9,'lossless')}],
    ['large structured networks remain finite and passive',()=>{for(const n of [128,512,2048]){const rate=48000,ms=Array.from({length:n},(_,i)=>({dt:1/rate,massKg:.002,frequencyHz:260+(i%48)*220,dampingNsM:.02}));const ps=Array.from({length:4},(_,j)=>({k:2000,c:.025,weights:Array.from({length:n},(_,i)=>({i,b:(i%4===j?1:-.2)/Math.sqrt(n)}))}));const net=new ModalPortNetwork(ms,ps,coeff);net.x[0]=1e-4;const e0=net.energy();let maxIncrease=0;const t=Date.now();for(let i=0;i<2048;i++){const before=net.energy();net.step();maxIncrease=Math.max(maxIncrease,net.energy()-before);}const msElapsed=Date.now()-t;const residual=Math.abs(net.energy()-e0+net.localLossJ+net.portLossJ);a(Number.isFinite(net.energy())&&maxIncrease<1e-12&&residual<1e-12,'large');large.push({modes:n,ports:4,steps:2048,conditionUpper:net.conditionUpper,maxIncrease,residual,elapsedMsIncludingEnergy:msElapsed});}}],
    ['invalid parameters rejected',()=>{reject(()=>new ModalPortNetwork(specs(48000),[{...ports[0],k:-1}],coeff));reject(()=>new ModalPortNetwork(specs(48000),[{...ports[0],weights:[{i:0,b:1},{i:0,b:2}]}],coeff));reject(()=>new ModalPortNetwork(specs(48000),[{...ports[0],weights:[{i:4,b:1}]}],coeff));const ms=specs(48000);ms[1].dt*=2;reject(()=>new ModalPortNetwork(ms,[],coeff));const net=new ModalPortNetwork(specs(48000),ports,coeff);net.force[0]=NaN;reject(()=>net.step());}]
  ];
  for(const [name,fn] of cases){try{fn()}catch(e){throw Error(name+': '+e.message)}}return {passed:cases.map(c=>c[0]),convergence,large,refRate};
}
const result=runChecks(modalCoefficients,coupledPair,MechanicalReference);for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));
