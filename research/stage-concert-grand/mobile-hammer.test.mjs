import {solidWire} from '../c3x-physical/c4-wire-consistency.mjs';
import {makeDesign} from './c4-design.mjs';
import {modalCoefficients} from './exact-modal.mjs';
import {StiffString,stringMode,spatialWeight} from './stiff-string.mjs';
import {Trichord} from './trichord.mjs';
import {MemoryHammer} from './felt-memory.mjs';
import {MovingBridge} from './moving-bridge.mjs';
import {contactCompliance,freeContacts,solveCoupledContact,MobileMemoryHammer} from './mobile-hammer.mjs';
function checks(hp){
  const a=(v,m)=>{if(!v)throw Error(m)},wires=[-.5,0,.5].map(c=>hp.makeDesign(hp.solidWire,{f1Hz:440*2**(-9/12+c/1200)}));
  const bridge=(rate,k=1e6,cut=16000)=>new hp.MovingBridge(wires,{sampleRate:rate,maxFrequencyHz:cut,bridgeK:k},hp);
  const sim=(rate,v=1,k=1e6,cut=16000,offsets=[0,0,0])=>{
    const b=bridge(rate,k,cut),m=new MobileMemoryHammer(b,{velocityMps:v,offsets}),e0=m.energy();let peak=0,comp=0,first=-1,last=-1,lastForce=0,maxB=0,maxIncrease=0,prev=e0,maxBalance=0,res=0,contactWork=0,maxConjugacy=0;
    const spec=[500,1000,3000,6000,10000].map(f=>({f,re:0,im:0}));let t=0;
    for(let i=0;i<Math.round(.008*rate);i++){const before=b.wires.map((_,j)=>b.contactDisplacement(j)),work0=b.workJ,s=m.step(),e=m.energy();lastForce=s.sum;if(s.sum>1e-9){if(first<0)first=i;last=i;}peak=Math.max(peak,s.sum);comp=Math.max(comp,...s.compression);maxB=Math.max(maxB,Math.abs(b.b));maxIncrease=Math.max(maxIncrease,e-prev);prev=e;maxBalance=Math.max(maxBalance,Math.abs(e+b.lossJ+m.lossJ-e0));res=Math.max(res,m.lastResidual);const work=s.forces.reduce((q,f,j)=>q+f*(b.contactDisplacement(j)-before[j]),0);contactWork+=work;maxConjugacy=Math.max(maxConjugacy,Math.abs(b.workJ-work0-work));t=(i+.5)/rate;for(const q of spec){q.re+=s.sum*Math.cos(2*Math.PI*q.f*t)/rate;q.im+=s.sum*Math.sin(2*Math.PI*q.f*t)/rate;}}
    return {rate,v,k,cut,peakN:peak,compressionMm:comp*1000,contactMs:(last-first+1)*1000/rate,rebounce:m.v,wireEnergyJ:b.wires.reduce((s,_,j)=>s+b.wireEnergy(j),0),bridgeEnergyJ:.5*(b.bridgeK*b.b*b.b+(b.mB-b.wires.reduce((s,w)=>s+w.massKg/3,0))*b.vb*b.vb),bridgeLossJ:b.bridgeLossJ,wireLossJ:b.stringLossJ,feltLossJ:m.lossJ,contactWork,maxConjugacy,maxB,maxIncrease,maxBalance,res,finalForce:lastForce,impulseError:Math.abs(m.massKg*(v-m.v)-m.impulseNs),methods:m.methods,spectrum:spec.map(q=>({f:q.f,db:20*Math.log10(Math.hypot(q.re,q.im)/m.impulseNs)}))};
  };
  const dyn=[.5,1,2.5].map(v=>sim(96000,v)),rates=[sim(48000),dyn[1],sim(192000),sim(384000)],rigid=sim(192000,1,1e14),asym=sim(96000,2.5,1e6,16000,[0,.00005,.0001]),cut=[sim(192000,1,1e6,8000),rates[2],sim(192000,1,1e6,32000)];
  const tri=new hp.Trichord({stringOptions:{sampleRate:192000,maxFrequencyHz:16000}},hp),fixed=new hp.MemoryHammer(tri);let fixedPeak=0;for(let i=0;i<1536;i++)fixedPeak=Math.max(fixedPeak,fixed.step().sum);
  const fixedResult={peakN:fixedPeak,wireEnergyJ:tri.energy(),rebounce:fixed.v};
  const b=bridge(48000);b.x[0]=.00002;b.v[2]=.01;b.b=1e-7;b.vb=.0001;
  const G=contactCompliance(b),f=[.12,.25,.08],pred=freeContacts(b).map((v,i)=>v+G[i].reduce((s,c,j)=>s+c*f[j],0));b.step(f);const responseError=Math.max(...pred.map((v,i)=>Math.abs(v-b.contactDisplacement(i))));
  const p={ke:1.4e9,km:.6e9,kr:1000,viscosity:1,power:2.5},strong=solveCoupledContact([.0004,.0004,.0004],[.0005,.0005,.0005],[[2e-5,1e-5,1e-5],[1e-5,2e-5,1e-5],[1e-5,1e-5,2e-5]],[0,0,0],p);
  const all=[...dyn,...rates,rigid,asym,...cut];
  const cases=[
    ['affine predicted contact displacement matches actual step',()=>a(responseError<1e-15,'prediction')],
    ['compliance reciprocal and positive cross-coupling',()=>a(G.every((row,i)=>row.every((v,j)=>v>0&&Math.abs(v-G[j][i])<1e-20)),'G')],
    ['strong contact coordinate fallback converges',()=>a(strong.method==='coordinate'&&strong.residual<1e-9,'fallback')],
    ['all contacts passive and energy balanced',()=>a(all.every(q=>q.maxIncrease<1e-10&&q.maxBalance<1e-10&&q.res<1e-8),'energy '+JSON.stringify(all))],
    ['contact work equals bridge subsystem work',()=>a(all.every(q=>q.maxConjugacy<1e-12&&Number.isFinite(q.bridgeEnergyJ)&&q.bridgeEnergyJ>=0&&Math.abs(q.contactWork-q.bridgeLossJ-q.wireLossJ-q.wireEnergyJ-q.bridgeEnergyJ)<1e-12),'work')],
    ['hammer impulse and reaction',()=>a(all.every(q=>q.impulseError<1e-12),'impulse')],
    ['rebound and release',()=>a(all.every(q=>q.rebounce<0&&q.finalForce===0),'release')],
    ['stronger touches increase force and string energy',()=>a(dyn.slice(1).every((q,i)=>q.peakN>dyn[i].peakN&&q.wireEnergyJ>dyn[i].wireEnergyJ),'dynamic')],
    ['mobile bridge receives motion and dissipates energy',()=>a(dyn.every(q=>q.maxB>0&&q.bridgeLossJ>0),'bridge')],
    ['rigid limit suppresses bridge and approaches exact fixed support',()=>a(rigid.maxB<rates[2].maxB*.001&&Math.abs(rigid.peakN/fixedPeak-1)<.01&&Math.abs(rigid.wireEnergyJ/fixedResult.wireEnergyJ-1)<.01,'rigid '+JSON.stringify({rigid,fixedResult}))],
    ['temporal refinement improves peak',()=>a(Math.abs(rates[2].peakN-rates[3].peakN)<Math.abs(rates[0].peakN-rates[3].peakN),'refinement')],
    ['spectra finite at all rates and cutoffs',()=>a(all.every(q=>q.spectrum.every(s=>Number.isFinite(s.db))),'spectra')],
    ['asymmetric strong contact remains solved',()=>a(asym.res<1e-8&&asym.contactWork>0,'asym')]
  ];
  for(const [n,f] of cases){try{f()}catch(e){throw Error(n+': '+e.message)}}
  return {passed:cases.map(c=>c[0]),G,responseError,strong,dyn,rates,rigid,fixedResult,asym,cut};
}
const result=checks({solidWire,makeDesign,modalCoefficients,StiffString,stringMode,spatialWeight,Trichord,MemoryHammer,MovingBridge});for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));
