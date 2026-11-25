// Continuous-frequency linear diagnostic of the existing mechanical system.
// Does not change the time-domain renderer or claim perceptual pitch.
// Convention exp(i*w*t); velocity/force mobility, SI.
const add=([a,b],[c,d])=>[a+c,b+d],sub=([a,b],[c,d])=>[a-c,b-d],mul=([a,b],[c,d])=>[a*c-b*d,a*d+b*c],abs=z=>Math.hypot(...z);
const div=([a,b],[c,d])=>{const n=c*c+d*d;if(!(n>0))throw Error('singular response');return [(a*c+b*d)/n,(b*c-a*d)/n];};
export function solveComplex(A,b){
 const n=b.length,M=A.map((row,i)=>[...row.map(z=>z.slice()),b[i].slice()]);
 for(let i=0;i<n;i++){
  let p=i;for(let k=i+1;k<n;k++)if(abs(M[k][i])>abs(M[p][i]))p=k;
  [M[i],M[p]]=[M[p],M[i]];
  const v=M[i][i];for(let j=i;j<=n;j++)M[i][j]=div(M[i][j],v);
  for(let k=i+1;k<n;k++){const q=M[k][i];for(let j=i;j<=n;j++)M[k][j]=sub(M[k][j],mul(q,M[i][j]));}
 }
 const x=Array(n);for(let i=n-1;i>=0;i--){let z=M[i][n];for(let j=i+1;j<n;j++)z=sub(z,mul(M[i][j],x[j]));x[i]=z;}
 return x;
}
export function boardMobility(board,f){
 if(!Number.isFinite(f)||f<=0)throw RangeError('frequency');
 const w=2*Math.PI*f,vel=Array(board.modes.length),seen=new Set;
 let Y=[0,0];
 for(const block of board.blocks){
  const ids=block.indices,ms=ids.map(i=>board.modes[i]);
  const A=ms.map((m,i)=>ms.map((_,j)=>[i===j?m.lambda-w*w:0,w*(block.R[i][j]+(i===j?m.coeff.dampingNsM:0))]));
  const x=solveComplex(A,ms.map(m=>[m.w,0]));
  ids.forEach((id,j)=>{if(seen.has(id))throw Error('duplicate mode');seen.add(id);vel[id]=mul([0,w],x[j]);Y=add(Y,mul([ms[j].w,0],vel[id]));});
 }
 if(seen.size!==board.modes.length||Y[0]<-1e-10||!Y.every(Number.isFinite))throw Error('nonpassive or incomplete board mobility');
 return {Y,vel};
}
// Condensed effective force from equal vertical hammer-contact forces on each wire.
export function contactDrive(bridge,f){
 const w=2*Math.PI*f,a=bridge.vAxis;
 let q=[.13*bridge.wires.length,0];
 for(const m of a.modes)q=sub(q,mul([m.weight,0],div([-w*w*m.cross,w*m.cc],[m.k-w*w*m.m,w*m.c])));
 return q;
}
export function coupledMobility(bridge,board,joint,f){
 const w=2*Math.PI*f,Ys=bridge.mobility(f).vv,{Y:Yb,vel}=boardMobility(board,f);
 const Z=[joint.c,-joint.k/w],den=add([1,0],mul(Z,add(Ys,Yb)));
 const jointForce=div(mul(Z,Ys),den),input=div(mul(Ys,add([1,0],mul(Z,Yb))),den);
 const drive=contactDrive(bridge,f),contactJointForce=mul(jointForce,drive);
 const modal=vel.map((z,i)=>({i,hz:board.modes[i].frequencyHz,velocity:abs(mul(z,contactJointForce))}));
 if(input[0]<-1e-10)throw Error('nonpassive coupled mobility');
 return {f,board:Yb,bridge:Ys,input,contactDrive:drive,contactBoardVelocity:abs(mul(Yb,contactJointForce)),modalVelocityNorm:Math.hypot(...modal.map(m=>m.velocity)),topModes:modal.sort((a,b)=>b.velocity-a.velocity).slice(0,4)};
}
export function scanBand(bridge,board,joint,center,spanCents=80,stepHz=.05){
 if(!(center>0&&spanCents>0&&stepHz>0))throw RangeError('scan');
 const lo=center*2**(-spanCents/1200),hi=center*2**(spanCents/1200),n=Math.ceil((hi-lo)/stepHz);
 if(n>5000)throw RangeError('scan size');
 const samples=Array.from({length:n+1},(_,i)=>coupledMobility(bridge,board,joint,lo+(hi-lo)*i/n));
 const peaks=samples.filter((v,i)=>i>0&&i<n&&v.modalVelocityNorm>=samples[i-1].modalVelocityNorm&&v.modalVelocityNorm>samples[i+1].modalVelocityNorm).sort((a,b)=>b.modalVelocityNorm-a.modalVelocityNorm).slice(0,6).map(v=>({...v,cents:1200*Math.log2(v.f/center)}));
 return {center,lo,hi,stepHz:(hi-lo)/n,peaks,samples};
}
