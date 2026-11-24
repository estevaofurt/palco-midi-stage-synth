import {solidWire} from '../c3x-physical/c4-wire-consistency.mjs';
import {makeDesign} from './c4-design.mjs';
import {modalCoefficients} from './exact-modal.mjs';
import {ModalPortNetwork} from './modal-port-network.mjs';
import {stringMode,spatialWeight,StiffString,staticCompliance} from './stiff-string.mjs';
function runChecks(solidWire,makeDesign,coeff,Network){
  const a=(v,m)=>{if(!v)throw Error(m)},near=(x,y,t)=>Math.abs(x-y)<t,reject=fn=>{let bad=false;try{fn()}catch(e){bad=true}a(bad,'expected rejection')};
  const wire=makeDesign(solidWire),make=o=>new StiffString(wire,o,coeff),s=make(),L=wire.lengthM,center=.13*L,width=.012;
  const selected=[1,2,4,8,12,16,32].map(n=>{const m=stringMode(wire,n);return {n,fHz:m.frequencyHz,phaseMps:m.phaseSpeedMps,groupMps:m.groupSpeedMps,bendingFraction:m.bendingStiffness/m.stiffnessNPerM};});
  const compliance=[8,16,32,s.modes.length,128,512,4096].map(n=>({n,point:staticCompliance(wire,center,0,n),footprint:staticCompliance(wire,center,width,n)}));
  const end=compliance.at(-1),trunc=compliance[3];
  const spatialConvergence=[32,64,128,256].map(N=>{const n=12,m=stringMode(wire,n),dx=L/N,lambda=4*Math.sin(n*Math.PI/(2*N))**2/dx**2,fd=Math.sqrt((wire.tensionN*lambda+wire.EI*lambda**2)/wire.linearDensityKgM)/(2*Math.PI);return {intervals:N,errorPct:100*(fd/m.frequencyHz-1)};});
  const cases=[
    ['fundamental from physical parameters',()=>a(near(s.modes[0].frequencyHz,wire.f1Hz,1e-10),'f1')],
    ['all modal frequencies match independent B expression',()=>a(s.modes.every(m=>near(m.frequencyHz,m.n*wire.f1Hz*Math.sqrt((1+wire.B*m.n*m.n)/(1+wire.B)),1e-9)),'dispersion')],
    ['modal mass equals half vibrating mass',()=>a(s.modes.every(m=>near(m.massKg,wire.massKg/2,1e-15)),'mass')],
    ['tension and bending stiffness positive',()=>a(s.modes.every(m=>m.tensionStiffness>0&&m.bendingStiffness>0&&near(m.stiffnessNPerM,m.coeff.k,1e-7)),'stiffness')],
    ['zero EI reduces to harmonic string',()=>a(near(stringMode({...wire,EI:0},12).frequencyHz,12*stringMode({...wire,EI:0},1).frequencyHz,1e-10),'harmonic')],
    ['group velocity exceeds phase velocity',()=>a(selected.every(m=>m.groupMps>m.phaseMps)&&selected.at(-1).groupMps>selected[0].groupMps,'dispersion')],
    ['cutoff obeys guard and is not arbitrary mode count',()=>a(s.modes.at(-1).frequencyHz<s.cutoffHz&&stringMode(wire,s.modes.length+1).frequencyHz>=s.cutoffHz&&make({sampleRate:22050}).modes.at(-1).frequencyHz<8820,'cutoff')],
    ['pinned endpoints and midpoint parity',()=>{a(s.weights(0).every(v=>v===0)&&s.weights(L).every(v=>v===0),'pinned');a(s.weights(L/2).every((v,i)=>i%2===0?near(Math.abs(v),1,1e-12):Math.abs(v)<1e-12),'parity')}],
    ['finite footprint matches numerical spatial integral',()=>{const m=s.modes[11],N=2048;let avg=0;for(let i=0;i<N;i++)avg+=Math.sin(m.waveNumber*(center-width/2+width*(i+.5)/N))/N;a(near(avg,spatialWeight(m,L,center,width),1e-8),'footprint')}],
    ['force and displacement are power conjugate',()=>{const w=s.weights(center,width),v=Float64Array.from(w,(_,i)=>.01*Math.cos(i)),f=.23;let sum=0;for(let i=0;i<w.length;i++)sum+=f*w[i]*v[i];a(near(sum,f*s.projection(w,v),1e-14),'work')}],
    ['zero state stays zero',()=>{const q=make();q.step(q.weights(center,width));a(q.energy()===0,'zero')}],
    ['lossless string conserves energy',()=>{const q=make({sigma0PerS:0,sigma2M2PerS:0}),w=q.weights(center,width);q.x[0]=1e-5;q.x[15]=1e-7;const e=q.energy();for(let i=0;i<4800;i++)q.step(w);a(Math.abs(q.energy()/e-1)<1e-9,'energy')}],
    ['damped string loses energy monotonically',()=>{const q=make(),w=q.weights(center,width);q.x[0]=1e-5;q.x[15]=1e-7;const e0=q.energy();let e=e0;for(let i=0;i<4800;i++){q.step(w);const next=q.energy();a(next<=e+1e-14,'passive');e=next;}a(q.lossJ>0&&near(e+q.lossJ,e0,1e-12),'loss')}],
    ['applied force work equals stored and lost energy',()=>{const q=make(),w=q.weights(center,width);for(let i=0;i<480;i++)q.step(w,i<100?.1*Math.sin(i*Math.PI/100):0);a(near(q.energy()+q.lossJ,q.workJ,1e-12)&&q.lossJ>=0,'forced')}],
    ['matches F2.3 independent modal network',()=>{const q=make(),w=q.weights(center,width),net=new Network(q.modes.map(m=>({dt:q.dt,massKg:m.massKg,frequencyHz:m.frequencyHz,dampingNsM:m.dampingNsM})),[],coeff);for(let i=0;i<256;i++){const f=.05*Math.sin(i*.1);q.step(w,f);for(let j=0;j<w.length;j++)net.force[j]=w[j]*f;net.step();}a(q.x.every((v,i)=>near(v,net.x[i],1e-14))&&q.v.every((v,i)=>near(v,net.v[i],1e-11)),'network')}],
    ['support force includes bending shear',()=>{const q=make();q.x[0]=1e-6;const k=Math.PI/L;a(near(q.rightSupportForceN(),(wire.tensionN*k+wire.EI*k**3)*1e-6,1e-14),'reaction')}],
    ['static compliance converges and finite footprint reduces truncation error',()=>a(compliance.slice(1).every((v,i)=>v.point>=compliance[i].point&&v.footprint>=compliance[i].footprint)&&(end.footprint-trunc.footprint)/end.footprint<(end.point-trunc.point)/end.point,'static')],
    ['independent spatial finite-difference dispersion converges',()=>a(spatialConvergence.slice(1).every((v,i)=>Math.abs(spatialConvergence[i].errorPct/v.errorPct)>3.5&&Math.abs(spatialConvergence[i].errorPct/v.errorPct)<4.5),'FD')],
    ['invalid inputs rejected',()=>{reject(()=>make({sigma2M2PerS:-1}));reject(()=>s.weights(0,.01));reject(()=>s.step([1],1));reject(()=>stringMode(wire,0));reject(()=>make({maxFrequencyHz:100}));}]
  ];
  for(const [name,fn] of cases){try{fn()}catch(e){throw Error(name+': '+e.message)}}return {passed:cases.map(c=>c[0]),count:s.modes.length,highestHz:s.modes.at(-1).frequencyHz,nextHz:stringMode(wire,s.modes.length+1).frequencyHz,modalMassKg:s.modes[0].massKg,selected,compliance,relativeMissingPointPct:100*(end.point-trunc.point)/end.point,relativeMissingFootprintPct:100*(end.footprint-trunc.footprint)/end.footprint,spatialConvergence,lossExamples:[1,8,16,32].map(n=>{const m=s.modes[n-1];return {n,sigma:m.sigma,amplitudeT60S:Math.log(1000)/m.sigma};})};
}
const result=runChecks(solidWire,makeDesign,modalCoefficients,ModalPortNetwork);for(const name of result.passed)console.log('PASS '+name);console.log(JSON.stringify(result,null,2));
