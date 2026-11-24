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
export function boardMobility(board,f){
 if(!Number.isFinite(f)||f<=0)throw RangeError('frequency');
 const w=2*Math.PI*f;let Y=[0,0],structuralW=0,radiationW=0,maxRelativeResidual=0;
 for(const b of board.blocks){
  const modes=b.indices.map(i=>board.modes[i]),N=modes.length;
  const A=modes.map((m,i)=>modes.map((_,j)=>[i===j?m.lambda-w*w:0,w*(b.R[i][j]+(i===j?m.coeff.dampingNsM:0))]));
  const F=modes.map(m=>[m.w,0]),x=solve(A,F),v=x.map(z=>mul([0,w],z));
  for(let i=0;i<N;i++){
   Y=add(Y,mul([modes[i].w,0],v[i]));structuralW+=.5*modes[i].coeff.dampingNsM*abs(v[i])**2;
   let rv=[0,0],ax=[0,0],scale=abs(F[i]);for(let j=0;j<N;j++){rv=add(rv,mul([b.R[i][j],0],v[j]));const t=mul(A[i][j],x[j]);ax=add(ax,t);scale+=abs(t);}
   radiationW+=.5*(v[i][0]*rv[0]+v[i][1]*rv[1]);maxRelativeResidual=Math.max(maxRelativeResidual,abs(sub(ax,F[i]))/Math.max(scale,1e-300));
  }
 }
 const inputW=.5*Y[0];return {f,Y,structuralW,radiationW,inputW,powerResidualW:inputW-structuralW-radiationW,maxRelativeResidual};
}
export function loadedMobility(bare,Yb,f,jointK,jointC){
 if(!Number.isFinite(f)||f<=0||![jointK,jointC].every(v=>Number.isFinite(v)&&v>=0))throw RangeError('load options');
 const Zj=[jointC,-jointK/(2*Math.PI*f)];
 const Zload=abs(Zj)===0?[0,0]:div(Zj,add([1,0],mul(Zj,Yb)));
 const den=add([1,0],mul(Zload,bare.vv));
 const vv=div(bare.vv,den),vh=div(bare.vh,den),hh=sub(bare.hh,div(mul(Zload,mul(bare.vh,bare.vh)),den));
 // Vertical applied harmonic force of peak 1 N. Load force is Zload*bridge velocity.
 const loadForce=mul(Zload,vv),boardVelocity=mul(Yb,loadForce);
 const boardInputW=.5*abs(loadForce)**2*Yb[0],jointLossW=.5*jointC*abs(sub(vv,boardVelocity))**2,inputW=.5*vv[0];
 return {f,vv,vh,hh,Zload,realDet:vv[0]*hh[0]-vh[0]**2,inputW,boardInputW,jointLossW,bridgeAndStringsW:inputW-boardInputW-jointLossW};
}
export function scanBand(bridge,board,{centerHz,halfWidthHz=2,stepHz=.05,jointK=1e7,jointC=1}={}){
 if(!Number.isFinite(centerHz)||!Number.isFinite(halfWidthHz)||!Number.isFinite(stepHz)||halfWidthHz<=0||stepHz<=0||centerHz<=halfWidthHz||2*halfWidthHz/stepHz>4000)throw RangeError('scan bounds');
 const n=Math.round(2*halfWidthHz/stepHz),rows=[];
 for(let i=0;i<=n;i++){const f=centerHz-halfWidthHz+i*2*halfWidthHz/n,boardResponse=boardMobility(board,f),bare=bridge.mobility(f),loaded=loadedMobility(bare,boardResponse.Y,f,jointK,jointC);rows.push({f,board:boardResponse,bare,loaded});}
 return rows;
}
