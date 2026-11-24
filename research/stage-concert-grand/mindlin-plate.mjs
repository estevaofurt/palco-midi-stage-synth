// F6.4: Mindlin plate with centered Timoshenko line ribs, restricted simply supported Navier subspace. SI, research only.
export function mindlinModes(p,ribs,{basisHz=1000,GxzPa=.65e9,GyzPa=.06e9,shearFactor=5/6,ribShearPa=.65e9,rotaryScale=1,shearScale=1}={},helpers){
 if(![GxzPa,GyzPa,shearFactor,ribShearPa,rotaryScale,shearScale].every(v=>Number.isFinite(v)&&v>0))throw new RangeError('Mindlin parameters');
 const base=helpers.plateModes(p,basisHz),groups=new Map(),out=[];
 for(const q of base){if(!groups.has(q.n))groups.set(q.n,[]);groups.get(q.n).push(q);}
 const A=p.areaM2/4,h=p.thicknessM,Sx=shearScale*shearFactor*GxzPa*h,Sy=shearScale*shearFactor*GyzPa*h;
 let residual=0,orthogonality=0;
 for(const [n,modes] of groups){
   const N=modes.length,D=3*N;if(D>192)throw new RangeError('block size');
   const M=Array.from({length:D},()=>Array(D).fill(0)),K=M.map(row=>row.slice());
   for(let i=0;i<N;i++){
     const q=modes[i],x=q.kx,y=q.ky,j=3*i;
     M[j][j]=A*p.arealMass;M[j+1][j+1]=M[j+2][j+2]=A*p.arealMass*h*h/12*rotaryScale;
     K[j][j]=A*(Sx*x*x+Sy*y*y);K[j][j+1]=K[j+1][j]=-A*Sx*x;K[j][j+2]=K[j+2][j]=-A*Sy*y;
     K[j+1][j+1]=A*(p.D11*x*x+p.D66*y*y+Sx);K[j+2][j+2]=A*(p.D22*y*y+p.D66*x*x+Sy);K[j+1][j+2]=K[j+2][j+1]=A*(p.D12+p.D66)*x*y;
   }
   for(const rib of ribs){
     const b=modes.map(q=>Math.sin(q.kx*rib.xM)),y=modes[0].ky,L=p.widthM/2,mu=rib.massPerM,I=rib.widthM*rib.heightM**3/12,rot=rib.densityKgM3*I*rotaryScale,ks=shearScale*shearFactor*ribShearPa*rib.widthM*rib.heightM;
     for(let i=0;i<N;i++)for(let j=0;j<N;j++){
       const v=L*b[i]*b[j],ii=3*i,jj=3*j;
       M[ii][jj]+=mu*v;M[ii+2][jj+2]+=rot*v;
       K[ii][jj]+=ks*y*y*v;K[ii][jj+2]-=ks*y*v;K[ii+2][jj]-=ks*y*v;K[ii+2][jj+2]+=(rib.EI*y*y+ks)*v;
     }
   }
   const eig=helpers.generalizedEigen(M,K),mv=(A,v)=>A.map(row=>row.reduce((s,x,j)=>s+x*v[j],0));
   for(const e of eig){
     const u=mv(M,e.vector),v=mv(K,e.vector);
     residual=Math.max(residual,Math.hypot(...v.map((x,j)=>x-e.lambda*u[j]))/(Math.hypot(...v)+e.lambda*Math.hypot(...u)));
     for(const f of eig)orthogonality=Math.max(orthogonality,Math.abs(f.vector.reduce((s,x,j)=>s+x*u[j],0)-(e===f?1:0)));
     out.push({n,lambda:e.lambda,frequencyHz:Math.sqrt(e.lambda)/(2*Math.PI),components:modes.map((q,i)=>({m:q.m,n:q.n,kx:q.kx,ky:q.ky,coefficient:e.vector[3*i],rotationX:e.vector[3*i+1],rotationY:e.vector[3*i+2]}))});
   }
 }
 return {modes:out.sort((a,b)=>a.frequencyHz-b.frequencyHz),basisCount:base.length,residual,orthogonality};
}
