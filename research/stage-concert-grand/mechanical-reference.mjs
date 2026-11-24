// F2 offline reference solver in SI; not a real-time engine. Constant passive coefficients.
export class MechanicalReference {
  // SI: x[m], v[m/s], masses[kg], ground & edge stiffness[N/m], damping[N s/m].
  // Constant coefficients, positive ground springs optional; zero stiffness permits free mass.
  constructor({dt,mass,ground,damping,edges=[]}){
    const n=mass?.length;
    if(!Number.isFinite(dt)||dt<=0||!Number.isInteger(n)||n<1||n>256)throw new RangeError('dt or dimension');
    for(const [arr,positive] of [[mass,true],[ground,false],[damping,false]])if(!Array.isArray(arr)&&!ArrayBuffer.isView(arr)||arr.length!==n||Array.from(arr).some(v=>!Number.isFinite(v)||(positive?v<=0:v<0)))throw new RangeError('invalid coefficients');
    this.n=n;this.dt=dt;this.mass=Float64Array.from(mass);
    this.K=new Float64Array(n*n);this.C=new Float64Array(n*n);
    for(let i=0;i<n;i++){this.K[i*n+i]=ground[i];this.C[i*n+i]=damping[i];}
    for(const {i,j,k=0,c=0} of edges){
      if(!Number.isInteger(i)||!Number.isInteger(j)||i===j||i<0||j<0||i>=n||j>=n||![k,c].every(v=>Number.isFinite(v)&&v>=0))throw new RangeError('invalid passive edge');
      for(const [A,w] of [[this.K,k],[this.C,c]]){A[i*n+i]+=w;A[j*n+j]+=w;A[i*n+j]-=w;A[j*n+i]-=w;}
    }
    this.L=new Float64Array(n*n);
    for(let i=0;i<n;i++)for(let j=0;j<=i;j++){
      let a=(i===j?mass[i]:0)+dt*this.C[i*n+j]/2+dt*dt*this.K[i*n+j]/4;
      for(let k=0;k<j;k++)a-=this.L[i*n+k]*this.L[j*n+k];
      if(i===j){if(!(a>0&&Number.isFinite(a)))throw new RangeError('matrix factorization');this.L[i*n+j]=Math.sqrt(a);}
      else this.L[i*n+j]=a/this.L[j*n+j];
    }
    this.x=new Float64Array(n);this.v=new Float64Array(n);this.mid=new Float64Array(n);this.rhs=new Float64Array(n);this.z=new Float64Array(n);
    this.workJ=0;this.lossJ=0;
  }
  energy(){
    let e=0;const n=this.n;
    for(let i=0;i<n;i++){e+=.5*this.mass[i]*this.v[i]**2;for(let j=0;j<n;j++)e+=.5*this.x[i]*this.K[i*n+j]*this.x[j];}
    return e;
  }
  step(force){
    const n=this.n,h=this.dt;
    if(force!==undefined&&(force.length!==n||Array.from(force).some(v=>!Number.isFinite(v))))throw new RangeError('force vector');
    for(let i=0;i<n;i++){let kx=0;for(let j=0;j<n;j++)kx+=this.K[i*n+j]*this.x[j];this.rhs[i]=this.mass[i]*this.v[i]+h*((force?.[i]??0)-kx)/2;}
    for(let i=0;i<n;i++){let b=this.rhs[i];for(let j=0;j<i;j++)b-=this.L[i*n+j]*this.z[j];this.z[i]=b/this.L[i*n+i];}
    for(let i=n-1;i>=0;i--){let b=this.z[i];for(let j=i+1;j<n;j++)b-=this.L[j*n+i]*this.mid[j];this.mid[i]=b/this.L[i*n+i];}
    let w=0,d=0;
    for(let i=0;i<n;i++){const v=this.mid[i];this.x[i]+=h*v;this.v[i]=2*v-this.v[i];w+=(force?.[i]??0)*v;for(let j=0;j<n;j++)d+=v*this.C[i*n+j]*this.mid[j];}
    this.workJ+=h*w;this.lossJ+=h*d;
  }
}
export function midpointFrequency(fHz,rate,substeps=1){
  if(!Number.isFinite(fHz)||fHz<=0||!Number.isFinite(rate)||rate<=0||!Number.isInteger(substeps)||substeps<1)throw new RangeError('frequency/rate/substeps');
  const effectiveRate=rate*substeps;
  return effectiveRate/Math.PI*Math.atan(Math.PI*fHz/effectiveRate);
}

export function phaseBudget(fHz,rate,maxCents=1){
  if(!Number.isFinite(maxCents)||maxCents<=0)throw new RangeError('tolerance');
  const cents=s=>1200*Math.log2(midpointFrequency(fHz,rate,s)/fHz);
  let high=1;while(-cents(high)>maxCents){high*=2;if(high>1048576)throw new RangeError('substep limit');}
  let low=1;while(low<high){const m=Math.floor((low+high)/2);if(-cents(m)<=maxCents)high=m;else low=m+1;}
  return {fHz,rate,unsubsteppedCents:cents(1),minSubsteps:low,substeppedCents:cents(low)};
}
