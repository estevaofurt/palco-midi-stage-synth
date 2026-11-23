/**
 * Stage Synth — SHARED passive bridge/plate mechanical research, 2026-11-23.
 *
 * 2 transverse coordinates PER modelled string plus ONLY 2 shared board
 * coordinates. All string modes are terminated at the same moving bridge.
 *
 *   E = Σ_i (m_i*v_i² + k_i*x_i² + kc_i*(x_i-X0)²)/2
 *       + Σ_b (mb_b*Vb_b² + kb_b*Xb_b²)/2
 *       + kbb*(X0-X1)²/2
 *   dE/dt = Σ_i F_i*v_i - Σ_i c_i*v_i² - Σ_b cb_b*Vb_b².
 *
 * Implicit midpoint (passive, symmetric) yields a block arrowhead linear
 * system. Analytic elimination via Schur complement reduces each step from
 * a dense (N+2)^3 factorization / (N+2)^2 solve to O(N) operations.
 *
 * No per-sample allocations. No external samples or IRs. Normalized masses,
 * spring constants and board frequencies are still RESEARCH PLACEHOLDERS,
 * not measurements from Yamaha/Steinway. Output is generalized board VELOCITY
 * and not radiated sound pressure. Never connect to published Stage synth
 * before physical parameter identification and browser CPU/ABX validation.
 */
