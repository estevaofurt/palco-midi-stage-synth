// G2.09d: orthotropic ribbed Mindlin board, independent mechanical ports.
import {plateDesign,plateModes,patchWeight} from '../stage-concert-grand/orthotropic-plate.mjs';
import {ribDesign,generalizedEigen,ribbedPatchWeight} from '../stage-concert-grand/ribbed-plate.mjs';
import {mindlinModes} from '../stage-concert-grand/mindlin-plate.mjs';
import {PortMode} from './g2_arch_port.mjs';
export const MATERIALS=Object.freeze({
 control:Object.freeze({densityKgM3:430,ExPa:11e9,EyPa:.8e9,GxyPa:.65e9,nuXY:.3}),
 sitka:Object.freeze({densityKgM3:392,ExPa:11.5e9,EyPa:.47e9,GxyPa:.50e9,nuXY:.3}),
 norway:Object.freeze({densityKgM3:440,ExPa:15.8e9,EyPa:.85e9,GxyPa:.84e9,nuXY:.3})
});
export const PATCHES=Object.freeze([
 Object.freeze({key:48,xM:.65,yM:.60,dxM:.04,dyM:.025}),
 Object.freeze({key:60,xM:.83,yM:.46,dxM:.04,dyM:.025}),
 Object.freeze({key:84,xM:1.05,yM:.32,dxM:.04,dyM:.025})
]);
export function buildBoard(id,basisHz=4000){
 if(!Object.hasOwn(MATERIALS,id))throw RangeError('material');
 const p=plateDesign(MATERIALS[id]),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>ribDesign(p,{xM}));
 // Keep transverse shear and rib properties identical: not measured complete species tensors.
 const r=mindlinModes(p,ribs,{basisHz},{plateModes,generalizedEigen});
 return {id,p,ribs,basisHz,...r};
}
export function weights(b,patch){return b.modes.map(m=>ribbedPatchWeight(b.p,m,patch,patchWeight));}
export function staticFlex(b,patch,cutoff=Infinity){
 const w=weights(b,patch);return b.modes.reduce((s,m,i)=>s+(m.frequencyHz<cutoff?w[i]**2/m.lambda:0),0);
}
export class BoardPilot {
 constructor(b,sr=48000,{cutoffHz=3000,loss0=2,lossSlope=.0005}={}){
  if(![48000,96000].includes(sr)||!Number.isFinite(cutoffHz)||cutoffHz<=0||cutoffHz>.4*sr||![loss0,lossSlope].every(x=>Number.isFinite(x)&&x>=0))throw RangeError('board options');
  this.info=b.modes.filter(m=>m.frequencyHz<cutoffHz);
  this.w=PATCHES.map(p=>this.info.map(m=>ribbedPatchWeight(b.p,m,p,patchWeight)));
  this.modes=this.info.map(m=>new PortMode({massKg:1,frequencyHz:m.frequencyHz,dampingNsM:2*(loss0+lossSlope*2*Math.PI*m.frequencyHz),dt:1/sr}));
  this.workJ=0;this.lossJ=0;this.stepLossJ=0;this.h=1/sr;
 }
 energy(){return this.modes.reduce((s,m)=>s+m.energy(),0);}
 position(j){return this.modes.reduce((s,m,i)=>s+this.w[j][i]*m.x,0);}
 velocity(j){return this.modes.reduce((s,m,i)=>s+this.w[j][i]*m.velocity(),0);}
 step(forces=[0,0,0]){
  if(forces.length!==3||!Array.from(forces).every(Number.isFinite))throw RangeError('forces');
  let work=0,loss=0;
  for(let i=0;i<this.modes.length;i++){const m=this.modes[i],f=this.w.reduce((s,w,j)=>s+w[i]*forces[j],0),x=m.x,e=m.energy();m.advance(f);const dw=f*(m.x-x);work+=dw;loss+=dw+e-m.energy();}
  this.workJ+=work;this.lossJ+=loss;this.stepLossJ=loss;
 }
 mobility(f,j,k=j){
  if(!Number.isFinite(f)||f<=0)throw RangeError('frequency');
  let re=0,im=0;const w=2*Math.PI*f;
  for(let i=0;i<this.modes.length;i++){const m=this.modes[i],a=m.p.k-w*w,b=2*m.sigma*w,den=a*a+b*b,z=this.w[j][i]*this.w[k][i]*w/den;re+=z*b;im+=z*a;}
  return [re,im];
 }
}
