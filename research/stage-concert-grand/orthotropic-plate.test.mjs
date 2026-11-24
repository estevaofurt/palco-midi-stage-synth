import {modalCoefficients} from './exact-modal.mjs';
import {plateDesign,plateMode,plateModes,patchWeight,OrthotropicPlate} from './orthotropic-plate.mjs';
function checks(coeff){
  const a=(v,m)=>{if(!v)throw Error(m)},near=(x,y,t)=>Math.abs(x-y)<t;
  const p=plateDesign(),patch={xM:.83,yM:.46,dxM:.04,dyM:.025},other={xM:.37,yM:.71,dxM:.04,dyM:.025},s=new OrthotropicPlate(p,{},coeff),w=s.weights(patch),u=s.weights(other);
  const compliance=[250,500,1000,2000,4000,8000,16000].map(cut=>{const modes=plateModes(p,cut);return {cut,count:modes.length,point:modes.reduce((v,q)=>v+patchWeight(p,q,{xM:patch.xM,yM:patch.yM})**2/q.stiffnessNPerM,0),patch:modes.reduce((v,q)=>v+patchWeight(p,q,patch)**2/q.stiffnessNPerM,0)};});
  const q=plateMode(p,4,5),grid=[16,32,64,128].map(N=>{const lx=4*Math.sin(4*Math.PI/(2*N))**2/(p.lengthM/N)**2,ly=4*Math.sin(5*Math.PI/(2*N))**2/(p.widthM/N)**2,f=Math.sqrt((p.D11*lx**2+2*(p.D12+2*p.D66)*lx*ly+p.D22*ly**2)/p.arealMass)/(2*Math.PI);return {N,errorPct:100*(f/q.frequencyHz-1)};});
  const mobility=[50,100,261.63,500,1000,2000,4000].map(f=>({f,...s.mobility(f,w),cross:s.mobility(f,w,u).magnitude}));
  let quadratureError=0;
  const cases=[
    ['positive orthotropic bending tensor and reciprocal Poisson ratios',()=>a(p.D11*p.D22>p.D12**2&&p.D66>0&&near(p.nuXY/p.ExPa,p.nuYX/p.EyPa,1e-20),'tensor')],
    ['total and modal mass geometry',()=>a(near(p.massKg,5.2976,1e-12)&&s.modes.every(q=>q.massKg===p.massKg/4),'mass')],
    ['isotropic square analytic degeneracy and frequency',()=>{const E=10e9,nu=.3,z=plateDesign({lengthM:1,widthM:1,ExPa:E,EyPa:E,GxyPa:E/(2*(1+nu)),nuXY:nu});const q=plateMode(z,2,3);a(near(q.frequencyHz,Math.PI/2*Math.sqrt(z.D11/z.arealMass)*13,1e-10)&&near(q.frequencyHz,plateMode(z,3,2).frequencyHz,1e-10),'isotropic')}],
    ['orthotropic direction produces distinct frequencies',()=>{const z=plateDesign({lengthM:1,widthM:1});a(plateMode(z,2,1).frequencyHz>plateMode(z,1,2).frequencyHz,'anisotropy')}],
    ['complete sorted cutoff checked against exhaustive enumeration',()=>{const brute=[];for(let m=1;m<=100;m++)for(let n=1;n<=100;n++){const q=plateMode(p,m,n);if(q.frequencyHz<4000)brute.push(q);}a(brute.length===s.modes.length&&s.modes.every((q,i)=>q.frequencyHz<4000&&(i===0||q.frequencyHz>=s.modes[i-1].frequencyHz)),'basis')}],
    ['pinned boundaries and nodal symmetry',()=>a(s.weights({xM:0,yM:.5}).every(x=>x===0)&&Math.abs(patchWeight(p,plateMode(p,2,1),{xM:p.lengthM/2,yM:.4}))<1e-14,'boundary')],
    ['patch projection matches numerical quadrature',()=>{const q=plateMode(p,4,5),N=2048;let ax=0,ay=0;for(let i=0;i<N;i++){ax+=Math.sin(q.kx*(patch.xM-patch.dxM/2+patch.dxM*(i+.5)/N))/N;ay+=Math.sin(q.ky*(patch.yM-patch.dyM/2+patch.dyM*(i+.5)/N))/N;}quadratureError=Math.abs(ax*ay-patchWeight(p,q,patch));a(quadratureError<1e-7,'quadrature '+quadratureError)}],
    ['power conjugacy',()=>{const v=Float64Array.from(w,(_,i)=>Math.sin(i)*.001);a(near(w.reduce((t,x,i)=>t+x*.2*v[i],0),.2*s.projection(w,v),1e-14),'power')}],
    ['zero state silent',()=>{s.step();a(s.energy()===0,'zero')}],
    ['lossless exact modal propagation conserves energy',()=>{const b=new OrthotropicPlate(p,{cutoffHz:1000,loss0:0,lossSlope:0},coeff);b.x[0]=1e-4;const e=b.energy();for(let i=0;i<4800;i++)b.step();a(Math.abs(b.energy()/e-1)<1e-9,'energy')}],
    ['damped free motion passive',()=>{const b=new OrthotropicPlate(p,{cutoffHz:1000},coeff);b.x[0]=1e-4;let e=b.energy(),e0=e;for(let i=0;i<4800;i++){b.step();const n=b.energy();a(n<=e+1e-14,'increase');e=n;}a(b.lossJ>0&&near(e+b.lossJ,e0,1e-12),'loss')}],
    ['multiple patch forces and energy balance',()=>{for(let i=0;i<480;i++)s.step([{weights:w,forceN:.1*Math.sin(i*.1)},{weights:u,forceN:.05*Math.cos(i*.04)}]);a(near(s.energy()+s.lossJ,s.workJ,1e-12),'work')}],
    ['reciprocal mobility and PSD real matrix',()=>a(mobility.every(q=>{const ab=s.mobility(q.f,w,u),ba=s.mobility(q.f,u,w),bb=s.mobility(q.f,u);return q.real>=0&&bb.real>=0&&q.real*bb.real-ab.real**2>=-1e-15&&near(ab.real,ba.real,1e-14)&&near(ab.imag,ba.imag,1e-14)}),'FRF')],
    ['static compliance converges from below',()=>a(compliance.slice(1).every((q,i)=>q.point>=compliance[i].point&&q.patch>=compliance[i].patch),'static')],
    ['independent spatial finite difference eigenvalue convergence',()=>a(grid.slice(1).every((q,i)=>Math.abs(grid[i].errorPct/q.errorPct)>3.5&&Math.abs(grid[i].errorPct/q.errorPct)<4.5),'spatial')],
    ['invalid elastic tensor rejected',()=>{let bad=false;try{plateDesign({nuXY:10})}catch(e){bad=true}a(bad,'invalid')}]
  ];
  for(const [name,fn] of cases){try{fn()}catch(e){throw Error(name+': '+e.message)}}
  return {passed:cases.map(c=>c[0]),p,first:s.modes.slice(0,10).map(({m,n,frequencyHz})=>({m,n,frequencyHz})),count:s.modes.length,compliance,grid,mobility,quadratureError};
}
const result=checks(modalCoefficients);for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));
