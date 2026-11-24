// F7.3: positive resistive narrow-band surrogate, not full causal radiation impedance.
import {BoardPort} from './board-coupling.mjs';
import {sineIntegral} from './vibroacoustic-observer.mjs';
export function radiationResistance(p,modes,f,{nt=12,np=24,rho=1.204,c=343}={}){
 if(!Number.isFinite(f)||f<=0||![nt,np].every(v=>Number.isInteger(v)&&v>0&&v<=128)||![rho,c].every(v=>Number.isFinite(v)&&v>0)||!modes.length)throw new RangeError('radiation resistance');
 const N=modes.length,R=Array.from({length:N},()=>Array(N).fill(0)),w=2*Math.PI*f,k=w/c,scale=rho*w*w/(4*Math.PI*Math.PI*c)*2*Math.PI/(nt*np);
 const mx=Math.max(...modes.flatMap(m=>m.components.map(q=>q.m))),ny=Math.max(...modes.flatMap(m=>m.components.map(q=>q.n)));
 for(let i=0;i<nt;i++)for(let j=0;j<np;j++){
  const mu=(i+.5)/nt,s=Math.sqrt(1-mu*mu),phi=2*Math.PI*(j+.5)/np;
  const X=Array.from({length:mx+1},(_,m)=>sineIntegral(m,p.lengthM,k*s*Math.cos(phi))),Y=Array.from({length:ny+1},(_,n)=>sineIntegral(n,p.widthM,k*s*Math.sin(phi)));
  const z=modes.map(m=>{let re=0,im=0;for(const q of m.components){const a=X[q.m],b=Y[q.n];re+=q.coefficient*(a[0]*b[0]-a[1]*b[1]);im+=q.coefficient*(a[0]*b[1]+a[1]*b[0]);}return [re,im];});
  for(let a=0;a<N;a++)for(let b=0;b<=a;b++)R[a][b]+=scale*(z[a][0]*z[b][0]+z[a][1]*z[b][1]);
 }
 for(let a=0;a<N;a++)for(let b=0;b<a;b++)R[b][a]=R[a][b];return R;
}

export function radiationBlocks(p,modes,{bandsPerOctave=6,scale=1,...opts}={}){
 if(!Number.isInteger(bandsPerOctave)||bandsPerOctave<1||bandsPerOctave>24||!Number.isFinite(scale)||scale<0)throw new RangeError('blocks');
 const groups=new Map();modes.forEach((m,i)=>{const b=Math.floor(bandsPerOctave*Math.log2(m.frequencyHz/100));if(!groups.has(b))groups.set(b,[]);groups.get(b).push(i);});
 return Array.from(groups,([b,indices])=>{const f=100*2**((b+.5)/bandsPerOctave);return {indices,f,R:radiationResistance(p,indices.map(i=>modes[i]),f,opts).map(row=>row.map(v=>v*scale))};});
}

export function cholesky(A){
 const L=A.map(row=>row.map(()=>0));for(let i=0;i<A.length;i++)for(let j=0;j<=i;j++){let x=A[i][j];for(let k=0;k<j;k++)x-=L[i][k]*L[j][k];if(i===j){if(!(x>0))throw Error('nonpositive step matrix');L[i][j]=Math.sqrt(x);}else L[i][j]=x/L[j][j];}return L;
}

export function solveCholesky(L,b){
 const x=b.slice();for(let i=0;i<x.length;i++){for(let j=0;j<i;j++)x[i]-=L[i][j]*x[j];x[i]/=L[i][i];}
 for(let i=x.length-1;i>=0;i--){for(let j=i+1;j<x.length;j++)x[i]-=L[j][i]*x[j];x[i]/=L[i][i];}return x;
}

export class ResistiveBoard extends BoardPort{
 constructor(p,modes,patch,h,options={},helpers){
  const {radiation={},...structural}=options;super(p,modes,patch,h,structural,helpers);
  this.blocks=radiationBlocks(p,modes,radiation).map(b=>{const g=b.indices.map(i=>Math.sqrt(this.modes[i].coeff.G));const L=cholesky(b.R.map((row,i)=>row.map((v,j)=>+(i===j)+g[i]*v*g[j]/h)));return {...b,g,L};});
  this.radiationLossJ=0;this.structuralLossJ=0;this.lastModalForce=new Float64Array(modes.length);
  const response=this.increment(1,true);this.G=this.modes.reduce((s,m,i)=>s+m.w*response[i],0);
 }
 increment(force,responseOnly=false){
  const dx=new Float64Array(this.modes.length);
  for(const b of this.blocks){const rhs=b.indices.map((i,j)=>{const m=this.modes[i],q=m.coeff;return ((responseOnly?0:(q.A-1)*this.x[i]+q.S*this.v[i])+q.G*m.w*force)/b.g[j];});const y=solveCholesky(b.L,rhs);b.indices.forEach((i,j)=>dx[i]=b.g[j]*y[j]);}return dx;
 }
 free(){const dx=this.increment(0);return this.position()+this.modes.reduce((s,m,i)=>s+m.w*dx[i],0);}
 step(force){
  if(!Number.isFinite(force))throw new RangeError('force');
  const dx=this.increment(force),h=this.h;let rad=0,local=0,work=0;
  for(const b of this.blocks)for(let j=0;j<b.indices.length;j++){
   const i=b.indices[j],m=this.modes[i],q=m.coeff,x=this.x[i],v=this.v[i],rf=-b.R[j].reduce((s,a,k)=>s+a*dx[b.indices[k]]/h,0),f=m.w*force+rf,xn=q.A*x+q.S*v+q.G*f,vn=q.H*x+q.D*v+q.J*f;
   rad-=rf*(xn-x);local+=f*(xn-x)+.5*(v*v-vn*vn+m.lambda*(x*x-xn*xn));work+=m.w*force*(xn-x);this.x[i]=xn;this.v[i]=vn;this.lastModalForce[i]=f;
  }
  this.radiationLossJ+=rad;this.structuralLossJ+=local;this.lossJ+=rad+local;this.workJ+=work;
 }
}
