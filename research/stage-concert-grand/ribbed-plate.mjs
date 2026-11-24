// F6.2: centered full-span Euler-Bernoulli line ribs in a simply supported plate Ritz basis. No eccentric composite or torsion.
export function ribDesign(p,{xM,widthM=.022,heightM=.025,densityKgM3=430,youngPa=11e9}){
  if(![xM,widthM,heightM,densityKgM3,youngPa].every(Number.isFinite)||xM-widthM/2<=0||xM+widthM/2>=p.lengthM||![widthM,heightM,densityKgM3,youngPa].every(v=>v>0))throw new RangeError('rib');
  const area=widthM*heightM,inertia=widthM*heightM**3/12;
  return {xM,widthM,heightM,densityKgM3,youngPa,massPerM:area*densityKgM3,EI:youngPa*inertia,massKg:area*densityKgM3*p.widthM};
}

export function symmetricEigen(A){
  const n=A.length,B=A.map(row=>row.slice()),V=Array.from({length:n},(_,i)=>Array.from({length:n},(_,j)=>+(i===j)));
  const scale=Math.max(...B.map((row,i)=>Math.abs(row[i])));let converged=false;
  for(let sweep=0;sweep<100;sweep++){
    let max=0;
    for(let i=0;i<n;i++)for(let j=i+1;j<n;j++){
      const b=B[i][j];max=Math.max(max,Math.abs(b));if(Math.abs(b)<=scale*1e-14)continue;
      const tau=(B[j][j]-B[i][i])/(2*b),t=(tau>=0?1:-1)/(Math.abs(tau)+Math.hypot(1,tau)),c=1/Math.hypot(1,t),s=t*c;
      const a=B[i][i],d=B[j][j];B[i][i]=a-t*b;B[j][j]=d+t*b;B[i][j]=B[j][i]=0;
      for(let k=0;k<n;k++){if(k!==i&&k!==j){const x=B[k][i],y=B[k][j];B[k][i]=B[i][k]=c*x-s*y;B[k][j]=B[j][k]=s*x+c*y;}const x=V[k][i],y=V[k][j];V[k][i]=c*x-s*y;V[k][j]=s*x+c*y;}
    }
    if(max<=scale*1e-13){converged=true;break;}
  }
  if(!converged)throw Error('Jacobi convergence');
  return B.map((row,i)=>({lambda:row[i],vector:V.map(v=>v[i])})).sort((a,b)=>a.lambda-b.lambda);
}

export function generalizedEigen(M,K){
  const n=M.length,L=Array.from({length:n},()=>Array(n).fill(0)),W=L.map(r=>r.slice());
  for(let i=0;i<n;i++)for(let j=0;j<=i;j++){let a=M[i][j];for(let k=0;k<j;k++)a-=L[i][k]*L[j][k];if(i===j){if(!(a>0))throw Error('mass not SPD');L[i][j]=Math.sqrt(a);}else L[i][j]=a/L[j][j];}
  for(let i=0;i<n;i++)for(let j=0;j<=i;j++){let a=+(i===j);for(let k=j;k<i;k++)a-=L[i][k]*W[k][j];W[i][j]=a/L[i][i];}
  const T=W.map(row=>K[0].map((_,j)=>row.reduce((s,v,k)=>s+v*K[k][j],0)));
  const A=T.map(row=>W.map(w=>row.reduce((s,v,k)=>s+v*w[k],0)));
  for(let i=0;i<n;i++)for(let j=i+1;j<n;j++)A[i][j]=A[j][i]=(A[i][j]+A[j][i])/2;
  return symmetricEigen(A).map(({lambda,vector})=>{if(!(lambda>0))throw Error('nonpositive eigenvalue');return {lambda,vector:W.map((_,i)=>W.reduce((s,row,j)=>s+row[i]*vector[j],0))};});
}

export function ribbedModes(p,ribs,{basisHz=1000,massScale=1,stiffnessScale=1}={},helpers){
  if(![massScale,stiffnessScale].every(v=>Number.isFinite(v)&&v>=0))throw new RangeError('scale');
  const modes=helpers.plateModes(p,basisHz),groups=new Map(),out=[];
  for(const q of modes){if(!groups.has(q.n))groups.set(q.n,[]);groups.get(q.n).push(q);}
  let maxResidual=0,maxOrthogonality=0;
  for(const [n,base] of groups){
    const N=base.length;if(N>128)throw new RangeError('block size');
    const M=base.map((q,i)=>base.map((_,j)=>i===j?q.massKg:0)),K=base.map((q,i)=>base.map((_,j)=>i===j?q.stiffnessNPerM:0));
    for(const rib of ribs){
      const b=base.map(q=>Math.sin(q.kx*rib.xM)),mass=massScale*rib.massPerM*p.widthM/2,k=stiffnessScale*rib.EI*p.widthM/2*base[0].ky**4;
      for(let i=0;i<N;i++)for(let j=0;j<N;j++){M[i][j]+=mass*b[i]*b[j];K[i][j]+=k*b[i]*b[j];}
    }
    const eig=generalizedEigen(M,K);
    const mv=(A,v)=>A.map(row=>row.reduce((s,x,j)=>s+x*v[j],0)),dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
    for(let i=0;i<N;i++){
      const q=eig[i],u=mv(M,q.vector),v=mv(K,q.vector),norm=Math.hypot(...v)+q.lambda*Math.hypot(...u);
      maxResidual=Math.max(maxResidual,Math.hypot(...v.map((x,j)=>x-q.lambda*u[j]))/norm);
      for(let j=0;j<N;j++)maxOrthogonality=Math.max(maxOrthogonality,Math.abs(dot(eig[j].vector,u)-+(i===j)));
      out.push({n,frequencyHz:Math.sqrt(q.lambda)/(2*Math.PI),lambda:q.lambda,components:base.map((b,j)=>({m:b.m,n:b.n,kx:b.kx,ky:b.ky,coefficient:q.vector[j]}))});
    }
  }
  return {modes:out.sort((a,b)=>a.frequencyHz-b.frequencyHz),basisCount:modes.length,maxResidual,maxOrthogonality,ribMassKg:ribs.reduce((s,q)=>s+q.massKg*massScale,0)};
}

export function ribbedPatchWeight(p,mode,patch,weightFn){return mode.components.reduce((s,q)=>s+q.coefficient*weightFn(p,q,patch),0);}
