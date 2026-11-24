import {solidWire} from '../c3x-physical/c4-wire-consistency.mjs';
import {makeDesign} from './c4-design.mjs';
import {stringMode,spatialWeight} from './stiff-string.mjs';
import {plateDesign,plateModes,patchWeight} from './orthotropic-plate.mjs';
import {ribDesign,generalizedEigen} from './ribbed-plate.mjs';
import {mindlinModes} from './mindlin-plate.mjs';
import {PolarizedBridge,PolarizedHammer} from './polarized-bridge.mjs';
import {BoardPort,BoardCoupledBridge} from './board-coupling.mjs';
import {radiationGrid,surfaceShape,radiationKernel,SurfaceRadiator} from './surface-radiation.mjs';
import {captureAcceleration,pressureTrace,sineIntegral,bandEnergy} from './vibroacoustic-observer.mjs';
function study(hp){
 const a=(v,m)=>{if(!v)throw Error(m)},p=hp.plateDesign(),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>hp.ribDesign(p,{xM})),patch={xM:.83,yM:.46,dxM:.04,dyM:.025},wires=[-.5,0,.5].map(c=>hp.makeDesign(hp.solidWire,{f1Hz:440*2**(-9/12+c/1200)}));
 const basis=hp.mindlinModes(p,ribs,{basisHz:4000},hp).modes,listener={x:1.05,y:.38,z:1};
 function run(rate,cut=1500,velocity=1){const modes=basis.filter(m=>m.frequencyHz<cut),bridge=new hp.PolarizedBridge(wires,{sampleRate:rate,stiffness:[0,2e6],damping:[0,5]},hp),board=new hp.BoardPort(p,modes,patch,bridge.h,{},hp),b=new hp.BoardCoupledBridge(bridge,board),h=new hp.PolarizedHammer(b,{velocityMps:velocity});return {...captureAcceleration(h,board,Math.round(.012*rate)),modes,cut,velocity};}
 const standard=run(96000),coarse=run(48000),wide=run(96000,2000),soft=run(96000,1500,.5),loud=run(96000,1500,2.5);
 const pressure=(s,l=listener,nx=64)=>pressureTrace(p,s.modes,s.trace,s.rate,l,{nx,ny:Math.round(nx*1.1/1.4)},hp);
 const y=pressure(standard),yFine=pressure(standard,listener,128),yLow=pressure(coarse),yWide=pressure(wide);
 const rms=x=>Math.sqrt(x.reduce((s,v)=>s+v*v,0)/x.length),peak=x=>x.reduce((s,v)=>Math.max(s,Math.abs(v)),0),relative=(x,y)=>Math.sqrt(x.reduce((s,v,i)=>s+(v-(y[i]??0))**2,0)/y.reduce((s,v)=>s+v*v,0));
 const down=Float64Array.from({length:yLow.length},(_,i)=>((y[2*i]??0)+(y[2*i+1]??0))/2);
 const fineError=relative(y,yFine),timeError=relative(yLow,down),bandError=relative(y,yWide);
 const positions=[{x:.7,y:.55,z:1},listener,{x:.7,y:.55,z:2}].map(l=>{const q=pressure(standard,l);return {...l,peakPa:peak(q),rmsPa:rms(q)};});
 const energies=[bandEnergy(p,standard.modes,standard.trace,standard.rate,{nt:6,np:12}),bandEnergy(p,standard.modes,standard.trace,standard.rate,{nt:12,np:24}),bandEnergy(p,standard.modes,standard.trace,standard.rate,{nt:18,np:36})];
 const one={...standard.modes[0]},rad=new hp.SurfaceRadiator(p,[one],listener,{rate:96000,nx:16,ny:13}),imp=Float64Array.from({length:64},(_,i)=>i===0?1:0),offline=pressureTrace(p,[one],[imp],96000,listener,{nx:16,ny:13},hp);
 let parity=0;for(let i=0;i<offline.length;i++)parity=Math.max(parity,Math.abs(offline[i]-rad.step([imp[i]??0])));
 const f=2*Math.PI/p.lengthM,I=sineIntegral(2,p.lengthM,f),I0=sineIntegral(1,p.lengthM,0);
 const dyn=[soft,standard,loud].map(s=>({velocity:s.velocity,peakPa:peak(pressure(s)),boardLoss:s.boardLoss,initial:s.initial}));
 const test=[
 ['mechanical regression F6.4',()=>a(Math.abs(standard.boardEnergy-.0003397351744967451)<1e-12,'regression')],
 ['mean acceleration agrees with independent velocity equation',()=>a(standard.derivativeError<1e-8,'derivative '+standard.derivativeError)],
 ['all mechanical impacts remain passive',()=>a([standard,coarse,wide,soft,loud].every(s=>s.residual<1e-10&&s.maxIncrease<1e-10),'energy')],
 ['offline convolution equals streaming reference',()=>a(parity<1e-14,'parity')],
 ['analytical sine transform at zero and resonance',()=>a(Math.abs(I[0])<1e-12&&Math.abs(I[1]-p.lengthM/2)<1e-12&&Math.abs(I0[0]-2*p.lengthM/Math.PI)<1e-12,'integral')],
 ['pressure onset follows propagation delay',()=>a(y.slice(0,Math.floor(96000/343)).every(v=>v===0),'delay')],
 ['spatial refinement small for integrated trace',()=>a(fineError<.03,'grid '+fineError)],
 ['time and band diagnostics finite',()=>a(Number.isFinite(timeError)&&Number.isFinite(bandError),'diagnostics')],
 ['stronger hammer produces larger peak pressure',()=>a(dyn[0].peakPa<dyn[1].peakPa&&dyn[1].peakPa<dyn[2].peakPa,'dynamic')],
 ['hemisphere energy positive and angular refinement converges',()=>a(energies.every(q=>q.energyJ>0)&&Math.abs(energies[1].energyJ/energies[2].energyJ-1)<.03,'angular '+JSON.stringify(energies))],
 ['zero input radiates zero energy',()=>a(bandEnergy(p,[one],[new Float64Array(32)],96000,{nt:2,np:4}).energyJ===0,'zero')]
 ];
 for(const [n,f] of test){try{f()}catch(e){throw Error(n+': '+e.message)}}
 const compact=({trace,modes,...q})=>({...q,count:modes.length});
 return {passed:test.map(t=>t[0]),standard:compact(standard),coarse:compact(coarse),wide:compact(wide),positions,dyn,energies,fineError,timeError,bandError,parity,peakPa:peak(y),rmsPa:rms(y)};
}
const result=study({solidWire,makeDesign,stringMode,spatialWeight,plateDesign,plateModes,patchWeight,ribDesign,generalizedEigen,mindlinModes,PolarizedBridge,PolarizedHammer,BoardPort,BoardCoupledBridge,radiationGrid,surfaceShape,radiationKernel,SurfaceRadiator});for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));
