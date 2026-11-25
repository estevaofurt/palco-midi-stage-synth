// G2.04b: lossless phase fitting, passive lattice loop. Not a complete piano waveguide.
const TAU=2*Math.PI;
export const cents=(f,t)=>1200*Math.log2(f/t);
export function phaseDelay(w,N,M,a){return N*w+2*M*Math.atan2((1-a)*Math.sin(w/2),(1+a)*Math.cos(w/2));}
export function resonance(sr,N,M,a,k){
 let lo=0,hi=Math.PI;
 if(phaseDelay(hi,N,M,a)<TAU*k)throw RangeError('outside band');
 for(let i=0;i<48;i++){const w=(lo+hi)/2;if(phaseDelay(w,N,M,a)<TAU*k)lo=w;else hi=w;}
 return (lo+hi)*sr/(2*TAU);
}
export function fitDelay(sr,period,B){
 if(!Number.isInteger(period)||period<20||!(B>0)||![48000,96000].includes(sr))throw RangeError('fit');
 const w1=TAU/period,targets=Array.from({length:8},(_,i)=>{const k=i+1;return k*sr/period*Math.sqrt((1+B*k*k)/(1+B));});
 let best=null;
 for(let M=1;M<=8;M++)for(let N=1;N<period;N++){
  const phi=(TAU-N*w1)/M;
  if(phi<=0||phi>=Math.PI)continue;
  const r=Math.tan(phi/2)/Math.tan(w1/2),a=(1-r)/(1+r);
  if(Math.abs(a)>=.995)continue;
  const errors=targets.map((f,i)=>cents(resonance(sr,N,M,a,i+1),f));
  const rms=Math.sqrt(errors.reduce((s,x)=>s+x*x,0)/errors.length),max=Math.max(...errors.map(Math.abs));
  if(!best||rms<best.rms)best={sr,period,B,N,M,a,targets,errors,rms,max};
 }
 if(!best)throw Error('no stable fit');
 return best;
}
export class DispersiveDelay {
 constructor(d,sigma=2){
  if(!(Math.abs(d.a)<1)||!Number.isInteger(d.N)||d.N<1||!Number.isInteger(d.M)||d.M<1||!(Number.isFinite(sigma)&&sigma>=0))throw RangeError('delay');
  this.d=d;this.buffer=new Float64Array(d.N);this.state=new Float64Array(d.M);this.b=Math.sqrt(1-d.a*d.a);this.pos=0;this.gain=Math.exp(-sigma*d.period/d.sr);
 }
 next(input=0){
  const v=this.buffer[this.pos];let u=v;
  for(let j=0;j<this.state.length;j++){const s=this.state[j],y=this.d.a*u+this.b*s;this.state[j]=this.b*u-this.d.a*s;u=y;}
  this.buffer[this.pos]=this.gain*u+input;if(++this.pos===this.buffer.length)this.pos=0;
  return v;
 }
 norm(){let e=0;for(const x of this.buffer)e+=x*x;for(const x of this.state)e+=x*x;return e;}
}
