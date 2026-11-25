// G2.04a: comparable free-vibration core proof. Not a piano sound generator.
import {modalCoefficients} from '../stage-concert-grand/exact-modal.mjs';
export const PARTIALS=8;
export function design(sr,period,{sigma=2,B=0}={}){
 if(![48000,96000].includes(sr)||!Number.isInteger(period)||period<2*PARTIALS+1||!(sigma>=0&&Number.isFinite(sigma))||!(B>=0&&Number.isFinite(B)))throw RangeError('design');
 const f1=sr/period;
 const modes=Array.from({length:PARTIALS},(_,i)=>{
  const k=i+1,f=k*f1*Math.sqrt((1+B*k*k)/(1+B)),w=2*Math.PI*f;
  if(f>=.45*sr)throw RangeError('band');
  const amp=Math.sin(Math.PI*k*.13)/(k*k);
  const p=modalCoefficients({massKg:1,frequencyHz:Math.hypot(w,sigma)/(2*Math.PI),dampingNsM:2*sigma,dt:1/sr});
  const r=Math.exp(-sigma/sr),theta=w/sr;
  return {k,f,amp,p,c:r*Math.cos(theta),s:r*Math.sin(theta)};
 });
 return {sr,period,sigma,B,f1,modes};
}
export class ModalCore {
 constructor(d){this.d=d;this.x=new Float64Array(PARTIALS);this.y=new Float64Array(PARTIALS);}
 strike(g){if(!Number.isFinite(g))throw RangeError('strike');for(let k=0;k<PARTIALS;k++)this.x[k]+=g*this.d.modes[k].amp;}
 next(){let v=0;for(let k=0;k<PARTIALS;k++){const m=this.d.modes[k],x=this.x[k],y=this.y[k];v+=x;this.x[k]=m.c*x-m.s*y;this.y[k]=m.s*x+m.c*y;}return v;}
 norm(){let s=0;for(let k=0;k<PARTIALS;k++)s+=this.x[k]**2+this.y[k]**2;return s;}
}
export class ExactControl {
 constructor(d){this.d=d;this.x=new Float64Array(PARTIALS);this.v=new Float64Array(PARTIALS);}
 strike(g){if(!Number.isFinite(g))throw RangeError('strike');for(let k=0;k<PARTIALS;k++){const a=g*this.d.modes[k].amp;this.x[k]+=a;this.v[k]-=this.d.sigma*a;}}
 next(){let sum=0;for(let k=0;k<PARTIALS;k++){const p=this.d.modes[k].p,x=this.x[k],v=this.v[k];sum+=x;this.x[k]=p.A*x+p.S*v;this.v[k]=p.H*x+p.D*v;}return sum;}
 energy(){let e=0;for(let k=0;k<PARTIALS;k++){const p=this.d.modes[k].p;e+=.5*(this.v[k]**2+p.k*this.x[k]**2);}return e;}
}
export class DelayCore {
 constructor(d){if(d.B!==0)throw RangeError('dispersion not implemented');this.d=d;this.buf=new Float64Array(d.period);this.kernel=new Float64Array(d.period);this.pos=0;this.gain=Math.exp(-d.sigma*d.period/d.sr);
  for(let i=0;i<d.period;i++){let y=0;for(const m of d.modes)y+=m.amp*Math.cos(2*Math.PI*m.k*i/d.period);this.kernel[i]=y*Math.exp(-d.sigma*i/d.sr);}
 }
 strike(g){if(!Number.isFinite(g))throw RangeError('strike');const b=this.buf,n=b.length;let j=this.pos;for(let k=0;k<n;k++){b[j]+=g*this.kernel[k];if(++j===n)j=0;}}
 next(){const p=this.pos,v=this.buf[p];this.buf[p]=v*this.gain;if(++this.pos===this.buf.length)this.pos=0;return v;}
 norm(){let s=0;for(const x of this.buf)s+=x*x;return s;}
}
export function render(voices,out){for(let i=0;i<out.length;i++){let s=0;for(let j=0;j<voices.length;j++)s+=voices[j].next();out[i]=s;}}
