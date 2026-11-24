// F7.2: offline observation of mechanical trajectory; no fluid reaction. Finite tapered source energy diagnostic.
export function captureAcceleration(hammer,board,steps){
 if(!Number.isInteger(steps)||steps<1||steps>1000000||hammer.h!==board.h)throw new RangeError('capture');
 const rate=1/board.h,trace=board.modes.map(()=>new Float64Array(steps)),v0=new Float64Array(board.v.length),initial=hammer.energy();
 let residual=0,derivativeError=0,maxIncrease=0,prev=initial,peakForce=0;
 for(let t=0;t<steps;t++){
  v0.set(board.v);const s=hammer.step(),e=hammer.energy();peakForce=Math.max(peakForce,s.sum);
  residual=Math.max(residual,Math.abs(e+hammer.lossJ+hammer.bridge.lossJ-initial));maxIncrease=Math.max(maxIncrease,e-prev);prev=e;
  for(let i=0;i<trace.length;i++){const a=(board.v[i]-v0[i])*rate;trace[i][t]=a;const m=board.modes[i],force=-hammer.bridge.lastJointForce*m.w,coeff=m.coeff;
   // Independent exact constant-force velocity integral: m=1 in mass-normalized coordinates.
   const oldX=(board.x[i]-coeff.S*v0[i]-coeff.G*force)/coeff.A;
   if(Math.abs(coeff.A)>.5)derivativeError=Math.max(derivativeError,Math.abs(a-(coeff.H*oldX+(coeff.D-1)*v0[i]+coeff.J*force)*rate));
  }
 }
 return {rate,trace,initial,residual,derivativeError,maxIncrease,peakForce,boardEnergy:board.energy(),boardLoss:board.lossJ,mechanicalLoss:hammer.lossJ+hammer.bridge.lossJ};
}

export function pressureTrace(p,modes,trace,rate,listener,options,helpers){
 const grid=helpers.radiationGrid(p,listener,options),kernels=modes.map(m=>helpers.radiationKernel(grid,(x,y)=>helpers.surfaceShape(m,x,y),rate));
 if(trace.length!==kernels.length||!trace.length||trace.some(t=>t.length!==trace[0].length))throw new RangeError('trace');
 const out=new Float64Array(trace[0].length+Math.max(...kernels.map(k=>k.offset+k.taps.length-1)));
 for(let m=0;m<kernels.length;m++){const k=kernels[m],x=trace[m];for(let j=0;j<k.taps.length;j++){const a=k.taps[j],d=k.offset+j;if(a!==0)for(let t=0;t<x.length;t++)out[t+d]+=a*x[t];}}
 return out;
}

export function sineIntegral(m,L,k){
 const J=b=>{const z=b*L/2,s=Math.abs(z)<1e-8?1-z*z/6:Math.sin(z)/z;return [L*s*Math.cos(z),L*s*Math.sin(z)];};
 const plus=J(k+m*Math.PI/L),minus=J(k-m*Math.PI/L);return [(plus[1]-minus[1])/2,(minus[0]-plus[0])/2];
}

export function bandEnergy(p,modes,trace,rate,{maxHz=2000,nt=12,np=24,rho=1.204,c=343}={}){
 const len=trace[0].length;let N=1;while(N<2*len)N*=2;
 // DFT of finite acceleration record with a cosine taper over final quarter.
 // Energy estimate is for this constructed finite source, not the full note.
 const basis=new Map();for(const mode of modes)for(const q of mode.components)basis.set(q.m+','+q.n,{m:q.m,n:q.n,re:0,im:0});
 const terms=Array.from(basis.values()),index=new Map(terms.map((q,i)=>[q.m+','+q.n,i]));
 const projections=modes.map(q=>q.components.map(c=>({i:index.get(c.m+','+c.n),w:c.coefficient})));
 const maxBin=Math.min(Math.floor(maxHz*N/rate),N/2-1),dOmega=2*Math.PI/(nt*np),scale=2/(N*rate)*rho/(4*Math.PI*Math.PI*c);
 let energy=0;
 for(let bin=0;bin<=maxBin;bin++){
  const f=bin*rate/N,k=2*Math.PI*f/c;for(const q of terms){q.re=0;q.im=0;}
  const co=new Float64Array(len),si=new Float64Array(len);
  for(let t=0;t<len;t++){const u=t/(len-1),w=u<=.75?1:.5*(1+Math.cos(Math.PI*(u-.75)/.25)),phase=2*Math.PI*bin*t/N;co[t]=w*Math.cos(phase);si[t]=-w*Math.sin(phase);}
  for(let m=0;m<modes.length;m++){let re=0,im=0;const a=trace[m];for(let t=0;t<len;t++){re+=a[t]*co[t];im+=a[t]*si[t];}for(const q of projections[m]){terms[q.i].re+=q.w*re;terms[q.i].im+=q.w*im;}}
  let intensity=0;
  const mx=Math.max(...terms.map(q=>q.m)),ny=Math.max(...terms.map(q=>q.n));
  for(let i=0;i<nt;i++){const mu=(i+.5)/nt,rad=Math.sqrt(1-mu*mu);
   for(let j=0;j<np;j++){const phi=2*Math.PI*(j+.5)/np,ax=k*rad*Math.cos(phi),ay=k*rad*Math.sin(phi),X=Array.from({length:mx+1},(_,m)=>sineIntegral(m,p.lengthM,ax)),Y=Array.from({length:ny+1},(_,n)=>sineIntegral(n,p.widthM,ay));let re=0,im=0;
    for(const q of terms){const x=X[q.m],y=Y[q.n],a=x[0]*y[0]-x[1]*y[1],b=x[0]*y[1]+x[1]*y[0];re+=q.re*a-q.im*b;im+=q.re*b+q.im*a;}intensity+=re*re+im*im;
   }
  }
  energy+=scale*dOmega*intensity*(bin===0?.5:1);
 }
 return {energyJ:energy,N,binHz:rate/N,highestHz:maxBin*rate/N,nt,np};
}
