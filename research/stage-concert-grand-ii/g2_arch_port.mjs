// G2.04b: two physical modes with conjugate midpoint joint; output is a causal diagnostic observer, not pressure.
import {modalCoefficients} from '../stage-concert-grand/exact-modal.mjs';
export class PortMode {
 constructor({massKg,frequencyHz,dampingNsM,dt}){
  this.p=modalCoefficients({massKg,frequencyHz,dampingNsM,dt});this.x=0;this.y=0;
  this.sigma=dampingNsM/(2*massKg);this.w=Math.sqrt((2*Math.PI*frequencyHz)**2-this.sigma**2);
  if(!(this.w>0))throw RangeError('underdamped only');
  const r=Math.exp(-this.sigma*dt);this.c=r*Math.cos(this.w*dt);this.s=r*Math.sin(this.w*dt);
  this.fy=-(this.p.J+this.sigma*this.p.G)/this.w;
 }
 velocity(){return -this.sigma*this.x-this.w*this.y;}
 energy(){return .5*(this.p.massKg*this.velocity()**2+this.p.k*this.x*this.x);}
 init(x,v){this.x=x;this.y=-(v+this.sigma*x)/this.w;}
 predict(force){return this.c*this.x-this.s*this.y+this.p.G*force;}
 advance(force){const x=this.x,y=this.y;this.x=this.c*x-this.s*y+this.p.G*force;this.y=this.s*x+this.c*y+this.fy*force;}
}
export class CausalObserver {
 constructor(sr){this.a=Math.exp(-2*Math.PI*1500/sr);this.low=0;this.prev=0;this.left=0;this.right=0;}
 step(v){this.low=this.a*this.low+(1-this.a)*v;this.left=this.low;this.right=.8*this.low+.2*this.prev;this.prev=this.low;}
}
export class CoupledCore {
 constructor(sr=48000){
  if(![44100,48000,96000].includes(sr))throw RangeError('rate');this.sr=sr;this.h=1/sr;
  this.a=new PortMode({massKg:.004,frequencyHz:261.6255653,dampingNsM:.016,dt:this.h});
  this.b=new PortMode({massKg:.02,frequencyHz:280,dampingNsM:.12,dt:this.h});
  this.k=500;this.c=.08;this.alpha=this.k/2+this.c/this.h;
  this.den=1+this.alpha*(this.a.p.G+this.b.p.G);
  this.work=0;this.loss=0;this.observer=new CausalObserver(sr);
 }
 energy(){return this.a.energy()+this.b.energy()+.5*this.k*(this.a.x-this.b.x)**2;}
 step(force=0){
  const a=this.a,b=this.b,xa=a.x,xb=b.x,r0=xa-xb,e0=this.energy();
  const rf=a.predict(force)-b.predict(0);
  const f=-(this.k*(r0+rf)/2+this.c*(rf-r0)/this.h)/this.den;
  a.advance(force+f);b.advance(-f);
  const da=a.x-xa,db=b.x-xb,r1=a.x-b.x,work=force*da;
  this.work+=work;this.loss+=work+e0-this.energy();
  this.observer.step(b.velocity());
 }
 render(input,L,R){for(let i=0;i<L.length;i++){this.step(input?input[i]:0);L[i]=this.observer.left;R[i]=this.observer.right;}}
}
