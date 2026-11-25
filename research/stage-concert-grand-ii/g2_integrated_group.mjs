// G2.08c: simultaneous nonlinear shared hammer and reciprocal dissipative port.
// Fixed-support string modes with an internal load; NOT a moving bridge or radiation.
import {GroupHammer} from './g2_group_hammer.mjs';
import {PolarPort,LOADS} from './g2_polar_port.mjs';
import {LOSS_CASES} from './g2_decay.mjs';
import {feltPotential,feltSecant,solveContact} from '../stage-concert-grand/hammer-contact.mjs';
export class IntegratedGroup {
 constructor(key,sr=48000,{speedMps=1,spreadCents=.5,loss=LOSS_CASES.control,load=LOADS.rotated,cutoffHz}={}){
  const g=new GroupHammer(key,sr,{speedMps,spreadCents,...(cutoffHz===undefined?{}:{cutoffHz})});
  this.port=new PolarPort(g,loss,load);this.h=1/sr;this.x=g.x;this.v=g.v;this.params=g.params;this.k=g.k;
  this.vertical=this.port.axes[0];this.force=new Float64Array(g.strings.length);
  const h=this.h,[d00,d01,d11]=this.port.D,[H0,H1]=this.port.H;
  const a=1+d00*H0/h,b=d01*H1/h,c=d01*H0/h,d=1+d11*H1/h,det=a*d-b*c;
  if(!(det>0))throw Error('port inverse');
  this.R=[(d*d00-b*d01)/(det*h),(d*d01-b*d11)/(det*h),(a*d11-c*d01)/(det*h)];
  this.cross=this.vertical.map(q=>q.s.modes.reduce((z,m,i)=>z+q.w[i]*q.s.weights[i]*m.p.G,0));
  const hm=h*h/(2*this.params.massKg);
  this.C=this.vertical.map((q,i)=>this.vertical.map((_,j)=>hm+(i===j?q.s.modes.reduce((z,m,k)=>z+q.s.weights[k]**2*m.p.G,0):0)-this.cross[i]*this.R[0]*this.cross[j]));
  // Check positive definiteness of effective contact compliance (Schur complement).
  const L=this.C.map(r=>r.map(()=>0));
  for(let i=0;i<L.length;i++)for(let j=0;j<=i;j++){
   let v=this.C[i][j];for(let k=0;k<j;k++)v-=L[i][k]*L[j][k];
   if(i===j){if(!(v>0))throw Error('contact compliance');L[i][j]=Math.sqrt(v);}else L[i][j]=v/L[j][j];
  }
  this.feltLossJ=0;this.localLossJ=0;this.loadLossJ=0;this.impulseNs=0;
  this.stepFeltJ=0;this.stepLocalJ=0;this.stepLoadJ=0;this.residualN=0;this.portResidualN=0;this.sweeps=0;
 }
 compression(i){return this.x-this.vertical[i].s.displacement();}
 energy(){return .5*this.params.massKg*this.v**2+this.port.energy()+this.vertical.reduce((z,_,i)=>z+feltPotential(this.compression(i),this.k,this.params.power),0);}
 step(){
  const h=this.h,{massKg:m,power:p,rateFactorSPerM:eta}=this.params,k=this.k,hm=h*h/(2*m),n=this.force.length;
  const [R00,R01,R11]=this.R,[d00,d01,d11]=this.port.D;
  const old=[this.port.position(0),this.port.position(1)],d0=this.vertical.map((_,i)=>this.compression(i));
  const free=this.port.axes.map(axis=>axis.reduce((z,q)=>z+q.s.modes.reduce((u,mode,i)=>u+q.w[i]*(mode.predict(0)-mode.x),0),0));
  const P0=-R00*free[0]-R01*free[1];
  const cf=this.vertical.map((q,i)=>this.x+h*this.v-q.s.modes.reduce((z,mode,j)=>z+q.s.weights[j]*mode.predict(0),0)-this.cross[i]*P0);
  const law=(i,d)=>feltSecant(d0[i],d,k,p)*Math.max(0,1+eta*(d-d0[i])/h);
  const residual=()=>{let r=0;for(let i=0;i<n;i++){const d=cf[i]-this.C[i].reduce((z,c,j)=>z+c*this.force[j],0);r=Math.max(r,Math.abs(this.force[i]-law(i,d)));}return r;};
  this.force.fill(0);this.sweeps=0;
  if(!cf.every((d,i)=>law(i,d)===0)){
   let converged=false;
   for(let sweep=0;sweep<128;sweep++){
    for(let i=0;i<n;i++){
     const f=cf[i]-this.C[i].reduce((z,c,j)=>z+(i===j?0:c*this.force[j]),0);
     this.force[i]=solveContact(d0[i],f,this.C[i][i],h,k,p,eta);
    }
    this.sweeps=sweep+1;
    if(residual()<1e-9){converged=true;break;}
   }
   if(!converged)throw Error('integrated contact residual');
  }
  const sum=this.force.reduce((a,b)=>a+b,0),extra=this.cross.reduce((z,c,i)=>z+c*this.force[i],0);
  const F=[-R00*(free[0]+extra)-R01*free[1],-R01*(free[0]+extra)-R11*free[1]];
  this.x+=h*this.v-hm*sum;this.v-=h*sum/m;
  let local=0;
  for(let a=0;a<2;a++)for(let j=0;j<n;j++){
   const q=this.port.axes[a][j];
   for(let i=0;i<q.w.length;i++){
    const mode=q.s.modes[i],x=mode.x,E=mode.energy(),f=q.w[i]*F[a]+(a===0?q.s.weights[i]*this.force[j]:0);
    mode.advance(f);local+=f*(mode.x-x)+E-mode.energy();
   }
  }
  const dx=this.port.position(0)-old[0],dy=this.port.position(1)-old[1];
  const load=(d00*dx*dx+2*d01*dx*dy+d11*dy*dy)/h;
  this.portResidualN=Math.max(Math.abs(F[0]+(d00*dx+d01*dy)/h),Math.abs(F[1]+(d01*dx+d11*dy)/h));
  let felt=0,res=0;
  for(let i=0;i<n;i++){const d1=this.compression(i);felt+=this.force[i]*(d1-d0[i])-(feltPotential(d1,k,p)-feltPotential(d0[i],k,p));res=Math.max(res,Math.abs(this.force[i]-law(i,d1)));}
  this.residualN=res;this.stepFeltJ=felt;this.stepLocalJ=local;this.stepLoadJ=load;
  this.feltLossJ+=felt;this.localLossJ+=local;this.loadLossJ+=load;this.impulseNs+=h*sum;
 }
}
