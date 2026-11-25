// R9: continuous-frequency approximation to the existing passive board.
 // Unit sinusoidal force on a conjugate port; strings and hammer excluded.
export function solveReal(A,b){
 const n=b.length,M=A.map((r,i)=>[...r,b[i]]);
 for(let i=0;i<n;i++){
  let p=i;for(let j=i+1;j<n;j++)if(Math.abs(M[j][i])>Math.abs(M[p][i]))p=j;
  if(!(Math.abs(M[p][i])>1e-20))throw Error('singular transfer matrix');
  [M[i],M[p]]=[M[p],M[i]];
  for(let j=i+1;j<n;j++){const f=M[j][i]/M[i][i];for(let k=i;k<=n;k++)M[j][k]-=f*M[i][k];}
 }
 const x=Array(n).fill(0);
 for(let i=n-1;i>=0;i--){let t=M[i][n];for(let j=i+1;j<n;j++)t-=M[i][j]*x[j];x[i]=t/M[i][i];}
 if(!x.every(Number.isFinite))throw Error('nonfinite transfer');return x;
}
export function boardResponse(board,weights,f,kernels,response){
 if(!(f>0&&Number.isFinite(f))||weights.length!==board.modes.length)throw RangeError('transfer');
 const w=2*Math.PI*f,qr=new Float64Array(weights.length),qi=new Float64Array(weights.length);
 for(const block of board.blocks){
  const ids=block.indices,n=ids.length,A=Array.from({length:2*n},()=>Array(2*n).fill(0));
  for(let i=0;i<n;i++)for(let j=0;j<n;j++){
   const q=board.modes[ids[i]].coeff;
   const re=i===j?q.k-q.massKg*w*w:0,im=w*(block.R[i][j]+(i===j?q.dampingNsM:0));
   A[i][j]=A[i+n][j+n]=re;A[i][j+n]=-im;A[i+n][j]=im;
  }
  const x=solveReal(A,[...ids.map(i=>weights[i]),...ids.map(()=>0)]);
  ids.forEach((id,i)=>{qr[id]=x[i];qi[id]=x[i+n];});
 }
 let vr=0,vi=0;
 for(let i=0;i<weights.length;i++){vr-=w*weights[i]*qi[i];vi+=w*weights[i]*qr[i];}
 if(vr< -1e-10*Math.max(1,Math.hypot(vr,vi)))throw Error('negative mobility');
 const pressure=kernels.map(ks=>{
  let re=0,im=0;
  for(let i=0;i<weights.length;i++){const h=response(ks[i],f);re-=w*w*(qr[i]*h.re-qi[i]*h.im);im-=w*w*(qr[i]*h.im+qi[i]*h.re);}
  return {re,im,magnitude:Math.hypot(re,im)};
 });
 return {f,mobility:{re:vr,im:vi,magnitude:Math.hypot(vr,vi)},pressure,stereoMagnitude:Math.sqrt(pressure.reduce((s,p)=>s+p.magnitude**2,0)/pressure.length)};
}
