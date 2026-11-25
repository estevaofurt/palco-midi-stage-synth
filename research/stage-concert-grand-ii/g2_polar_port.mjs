// G2.08b: reciprocal two-axis dissipative port, fixed-support modes.
// Diagnostic internal force at 0.95L, NOT moving boundary or soundboard.
import {StringPilot} from './g2_string_pilot.mjs';
import {spatialWeight} from '../stage-concert-grand/stiff-string.mjs';
export const LOADS=Object.freeze({
 open:Object.freeze({strong:0,weak:0,angle:0}),
 aligned:Object.freeze({strong:.5,weak:.02,angle:0}),
 rotated:Object.freeze({strong:.5,weak:.02,angle:.5})
});
export class PolarPort {
 constructor(group,loss,{strong,weak,angle}){
  if(![strong,weak,angle].every(Number.isFinite)||strong<0||weak<0)throw RangeError('passive load');
  this.sr=group.strings[0].sr;this.h=1/this.sr;
  if(group.strings.some(s=>s.sr!==this.sr))throw RangeError('rate mismatch');
  this.axes=[0,1].map(axis=>group.strings.map(s=>{
   const q=new StringPilot(s.wire.midi,s.sr,{cutoffHz:s.cutoffHz,cents:s.cents,strikeFraction:s.strikeFraction,widthM:s.widthM,...loss});
   if(q.modes.length!==s.modes.length)throw Error('mode count');
   if(axis===0)for(let i=0;i<q.modes.length;i++)q.modes[i].init(s.modes[i].x,s.modes[i].velocity());
   return {s:q,w:q.info.map(m=>spatialWeight(m,q.wire.lengthM,.95*q.wire.lengthM,0))};
  }));
  const c=Math.cos(angle),s=Math.sin(angle);
  this.D=[strong*c*c+weak*s*s,(strong-weak)*c*s,strong*s*s+weak*c*c];
  this.H=this.axes.map(axis=>axis.reduce((sum,q)=>sum+q.s.modes.reduce((z,m,i)=>z+q.w[i]**2*m.p.G,0),0));
  this.localLossJ=0;this.loadLossJ=0;this.stepLocalJ=0;this.stepLoadJ=0;this.maxPortResidualN=0;
  this.F=new Float64Array(2);this.delta=new Float64Array(2);
 }
 axisEnergy(a){return this.axes[a].reduce((s,q)=>s+q.s.energy(),0);}
 energy(){return this.axisEnergy(0)+this.axisEnergy(1);}
 position(a){let x=0;for(const q of this.axes[a])for(let i=0;i<q.w.length;i++)x+=q.w[i]*q.s.modes[i].x;return x;}
 step(){
  const h=this.h,[d00,d01,d11]=this.D,[H0,H1]=this.H,x0=this.position(0),x1=this.position(1),E0=this.energy();
  const free=this.axes.map(axis=>axis.reduce((sum,q)=>sum+q.s.modes.reduce((z,m,i)=>z+q.w[i]*(m.predict(0)-m.x),0),0));
  const a=1+d00*H0/h,b=d01*H1/h,c=d01*H0/h,d=1+d11*H1/h,det=a*d-b*c;
  const r0=-(d00*free[0]+d01*free[1])/h,r1=-(d01*free[0]+d11*free[1])/h;
  const F0=(d*r0-b*r1)/det,F1=(a*r1-c*r0)/det;
  this.F[0]=F0;this.F[1]=F1;
  let local=0;
  for(let j=0;j<2;j++)for(const q of this.axes[j])for(let i=0;i<q.w.length;i++){
   const m=q.s.modes[i],x=m.x,e=m.energy(),force=this.F[j]*q.w[i];m.advance(force);local+=force*(m.x-x)+e-m.energy();
  }
  const dx=this.position(0)-x0,dy=this.position(1)-x1;
  this.delta[0]=dx;this.delta[1]=dy;
  const load=(d00*dx*dx+2*d01*dx*dy+d11*dy*dy)/h;
  this.stepLocalJ=local;this.stepLoadJ=load;this.localLossJ+=local;this.loadLossJ+=load;
  this.maxPortResidualN=Math.max(this.maxPortResidualN,Math.abs(F0+(d00*dx+d01*dy)/h),Math.abs(F1+(d01*dx+d11*dy)/h));
  return E0-this.energy()-load-local;
 }
}
