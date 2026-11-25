// G2.07b: abstract two-coordinate dissipative system, not a piano unison or body.
import {PortMode} from './g2_arch_port.mjs';
import {exactFree} from './g2_decay.mjs';
export const REGIMES=Object.freeze({
 control:Object.freeze({fast:.4,slow:.4,fastWeight:.9}),
 mixed:Object.freeze({fast:2,slow:.2,fastWeight:.9}),
 fastOnly:Object.freeze({fast:2,slow:.2,fastWeight:1}),
 slowOnly:Object.freeze({fast:2,slow:.2,fastWeight:0})
});
export class TwoRegimeProof {
 constructor(f,sr,{fast,slow,fastWeight}){
  if(![f,sr,fast,slow,fastWeight].every(Number.isFinite)||f<=0||sr<=0||fast<0||slow<0||fastWeight<0||fastWeight>1)throw RangeError('regime');
  this.weights=[Math.sqrt(fastWeight),Math.sqrt(1-fastWeight)];
  this.modes=[fast,slow].map(sigma=>new PortMode({massKg:.004,frequencyHz:f,dampingNsM:.008*sigma,dt:1/sr}));
  // Physical x-axis initial displacement, zero velocity, expressed in orthonormal eigenbasis.
  for(let i=0;i<2;i++)this.modes[i].init(1e-4*this.weights[i],0);
 }
 energy(){return this.modes.reduce((s,m)=>s+m.energy(),0);}
 step(){for(const m of this.modes)m.advance(0);}
 projection(){return this.modes.reduce((s,m,i)=>s+this.weights[i]*m.x,0);}
 sample(t){
  const states=this.modes.map(m=>exactFree(m,t));
  return {x:states.reduce((s,m,i)=>s+this.weights[i]*m.x,0),energyJ:states.reduce((s,m)=>s+m.energyJ,0),
   // Quadrature magnitude of weighted components, a diagnostic coherent envelope;
   // damped frequencies need not be identical, so retain phase.
   envelopeM:Math.hypot(...[0,1].map(axis=>this.modes.reduce((s,m,i)=>{
    const x=m.x,y=m.y,r=Math.exp(-m.sigma*t),c=Math.cos(m.w*t),d=Math.sin(m.w*t);
    return s+this.weights[i]*r*(axis===0?c*x-d*y:d*x+c*y);
   },0)))};
 }
}
