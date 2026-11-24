import {plateDesign,plateModes} from './orthotropic-plate.mjs';
import {ribDesign,generalizedEigen} from './ribbed-plate.mjs';
import {mindlinModes} from './mindlin-plate.mjs';
import {radiationGrid,surfaceShape,harmonicRadiation,radiationKernel,kernelResponse,SurfaceRadiator} from './surface-radiation.mjs';
function checks(hp){
 const a=(x,m)=>{if(!x)throw Error(m)},p=hp.plateDesign(),listener={x:1.05,y:.38,z:1},ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>hp.ribDesign(p,{xM}));
 const modes=hp.mindlinModes(p,ribs,{basisHz:4000},hp).modes,selected=[0,9,29,59,99,139,199].map(i=>modes[i]);
 const grids=[16,32,64,128].map(nx=>radiationGrid(p,listener,{nx,ny:Math.round(nx*1.1/1.4)})),reference=radiationGrid(p,listener,{nx:256,ny:200});
 const err=(x,y)=>Math.hypot(x.re-y.re,x.im-y.im)/Math.max(y.magnitude,1e-20);
 const convergence=selected.map((m,i)=>{const shape=(x,y)=>surfaceShape(m,x,y),f=m.frequencyHz,ref=harmonicRadiation(reference,shape,f);return {rank:[1,10,30,60,100,140,200][i],f,reference:ref.magnitude,errors:grids.map(g=>err(harmonicRadiation(g,shape,f),ref)),delayErrors:[48000,96000,192000].map(rate=>err(kernelResponse(radiationKernel(grids[2],shape,rate),f),harmonicRadiation(grids[2],shape,f)))};});
 const centered=radiationGrid(p,{x:p.lengthM/2,y:p.widthM/2,z:1},{nx:64,ny:48}),even=(x,y)=>Math.sin(2*Math.PI*x/p.lengthM)*Math.sin(Math.PI*y/p.widthM);
 const cancellation=harmonicRadiation(centered,even,500).magnitude,off=harmonicRadiation(grids[2],even,500).magnitude;
 const far=z=>harmonicRadiation(radiationGrid(p,{x:p.lengthM/2,y:p.widthM/2,z},{nx:64,ny:48}),()=>1,100);
 const far1=far(100),far2=far(200),analytic=1.204*p.areaM2/(2*Math.PI*100);
 const rad=new SurfaceRadiator(p,[selected[2]],listener,{rate:48000,nx:32,ny:25}),kernel=rad.kernels[0],impulse=[];
 for(let i=0;i<rad.size+10;i++)impulse.push(rad.step([i===0?1:0]));
 const impulseErr=Math.max(...impulse.map((v,i)=>Math.abs(v-(kernel.taps[i-kernel.offset]??0))));
 const rad2=new SurfaceRadiator(p,[selected[2]],listener,{rate:48000,nx:32,ny:25}),f=selected[2].frequencyHz,response=kernelResponse(rad2.kernels[0],f);let toneError=0;
 for(let i=0;i<3000;i++){const phase=2*Math.PI*f*i/48000,v=rad2.step([Math.cos(phase)]);if(i>=rad2.size)toneError=Math.max(toneError,Math.abs(v-(response.re*Math.cos(phase)-response.im*Math.sin(phase))));}
 const directivity=[{name:'center 1m',x:.7,y:.55,z:1},{name:'off axis 1m',...listener},{name:'center 2m',x:.7,y:.55,z:2}].map(l=>({name:l.name,values:selected.map(m=>harmonicRadiation(radiationGrid(p,l), (x,y)=>surfaceShape(m,x,y),m.frequencyHz).magnitude)}));
 const tests=[
 ['uniform piston far-field magnitude',()=>a(Math.abs(far1.magnitude/analytic-1)<.0001,'far')],
 ['inverse distance in far field',()=>a(Math.abs(far1.magnitude/far2.magnitude-2)<.0001,'distance')],
 ['axial symmetry cancels antisymmetric mode',()=>a(cancellation<1e-15&&off>1e-6,'cancel')],
 ['spatial refinement agrees with finer grid',()=>a(convergence.every(q=>q.errors[3]<q.errors[0]&&q.errors[3]<.015),'grid '+JSON.stringify(convergence))],
 ['fractional delay refinement improves complex response',()=>a(convergence.every(q=>q.delayErrors[2]<q.delayErrors[0]&&q.delayErrors[2]<.005),'delay')],
 ['causal kernel and impulse exact reproduction',()=>a(kernel.offset>0&&impulse.slice(0,kernel.offset).every(v=>v===0)&&impulseErr<1e-15,'impulse')],
 ['harmonic time-domain response matches kernel',()=>a(toneError<1e-13,'tone')],
 ['surface sign inversion inverts pressure',()=>{const g=grids[2],x=harmonicRadiation(g,even,500),y=harmonicRadiation(g,(x,y)=>-even(x,y),500);a(Math.hypot(x.re+y.re,x.im+y.im)<1e-15,'sign')}],
 ['modal superposition remains linear',()=>{const g=grids[2],s=(x,y)=>surfaceShape(selected[0],x,y),t=(x,y)=>surfaceShape(selected[1],x,y),u=harmonicRadiation(g,s,500),v=harmonicRadiation(g,t,500),w=harmonicRadiation(g,(x,y)=>s(x,y)+t(x,y),500);a(Math.hypot(u.re+v.re-w.re,u.im+v.im-w.im)<1e-14,'linear')}],
 ['listener geometry rejected outside front half space',()=>{let bad=false;try{radiationGrid(p,{x:0,y:0,z:0})}catch(e){bad=true}a(bad,'invalid')}]
 ];
 for(const [n,f] of tests){try{f()}catch(e){throw Error(n+': '+e.message)}}
 return {passed:tests.map(t=>t[0]),convergence,cancellation,off,farRatio:far1.magnitude/far2.magnitude,farRelativeError:far1.magnitude/analytic-1,impulseErr,toneError,firstDelayMs:1000*kernel.offset/kernel.rate,lastDelayMs:1000*(kernel.offset+kernel.taps.length-1)/kernel.rate,directivity};
}
const result=checks({plateDesign,plateModes,ribDesign,generalizedEigen,mindlinModes});for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));
