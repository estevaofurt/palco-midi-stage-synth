import {solidWire} from '../c3x-physical/c4-wire-consistency.mjs';
import {makeDesign} from './c4-design.mjs';
import {stringMode,spatialWeight} from './stiff-string.mjs';
import {MovingBridge} from './moving-bridge.mjs';
import {MobileMemoryHammer} from './mobile-hammer.mjs';
import {PolarizedBridge,PolarizedHammer} from './polarized-bridge.mjs';
function checks(hp){
  const a=(v,m)=>{if(!v)throw Error(m)};
  const wires=[-.5,0,.5].map(c=>hp.makeDesign(hp.solidWire,{f1Hz:440*2**(-9/12+c/1200)}));
  const make=o=>new PolarizedBridge(wires,o,hp);
  const b=make({sampleRate:48000});b.vAxis.x[0]=1e-5;b.hAxis.x[1]=2e-5;
  const G=b.contactCompliance(),f=[.1,.2,.3],pred=b.freeContacts().map((v,i)=>v+G[i].reduce((s,c,j)=>s+c*f[j],0));
  b.step(f);const affineError=Math.max(...pred.map((v,i)=>Math.abs(v-b.contactDisplacement(i))));
  function impact(rate,velocity=1,angleRad=.25){
    const b=make({sampleRate:rate,angleRad}),m=new PolarizedHammer(b,{velocityMps:velocity}),e0=m.energy();
    let peak=0,maxH=0,maxV=0,residual=0,maxIncrease=0,previous=e0,forceRes=0,last=0,maxWorkErr=0;
    for(let i=0;i<Math.round(.008*rate);i++){
      const y0=wires.map((_,j)=>b.contactDisplacement(j)),w0=b.workJ,s=m.step(),e=m.energy();
      last=s.sum;peak=Math.max(peak,s.sum);maxH=Math.max(maxH,Math.abs(b.hAxis.b));maxV=Math.max(maxV,Math.abs(b.vAxis.b));
      residual=Math.max(residual,Math.abs(e+b.lossJ+m.lossJ-e0));maxIncrease=Math.max(maxIncrease,e-previous);previous=e;
      forceRes=Math.max(forceRes,m.lastResidual);
      const work=s.forces.reduce((t,f,j)=>t+f*(b.contactDisplacement(j)-y0[j]),0);
      maxWorkErr=Math.max(maxWorkErr,Math.abs(b.workJ-w0-work));
    }
    return {rate,velocity,angleRad,peak,maxH,maxV,residual,maxIncrease,forceRes,last,rebounce:m.v,maxWorkErr,wireV:wires.reduce((s,_,j)=>s+b.wireEnergy('v',j),0),wireH:wires.reduce((s,_,j)=>s+b.wireEnergy('h',j),0),bridgeLoss:b.bridgeLossJ,stringLoss:b.stringLossJ,feltLoss:m.lossJ};
  }
  const dyn=[.5,1,2.5].map(v=>impact(96000,v)),rates=[impact(48000),dyn[1],impact(192000),impact(384000)],zero=impact(96000,1,0);
  const oldB=new hp.MovingBridge(wires,{sampleRate:96000},hp),old=new hp.MobileMemoryHammer(oldB);let oldPeak=0;for(let i=0;i<768;i++)oldPeak=Math.max(oldPeak,old.step().sum);
  const mobility=[100,261,262,500,1000,1400,3000,8000,12000].map(f=>b.mobility(f));
  function decay(angleRad,axis='v'){
    const rate=96000,b=make({sampleRate:rate,maxFrequencyHz:4000,angleRad});(axis==='v'?b.vAxis:b.hAxis).x[0]=1e-4;
    const initial=b.energy();let maxOther=0,maxBalance=0,maxIncrease=0,prev=initial;const samples=[];
    for(let i=0;i<=rate*.2;i++){
      const ev=wires.reduce((s,_,j)=>s+b.wireEnergy('v',j),0),eh=wires.reduce((s,_,j)=>s+b.wireEnergy('h',j),0),e=b.energy();
      maxOther=Math.max(maxOther,axis==='v'?eh:ev);maxBalance=Math.max(maxBalance,Math.abs(e+b.lossJ-initial));maxIncrease=Math.max(maxIncrease,e-prev);prev=e;
      if(i%2400===0)samples.push({ms:i/rate*1000,verticalPct:100*ev/initial,horizontalPct:100*eh/initial,totalPct:100*e/initial});
      if(i<rate*.2)b.step();
    }
    return {angleRad,axis,initial,maxOther,maxBalance,maxIncrease,samples};
  }
  const dec=[decay(.25),decay(0),decay(.25,'h')];
  const cases=[
    ['rotated stiffness and damping PSD',()=>a(b.K.vv*b.K.hh-b.K.vh**2>0&&b.C.vv*b.C.hh-b.C.vh**2>0,'tensor')],
    ['contact prediction affine and reciprocal',()=>a(affineError<1e-15&&G.every((row,i)=>row.every((v,j)=>v>=0&&Math.abs(v-G[j][i])<1e-20)),'affine')],
    ['uncoupled vertical limit matches F5.2',()=>a(Math.abs(zero.peak-oldPeak)<1e-8&&zero.wireH===0&&zero.maxH===0,'parity')],
    ['horizontal appears only with physical cross coupling',()=>a(dyn.every(q=>q.wireH>0&&q.maxH>0),'horizontal')],
    ['reciprocal transfer in both initial polarizations',()=>a(dec[0].maxOther>1e-12&&dec[2].maxOther>1e-12&&dec[1].maxOther===0,'transfer')],
    ['passive decay across scenarios',()=>a(dec.every(q=>q.maxBalance<1e-12&&q.maxIncrease<1e-12),'decay')],
    ['impact energy balance, contact reaction and work',()=>a([...dyn,...rates,zero].every(q=>q.residual<1e-10&&q.maxIncrease<1e-10&&q.forceRes<1e-8&&q.maxWorkErr<1e-12),'impact')],
    ['rebound and release at all speeds',()=>a(dyn.every(q=>q.rebounce<0&&q.last===0),'release')],
    ['dynamics retained',()=>a(dyn.slice(1).every((q,i)=>q.peak>dyn[i].peak&&q.wireV>dyn[i].wireV),'dynamics')],
    ['mobility real part PSD at sampled frequencies',()=>a(mobility.every(q=>q.vv[0]>=0&&q.hh[0]>=0&&q.realDet>=-1e-16&&Number.isFinite(q.crossMagnitude)),'mobility')],
    ['refinement reduces peak error',()=>a(Math.abs(rates[2].peak-rates[3].peak)<Math.abs(rates[0].peak-rates[3].peak),'refine')],
    ['lossless full network energy',()=>{const b=make({sampleRate:96000,maxFrequencyHz:4000,damping:[0,0],verticalLoss:[0,0],horizontalLoss:[0,0]});b.vAxis.x[0]=1e-4;const e=b.energy();for(let i=0;i<1000;i++)b.step();a(Math.abs(b.energy()/e-1)<1e-9,'lossless');}],
    ['cross mobility disappears when aligned',()=>a(make({angleRad:0}).mobility(500).crossMagnitude===0,'zero mobility')]
  ];
  for(const [n,f] of cases){try{f()}catch(e){throw Error(n+': '+e.message)}}
  return {passed:cases.map(c=>c[0]),K:b.K,C:b.C,affineError,oldPeak,dyn,rates,zero,mobility,dec};
}
const result=checks({solidWire,makeDesign,stringMode,spatialWeight,MovingBridge,MobileMemoryHammer});for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));
