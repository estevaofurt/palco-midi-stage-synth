import {solidWire} from '../c3x-physical/c4-wire-consistency.mjs';
import {makeDesign} from './c4-design.mjs';
import {modalCoefficients} from './exact-modal.mjs';
import {StiffString} from './stiff-string.mjs';
import {Trichord} from './trichord.mjs';
import {MemoryHammer} from './felt-memory.mjs';
import {solveThreeContacts,EfficientMemoryHammer} from './efficient-felt.mjs';
function study(helpers){
  const a=(v,m)=>{if(!v)throw Error(m)};
  function simulate({rate=48000,velocity=1,massKg=.01,stiffness=1,centerFraction=.13,widthM=.012,viscosity=1,cut=16000,offsets=[0,0,0],kind='fast'}={}){
    const tri=new helpers.Trichord({centerFraction,widthM,stringOptions:{sampleRate:rate,maxFrequencyHz:cut}},helpers);
    const params={massKg,initialVelocityMps:velocity,equilibriumK:1.4e9*stiffness,memoryK:.6e9*stiffness,viscosity,gapOffsetsM:offsets};
    const m=kind==='original'?new helpers.MemoryHammer(tri,params):new EfficientMemoryHammer(tri,{...params,referenceOnly:kind==='reference'});
    const e0=m.energy();let peak=0,first=null,last=null,residual=0,maxBalance=0,maxIncrease=0,prev=e0;
    const frequencies=[500,1000,3000,6000,10000],spectrum=frequencies.map(f=>({f,re:0,im:0})),trace=[];
    for(let i=0;i<Math.round(.008*rate);i++){
      const s=m.step(),e=m.energy(),l=tri.ledger(),t=(i+.5)/rate;
      peak=Math.max(peak,s.sum);if(s.sum>1e-9){if(first===null)first=i;last=i;}
      maxIncrease=Math.max(maxIncrease,e-prev);prev=e;residual=Math.max(residual,m.lastResidual);maxBalance=Math.max(maxBalance,Math.abs(e+l.lossJ+m.contactLossJ-e0));
      for(const q of spectrum){q.re+=s.sum*Math.cos(2*Math.PI*q.f*t)/rate;q.im+=s.sum*Math.sin(2*Math.PI*q.f*t)/rate;}
      trace.push(s.sum);
    }
    const modal=Array.from({length:tri.strings[0].vertical.modes.length},(_,i)=>tri.strings.reduce((sum,s)=>{const q=s.vertical.modes[i];return sum+.5*(q.massKg*s.vertical.v[i]**2+q.stiffnessNPerM*s.vertical.x[i]**2);},0));
    const total=tri.energy(),high=modal.reduce((s,e,i)=>s+(tri.strings[0].vertical.modes[i].frequencyHz>=3000?e:0),0);
    return {rate,velocity,massKg,stiffness,centerFraction,widthM,viscosity,cut,kind,peakN:peak,contactMs:1000*(last-first+1)/rate,energyJ:total,highPct:100*high/total,lossJ:m.contactLossJ,rebounce:m.v,finalForce:m.lastForces.reduce((a,b)=>a+b,0),maxIncrease,maxBalance,residual,evaluations:m.evaluations??null,methods:m.methods??null,spectrum:spectrum.map(q=>({f:q.f,db:20*Math.log10(Math.hypot(q.re,q.im)/m.impulseNs)})),modal,trace};
  }
  const base=simulate(),original=simulate({kind:'original'}),ref=simulate({kind:'reference'}),asym=simulate({velocity:2.5,offsets:[0,.00005,.0001]}),asymRef=simulate({velocity:2.5,offsets:[0,.00005,.0001],kind:'original'});
  const sensitivity=[['massKg',.008,.012],['stiffness',.8,1.2],['centerFraction',.104,.156],['widthM',.0096,.0144],['viscosity',.8,1.2]].flatMap(([key,l,h])=>[l,h].map(v=>({parameter:key,value:v,...simulate({[key]:v})})));
  const refined=[base,simulate({rate:96000}),simulate({rate:192000})];
  const cut=[simulate({rate:192000,cut:8000}),refined[2],simulate({rate:192000,cut:32000})];
  const maxDiff=(x,y)=>Math.max(...x.trace.map((v,i)=>Math.abs(v-y.trace[i])));
  const all=[base,original,ref,asym,asymRef,...sensitivity,...refined,...cut];
  const forced=solveThreeContacts([.0004,.0004,.0004],[.0005,.0005,.0005],[1e-5,1e-5,1e-5],1e-5,[0,0,0],{ke:1.4e9,km:.6e9,kr:1000,viscosity:1,power:2.5});
  const cases=[
    ['fast path matches original trajectory',()=>a(maxDiff(base,original)<1e-7,'baseline parity')],
    ['counted reference matches original',()=>a(maxDiff(ref,original)<1e-9,'reference parity')],
    ['asymmetric forte trajectory matches original',()=>a(maxDiff(asym,asymRef)<1e-7,'asym parity')],
    ['contact law evaluations reduced',()=>a(base.evaluations<ref.evaluations/10&&base.methods.contraction>0,'cost')],
    ['strong coupling uses fallback',()=>a(forced.method==='bisection'&&forced.forces.every(f=>f>=0),'fallback')],
    ['passivity and energy balance across all sweeps',()=>a(all.every(q=>q.maxIncrease<1e-10&&q.maxBalance<1e-10&&q.residual<1e-7),'energy')],
    ['all impacts rebound and release',()=>a(all.every(q=>q.rebounce<0&&q.finalForce===0),'release')],
    ['modal energies nonnegative and sum correctly',()=>a(all.every(q=>q.modal.every(e=>e>=0)&&Math.abs(q.modal.reduce((s,e)=>s+e,0)-q.energyJ)<1e-12),'modal')],
    ['force spectrum finite',()=>a(all.every(q=>q.spectrum.every(v=>Number.isFinite(v.db))),'spectrum')],
    ['time refinement reduces peak force error',()=>a(Math.abs(refined[1].peakN-refined[2].peakN)<Math.abs(base.peakN-refined[2].peakN),'refine')],
    ['spectral truncation comparison finite',()=>a(cut.every(q=>q.modal.length>0&&q.highPct>=0),'cut')],
    ['parameter sensitivity covers ten independent perturbations',()=>a(sensitivity.length===10&&sensitivity.every(q=>q.peakN>0&&q.energyJ>0),'sweep')]
  ];
  for(const [n,f] of cases){try{f()}catch(e){throw Error(n+': '+e.message)}}
  const compact=({trace,modal,...q})=>({...q,modalCount:modal.length,modalEnergyPct:modal.slice(0,8).map(e=>100*e/q.energyJ)});
  return {passed:cases.map(c=>c[0]),base:compact(base),reference:compact(ref),original:compact(original),asym:compact(asym),asymDiff:maxDiff(asym,asymRef),baseDiff:maxDiff(base,original),forced,sensitivity:sensitivity.map(compact),refined:refined.map(compact),cut:cut.map(compact)};
}
const result=study({Trichord,StiffString,modalCoefficients,makeDesign,solidWire,MemoryHammer});for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));
