import {solidWire} from '../c3x-physical/c4-wire-consistency.mjs';
import {makeDesign} from './c4-design.mjs';
import {modalCoefficients} from './exact-modal.mjs';
import {StiffString} from './stiff-string.mjs';
import {Trichord} from './trichord.mjs';
import {feltPotential,feltSecant,solveContact,HammerTrichord} from './hammer-contact.mjs';
function runChecks(helpers){
  const a=(v,m)=>{if(!v)throw Error(m)},near=(x,y,t)=>Math.abs(x-y)<t,reject=f=>{let bad=false;try{f()}catch(e){bad=true}a(bad,'expected rejection')};
  const make=(rate=48000,velocity=1,eta=.12,cut=16000,gaps=[0,0,0],detune=[-.5,0,.5])=>new HammerTrichord(new helpers.Trichord({detuneCents:detune,stringOptions:{sampleRate:rate,maxFrequencyHz:cut}},helpers),{initialVelocityMps:velocity,rateFactorSPerM:eta,gapOffsetsM:gaps});
  function simulate(rate,velocity,eta=.12,cut=16000,gaps=[0,0,0],detune=[-.5,0,.5]){
    const m=make(rate,velocity,eta,cut,gaps,detune),e0=m.energy(),v0=m.v;
    let peak=0,compression=0,first=null,last=null,minLoss=Infinity,maxIncrease=0,maxBalance=0,maxResidual=0,prev=e0,peakAsymmetry=0;
    for(let i=0;i<Math.ceil(.008*rate);i++){
      const s=m.step(),e=m.energy(),l=m.tri.ledger();
      if(s.sum>1e-9){if(first===null)first=m.time-m.h;last=m.time;}
      peak=Math.max(peak,s.sum);compression=Math.max(compression,...s.compression);
      minLoss=Math.min(minLoss,s.loss);maxIncrease=Math.max(maxIncrease,e-prev);prev=e;
      maxBalance=Math.max(maxBalance,Math.abs(e+l.lossJ+m.contactLossJ-e0));
      maxResidual=Math.max(maxResidual,m.lastResidual);peakAsymmetry=Math.max(peakAsymmetry,Math.max(...s.forces)-Math.min(...s.forces));
    }
    const energyByWire=m.tri.strings.map(s=>s.vertical.energy()),stringEnergy=m.tri.energy();
    let highEnergy=0;for(const s of m.tri.strings)for(let i=0;i<s.vertical.modes.length;i++){const q=s.vertical.modes[i];if(q.frequencyHz>=3000)highEnergy+=.5*(q.massKg*s.vertical.v[i]**2+q.stiffnessNPerM*s.vertical.x[i]**2);}
    return {rate,velocity,eta,cut,peakForceN:peak,maxCompressionM:compression,contactMs:first===null?0:1000*(last-first),exitVelocityMps:m.v,stringEnergyJ:stringEnergy,energyByWire,highEnergyFraction:highEnergy/stringEnergy,contactLossJ:m.contactLossJ,stringLossJ:m.tri.ledger().lossJ,initialEnergyJ:e0,minLoss,maxIncrease,maxBalance,maxResidual,peakAsymmetry,impulseResidual:Math.abs(m.massKg*(v0-m.v)-m.impulseNs),finalForceN:m.lastForces.reduce((a,b)=>a+b,0),horizontalEnergy:m.tri.strings.reduce((a,s)=>a+s.horizontal.energy(),0)};
  }
  const dynamics=[.5,1,2.5].map(v=>simulate(96000,v)),convergence=[simulate(48000,1),dynamics[1],simulate(192000,1)],lossless=simulate(48000,1,0),symmetric=simulate(48000,1,.12,16000,[0,0,0],[0,0,0]),offset=simulate(48000,1,.12,16000,[0,.00005,.0001]),truncation=[simulate(192000,1,.12,8000),convergence[2],simulate(192000,1,.12,32000)];
  const cases=[
    ['unilateral contact no attraction',()=>a(solveContact(-.001,-.0005,1e-7,1e-5,2e9,2.5,.12)===0,'gap')],
    ['stable elastic divided difference',()=>{const d=.0005,k=2e9,p=2.5;a(near(feltSecant(d,d,k,p),k*d**p,1e-12)&&near(feltSecant(d,d+1e-14,k,p),k*d**p,1e-6),'secant')}],
    ['elastic contact exact work identity',()=>{for(const [x,y] of [[-.0001,.0003],[.0004,-.0001],[.0002,.00021]])a(near(feltSecant(x,y,2e9,2.5)*(y-x),feltPotential(y,2e9,2.5)-feltPotential(x,2e9,2.5),1e-14),'work')}],
    ['discrete nonlinear contact root',()=>{const f=solveContact(.0002,.0005,1e-7,1e-5,2e9,2.5,.12),d=.0005-1e-7*f;a(f>=0&&near(f,feltSecant(.0002,d,2e9,2.5)*Math.max(0,1+.12*(d-.0002)/1e-5),1e-9),'root')}],
    ['pre-contact ballistic and silent',()=>{const m=make();m.step();a(m.lastForces.every(f=>f===0)&&m.tri.energy()===0&&near(m.x,-.0002+m.h,1e-15),'ballistic')}],
    ['one hammer excites all three strings',()=>a(dynamics.every(q=>q.energyByWire.every(e=>e>0)),'excitation')],
    ['no fabricated horizontal excitation',()=>a(dynamics.every(q=>q.horizontalEnergy===0),'horizontal')],
    ['passivity and force residual',()=>a(dynamics.concat(convergence,offset,lossless,truncation).every(q=>q.minLoss>=-1e-12&&q.maxIncrease<1e-11&&q.maxBalance<1e-10&&q.maxResidual<1e-7),'energy '+JSON.stringify(dynamics))],
    ['hammer momentum matches contact impulse',()=>a(dynamics.concat(convergence).every(q=>q.impulseResidual<1e-12),'reaction')],
    ['release and rebound without forced cutoff',()=>a(dynamics.every(q=>q.finalForceN===0&&q.exitVelocityMps<0),'rebound '+JSON.stringify(dynamics))],
    ['elastic felt zero contact loss',()=>a(Math.abs(lossless.contactLossJ)<1e-11,'elastic')],
    ['higher speed increases peak and transferred energy',()=>a(dynamics.slice(1).every((q,i)=>q.peakForceN>dynamics[i].peakForceN&&q.stringEnergyJ>dynamics[i].stringEnergyJ),'dynamics')],
    ['symmetric contacts remain symmetric',()=>a(symmetric.peakAsymmetry<1e-9,'symmetry')],
    ['offset contacts allow unequal forces',()=>a(offset.peakAsymmetry>1e-3,'offset')],
    ['time refinement reduces peak force error',()=>{const ref=convergence[2].peakForceN;a(Math.abs(convergence[1].peakForceN-ref)<Math.abs(convergence[0].peakForceN-ref),'refine '+JSON.stringify(convergence))}],
    ['spectral truncation results finite',()=>a(truncation.every(q=>Number.isFinite(q.peakForceN)&&q.stringEnergyJ>0),'truncation')],
    ['invalid felt parameters rejected',()=>{reject(()=>new HammerTrichord(new helpers.Trichord({},helpers),{massKg:-1}));reject(()=>solveContact(0,1,-1,1,1,2,0));}]
  ];
  for(const [name,fn] of cases){try{fn()}catch(e){throw Error(name+': '+e.message)}}
  return {passed:cases.map(c=>c[0]),dynamics,convergence,lossless,symmetric,offset,truncation};
}
const result=runChecks({Trichord,StiffString,modalCoefficients,makeDesign,solidWire});for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));
