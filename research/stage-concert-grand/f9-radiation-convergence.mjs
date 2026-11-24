// F9.11: continuous linear harmonic diagnostic of the existing passive network.
// Not the discrete time-step transfer function, not a measured Yamaha FRF.
const add=([a,b],[c,d])=>[a+c,b+d],sub=([a,b],[c,d])=>[a-c,b-d],mul=([a,b],[c,d])=>[a*c-b*d,a*d+b*c],abs=([a,b])=>Math.hypot(a,b);
const div=([a,b],[c,d])=>{const n=c*c+d*d;if(!(n>0&&Number.isFinite(n)))throw RangeError('singular complex division');return [(a*c+b*d)/n,(b*c-a*d)/n];};
function solve(A,b){
 const n=b.length,M=A.map(r=>r.map(z=>z.slice())),v=b.map(z=>z.slice());
 for(let k=0;k<n;k++){
  let p=k;for(let j=k+1;j<n;j++)if(abs(M[j][k])>abs(M[p][k]))p=j;
  if(!(abs(M[p][k])>0))throw Error('singular block');
  [M[k],M[p]]=[M[p],M[k]];[v[k],v[p]]=[v[p],v[k]];
  for(let i=k+1;i<n;i++){const q=div(M[i][k],M[k][k]);for(let j=k+1;j<n;j++)M[i][j]=sub(M[i][j],mul(q,M[k][j]));v[i]=sub(v[i],mul(q,v[k]));M[i][k]=[0,0];}
 }
 const x=Array(n);for(let i=n-1;i>=0;i--){let q=v[i];for(let j=i+1;j<n;j++)q=sub(q,mul(M[i][j],x[j]));x[i]=div(q,M[i][i]);}return x;
}
export function modalBoardResponse(board,f){
 if(!Number.isFinite(f)||f<=0)throw RangeError('frequency');
 const w=2*Math.PI*f;const acceleration=Array(board.modes.length);let Y=[0,0],structuralW=0,radiationW=0,maxRelativeResidual=0;
 for(const b of board.blocks){
  const modes=b.indices.map(i=>board.modes[i]),N=modes.length;
  const A=modes.map((m,i)=>modes.map((_,j)=>[i===j?m.lambda-w*w:0,w*(b.R[i][j]+(i===j?m.coeff.dampingNsM:0))]));
  const F=modes.map(m=>[m.w,0]),x=solve(A,F),v=x.map(z=>mul([0,w],z));
  for(let i=0;i<N;i++){
   acceleration[b.indices[i]]=mul([-w*w,0],x[i]);Y=add(Y,mul([modes[i].w,0],v[i]));structuralW+=.5*modes[i].coeff.dampingNsM*abs(v[i])**2;
   let rv=[0,0],ax=[0,0],scale=abs(F[i]);for(let j=0;j<N;j++){rv=add(rv,mul([b.R[i][j],0],v[j]));const t=mul(A[i][j],x[j]);ax=add(ax,t);scale+=abs(t);}
   radiationW+=.5*(v[i][0]*rv[0]+v[i][1]*rv[1]);maxRelativeResidual=Math.max(maxRelativeResidual,abs(sub(ax,F[i]))/Math.max(scale,1e-300));
  }
 }
 const inputW=.5*Y[0];return {f,Y,acceleration,structuralW,radiationW,inputW,powerResidualW:inputW-structuralW-radiationW,maxRelativeResidual};
}

// Aggregate the complex acceleration field in the existing Navier basis.
// Separate the x and y sums; memoize rows for each regular radiation grid.
export function complexSurface(modes,acceleration){
 if(modes.length!==acceleration.length||!modes.length||acceleration.some(z=>!Array.isArray(z)||z.length!==2||!z.every(Number.isFinite)))throw RangeError('modal field');
 const terms=new Map(),kx=new Map(),ky=new Map();
 modes.forEach((m,i)=>{for(const q of m.components){
  if(kx.has(q.m)&&kx.get(q.m)!==q.kx||ky.has(q.n)&&ky.get(q.n)!==q.ky)throw Error('incompatible basis');
  kx.set(q.m,q.kx);ky.set(q.n,q.ky);
  const key=q.m+':'+q.n,old=terms.get(key)??{m:q.m,n:q.n,z:[0,0]};
  old.z=add(old.z,mul([q.coefficient,0],acceleration[i]));terms.set(key,old);
 }});
 const ns=[...ky.keys()],rows=new Map(),ys=new Map(),entries=[...terms.values()];
 return (x,y)=>{
  if(!rows.has(x)){
   const sx=new Map([...kx].map(([m,k])=>[m,Math.sin(k*x)])),row=new Map(ns.map(n=>[n,[0,0]]));
   for(const q of entries)row.set(q.n,add(row.get(q.n),mul([sx.get(q.m),0],q.z)));
   rows.set(x,ns.map(n=>row.get(n)));
  }
  if(!ys.has(y))ys.set(y,ns.map(n=>Math.sin(ky.get(n)*y)));
  const row=rows.get(x),sy=ys.get(y);let re=0,im=0;for(let i=0;i<ns.length;i++){re+=row[i][0]*sy[i];im+=row[i][1]*sy[i];}return [re,im];
 };
}
export function pressureResponse(grid,field,f,rate=null){
 if(!Array.isArray(grid)||!grid.length||!Number.isFinite(f)||f<=0||(rate!==null&&(!Number.isFinite(rate)||rate<=0)))throw RangeError('radiation options');
 const w=2*Math.PI*f;let re=0,im=0;
 for(const q of grid){
  const [a,b]=field(q.x,q.y);let c,s;
  if(rate===null){c=Math.cos(w*q.delay);s=-Math.sin(w*q.delay);}
  else{const t=q.delay*rate,i=Math.floor(t),u=t-i,p=w*i/rate,v=w*(i+1)/rate;c=(1-u)*Math.cos(p)+u*Math.cos(v);s=-(1-u)*Math.sin(p)-u*Math.sin(v);}
  re+=q.weight*(a*c-b*s);im+=q.weight*(a*s+b*c);
 }return [re,im];
}
export function responseDifference(reference,candidate){
 const scale=abs(reference);if(![...reference,...candidate].every(Number.isFinite)||scale<=1e-15)return {relativeComplexError:null,magnitudeDeltaDb:null};
 return {relativeComplexError:abs(sub(candidate,reference))/scale,magnitudeDeltaDb:abs(candidate)>0?20*Math.log10(abs(candidate)/scale):null};
}