const TWOPI=2*Math.PI;
const hz=k=>440*2**((k-69)/12);
const valid=(v,minimum,maximum,label)=>{
 if(!Number.isFinite(v)||v<minimum||v>maximum)
   throw new RangeError('invalid '+label);
 return v;
};
export class SharedPassivePianoBridge {
 constructor({sampleRate=48000,keys=[36,43,48],coupling=.12}={}){
   valid(sampleRate,22050,192000,'sample rate');
   valid(coupling,0,1,'coupling');
   if(!Array.isArray(keys)||keys.length<1||keys.length>88||
      keys.some(k=>!Number.isInteger(k)||k<21||k>108))
     throw new RangeError('expected 1–88 valid MIDI keys');
   this.sampleRate=sampleRate;this.dt=1/sampleRate;
   this.keys=keys.slice();
   this.n=keys.length*2;
   const n=this.n;
   this.x=new Float64Array(n);this.v=new Float64Array(n);
   this.rhs=new Float64Array(n);this.mid=new Float64Array(n);
   this.mass=new Float64Array(n);this.ground=new Float64Array(n);
   this.damping=new Float64Array(n);this.coupling=new Float64Array(n);
   this.aInverse=new Float64Array(n);this.offDiagonal=new Float64Array(n);
   this.forces=new Float64Array(n);
   this.bx=new Float64Array(2);this.bv=new Float64Array(2);
   this.bmass=new Float64Array([4.2,2.3]);
   this.bdamper=new Float64Array([this.bmass[0]*24,this.bmass[1]*32]);
   this.bground=new Float64Array([
     this.bmass[0]*(TWOPI*95)**2,
     this.bmass[1]*(TWOPI*163)**2
   ]);
   this.boardSpring=.15*(TWOPI*95)**2;
   let sumK=0,sumSchur=0;
   const h=this.dt;
   for(let i=0;i<n;i++){
     const key=keys[Math.floor(i/2)],polarization=i%2;
     const f=hz(key)*(polarization===0?1:1.0009);
     const w=TWOPI*f,m=polarization?1.1:1;
     this.mass[i]=m;
     this.ground[i]=m*w*w;
     this.damping[i]=2*m*(polarization===0?.5:.14);
     const kc=coupling*m*w*w*(polarization===0?.018:.012);
     this.coupling[i]=kc;sumK+=kc;
     const a=m+.5*h*this.damping[i]+.25*h*h*(this.ground[i]+kc);
     this.aInverse[i]=1/a;
     const s=-.25*h*h*kc;
     this.offDiagonal[i]=s;
     sumSchur+=s*s/a;
   }
   const d0=this.bmass[0]+.5*h*this.bdamper[0]+
     .25*h*h*(this.bground[0]+this.boardSpring+sumK);
   const d1=this.bmass[1]+.5*h*this.bdamper[1]+
     .25*h*h*(this.bground[1]+this.boardSpring);
   const cross=-.25*h*h*this.boardSpring;
   // A string terms are diagonal; eliminating them leaves the 2x2 Schur
   // complement. SPD follows from M>0, C>=0, K>0 by construction.
   this.S00=d0-sumSchur;
   this.S01=cross;
   this.S11=d1;
   this.determinant=this.S00*this.S11-cross*cross;
   if(!(this.S00>0&&this.determinant>0&&Number.isFinite(this.determinant)))
     throw new RangeError('non-passive bridge configuration');
   this.sumK=sumK;
   this.bridgeVelocity=0;this.boardVelocity=0;
   this.externalWork=0;this.dissipated=0;
 }
 /**
  * Force array is preallocated. Set this.forces[i] before step(), clear it
  * after a hammer is released. Its scale is normalized, not Newtons.
  */
 step(){
   const h=this.dt,n=this.n,x=this.x,v=this.v,
     rhs=this.rhs,mid=this.mid,inv=this.aInverse,s=this.offDiagonal;
   const xb=this.bx,bv=this.bv,forces=this.forces;
   let rhsBoard0=this.sumK*xb[0],schurRhs=0,diss=0,work=0;
   for(let i=0;i<n;i++){
     rhsBoard0-=this.coupling[i]*x[i];
     const kx=(this.ground[i]+this.coupling[i])*x[i]-
        this.coupling[i]*xb[0];
     const ri=this.mass[i]*v[i]-.5*h*kx+.5*h*forces[i];
     rhs[i]=ri;
     schurRhs+=s[i]*ri*inv[i];
   }
   const boardSpring=this.boardSpring;
   rhsBoard0=(this.bmass[0]*bv[0]-.5*h*(rhsBoard0+
     (this.bground[0]+boardSpring)*xb[0]-boardSpring*xb[1]))-schurRhs;
   const rhsBoard1=this.bmass[1]*bv[1]-.5*h*
     ((this.bground[1]+boardSpring)*xb[1]-boardSpring*xb[0]);
   const vm0=(rhsBoard0*this.S11-this.S01*rhsBoard1)/this.determinant;
   const vm1=(this.S00*rhsBoard1-this.S01*rhsBoard0)/this.determinant;
   for(let i=0;i<n;i++){
     const vi=(rhs[i]-s[i]*vm0)*inv[i];
     mid[i]=vi;
     x[i]+=h*vi;
     v[i]=2*vi-v[i];
     diss+=this.damping[i]*vi*vi;
     work+=forces[i]*vi;
   }
   xb[0]+=h*vm0;xb[1]+=h*vm1;
   bv[0]=2*vm0-bv[0];bv[1]=2*vm1-bv[1];
   diss+=this.bdamper[0]*vm0*vm0+this.bdamper[1]*vm1*vm1;
   this.externalWork+=h*work;
   this.dissipated+=h*diss;
   this.bridgeVelocity=vm0;
   this.boardVelocity=.67*vm0+.33*vm1;
   return this.boardVelocity;
 }
 setInitialStringDisplacement(index,x){
   if(!Number.isInteger(index)||index<0||index>=this.n||
      !Number.isFinite(x))throw new RangeError('string displacement');
   this.x[index]=x;
 }
 energy(){
   let e=0,xb0=this.bx[0];
   for(let i=0;i<this.n;i++){
     const xi=this.x[i],vi=this.v[i],diff=xi-xb0;
     e+=.5*(this.mass[i]*vi*vi+this.ground[i]*xi*xi+
       this.coupling[i]*diff*diff);
   }
   for(let j=0;j<2;j++)
     e+=.5*(this.bmass[j]*this.bv[j]**2+
       this.bground[j]*this.bx[j]**2);
   e+=.5*this.boardSpring*(this.bx[0]-this.bx[1])**2;
   return e;
 }
 reset(){
   this.x.fill(0);this.v.fill(0);this.rhs.fill(0);this.mid.fill(0);
   this.bx.fill(0);this.bv.fill(0);this.forces.fill(0);
   this.bridgeVelocity=this.boardVelocity=0;
   this.externalWork=this.dissipated=0;
 }
}
