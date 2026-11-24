import {solidWire} from '../c3x-physical/c4-wire-consistency.mjs';
import {makeDesign} from './c4-design.mjs';
import {modalCoefficients} from './exact-modal.mjs';
import {StiffString} from './stiff-string.mjs';
import {Trichord} from './trichord.mjs';
import {HammerTrichord} from './hammer-contact.mjs';
import {memoryEnergy,relaxMemory,frozenMemoryForce,MemoryHammer} from './felt-memory.mjs';
function runChecks(helpers){
  const a=(v,m)=>{if(!v)throw Error(m)},near=(x,y,t)=>Math.abs(x-y)<t,reject=f=>{let bad=false;try{f()}catch(e){bad=true}a(bad,'expected rejection')};
  const p={ke:1.4e9,km:.6e9,kr:1000,viscosity:1,power:2.5};
  const instantaneous=(d,z)=>p.ke*Math.max(0,d)**p.power+p.km*Math.max(0,d-z)**p.power;
  const hold=[];let z=0,loss=0;const d=.0004,h=1/96000,e0=memoryEnergy(d,z,p);
  for(let i=0;i<=960;i++){if(i%96===0)hold.push({ms:i*h*1000,forceN:instantaneous(d,z),zM:z,lossJ:loss});if(i<960){const q=relaxMemory(d,z,h,p);z=q.z;loss+=q.lossJ;}}
  const holdResidual=Math.abs(e0-memoryEnergy(d,z,p)-loss);
  const loop=[];z=0;loss=0;let work=0,prev=0;
  for(let i=1;i<=384;i++){const d=.0004*(i<=192?i/192:(384-i)/192),r=relaxMemory(prev,z,h/2,p);z=r.z;loss+=r.lossJ;const f=frozenMemoryForce(prev,d,z,p);work+=f*(d-prev);const s=relaxMemory(d,z,h/2,p);z=s.z;loss+=s.lossJ;if(i%24===0)loop.push({ms:i*h*1000,compressionMm:d*1000,forceN:f,zM:z});prev=d;}
  const loopResidual=Math.abs(work-loss-memoryEnergy(0,z,p)),loopZ=z;for(let i=0;i<960;i++)z=relaxMemory(0,z,h,p).z;
  function simulate(rate,velocity,kind='memory',km=.6e9){
    const tri=new helpers.Trichord({stringOptions:{sampleRate:rate,maxFrequencyHz:16000}},helpers);
    const m=kind==='elastic'?new HammerTrichord(tri,{initialVelocityMps:velocity,kNPerMPower:1.4e9,rateFactorSPerM:0}):new MemoryHammer(tri,{initialVelocityMps:velocity,memoryK:km});
    const initial=m.energy();let peak=0,compression=0,first=null,last=null,maxIncrease=0,maxBalance=0,prev=initial,maxResidual=0,maxMemory=0;
    for(let i=0;i<Math.ceil(.008*rate);i++){const s=m.step(),e=m.energy(),l=tri.ledger();if(s.sum>1e-9){if(first===null)first=m.time-m.h;last=m.time;}peak=Math.max(peak,s.sum);compression=Math.max(compression,...s.compression);maxIncrease=Math.max(maxIncrease,e-prev);prev=e;maxBalance=Math.max(maxBalance,Math.abs(e+l.lossJ+m.contactLossJ-initial));maxResidual=Math.max(maxResidual,m.lastResidual);if(m.z)maxMemory=Math.max(maxMemory,...m.z);}
    let high=0;for(const s of tri.strings)for(let i=0;i<s.vertical.modes.length;i++){const q=s.vertical.modes[i];if(q.frequencyHz>=3000)high+=.5*(q.massKg*s.vertical.v[i]**2+q.stiffnessNPerM*s.vertical.x[i]**2);}
    return {rate,velocity,peakForceN:peak,maxCompressionM:compression,contactMs:1000*(last-first),exitVelocityMps:m.v,stringEnergyJ:tri.energy(),highFraction:high/tri.energy(),contactLossJ:m.contactLossJ,maxMemoryM:maxMemory,remainingMemoryM:m.z?Math.max(...m.z):0,maxIncrease,maxBalance,maxResidual,maxRelaxResidualJ:m.maxRelaxResidualJ??0,finalForceN:m.lastForces.reduce((a,b)=>a+b,0),impulseResidual:Math.abs(m.massKg*(velocity-m.v)-m.impulseNs)};
  }
  const dynamics=[.5,1,2.5].map(v=>simulate(96000,v)),convergence=[simulate(48000,1),dynamics[1],simulate(192000,1)],zeroBranch=simulate(48000,1,'memory',0),elastic=simulate(48000,1,'elastic');
  const cases=[
    ['no tension for separated felt',()=>a(frozenMemoryForce(-.001,-.0001,.0001,p)===0,'unilateral')],
    ['uncompressed fresh felt has zero energy',()=>a(memoryEnergy(-.001,0,p)===0,'zero')],
    ['relaxation decreases force toward equilibrium at fixed compression',()=>a(hold.slice(1).every((v,i)=>v.forceN<=hold[i].forceN+1e-12)&&hold.at(-1).forceN<hold[0].forceN*.9&&holdResidual<1e-12,'hold '+JSON.stringify({hold,holdResidual}))],
    ['relaxation loss equals independently evaluated potential change',()=>{const q=relaxMemory(.0004,.0001,h,p);a(q.lossJ>=0&&Math.abs(q.residualJ)<1e-14,'loss')}],
    ['frozen memory force is exact discrete gradient',()=>{const x=.0003,y=.0004,z=.0001;a(near(frozenMemoryForce(x,y,z,p)*(y-x),memoryEnergy(y,z,p)-memoryEnergy(x,z,p),1e-14),'gradient')}],
    ['load unload cycle has positive dissipation',()=>a(work>0&&loss>0&&loopResidual<1e-12,'loop')],
    ['unloaded memory recovers without negative state',()=>a(loopZ>0&&z>=0&&z<loopZ*.001,'recovery')],
    ['history changes force at same compression',()=>a(instantaneous(.0004,.0001)<instantaneous(.0004,0),'history')],
    ['shared impact remains passive and force law solved',()=>a(dynamics.concat(convergence).every(q=>q.maxIncrease<1e-10&&q.maxBalance<1e-10&&q.maxResidual<1e-7&&q.maxRelaxResidualJ<1e-12),'passivity '+JSON.stringify(dynamics))],
    ['rebound and separation without cutoff',()=>a(dynamics.every(q=>q.finalForceN===0&&q.exitVelocityMps<0),'rebound')],
    ['impulse equals hammer momentum change',()=>a(dynamics.every(q=>q.impulseResidual<1e-12),'impulse')],
    ['higher velocities increase peak and transferred energy',()=>a(dynamics.slice(1).every((q,i)=>q.peakForceN>dynamics[i].peakForceN&&q.stringEnergyJ>dynamics[i].stringEnergyJ),'dynamics')],
    ['memory branch zero recovers elastic reference',()=>a(near(zeroBranch.peakForceN,elastic.peakForceN,1e-7)&&near(zeroBranch.stringEnergyJ,elastic.stringEnergyJ,1e-10)&&zeroBranch.contactLossJ<1e-12,'elastic')],
    ['time refinement reduces peak error',()=>a(Math.abs(convergence[1].peakForceN-convergence[2].peakForceN)<Math.abs(convergence[0].peakForceN-convergence[2].peakForceN),'refinement '+JSON.stringify(convergence))],
    ['invalid memory input rejected',()=>{reject(()=>relaxMemory(0,0,h,{...p,viscosity:0}));reject(()=>relaxMemory(0,-1,h,p));reject(()=>relaxMemory(0,0,1,p));}]
  ];
  for(const [name,f] of cases){try{f()}catch(e){throw Error(name+': '+e.message)}}
  return {passed:cases.map(c=>c[0]),hold,holdResidual,loop,loopWorkJ:work,loopLossJ:loss,loopResidual,loopZ,recoveredZ:z,dynamics,convergence,zeroBranch,elastic};
}
const result=runChecks({Trichord,StiffString,modalCoefficients,makeDesign,solidWire});for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));
