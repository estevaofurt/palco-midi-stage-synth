// F9.1 continuous checkpoints: same mechanics and geometric kernels as F8, convolution overlap-add before common export filter.
export function renderChunk(hp,{seconds=.5,velocity=1,scale=1,prior=null}={}){
 const rate=96000,outRate=48000,n=Math.round(seconds*outRate),p=hp.plateDesign(),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>hp.ribDesign(p,{xM})),patch={xM:.83,yM:.46,dxM:.04,dyM:.025},wires=[-.5,0,.5].map(c=>hp.makeDesign(hp.solidWire,{f1Hz:440*2**(-9/12+c/1200)}));
 const modes=hp.mindlinModes(p,ribs,{basisHz:4000},hp).modes.filter(m=>m.frequencyHz<3000);
 const bridge=new hp.PolarizedBridge(wires,{sampleRate:rate,stiffness:[0,2e6],damping:[0,5]},hp),board=new hp.ResistiveBoard(p,modes,patch,bridge.h,{radiation:{scale}},hp),b=new hp.BoardCoupledBridge(bridge,board),hammer=new hp.PolarizedHammer(b,{velocityMps:velocity});
 const obj=[bridge.vAxis,bridge.hAxis,bridge,board,b,hammer];
 const fields=[["x","v","b","vb","workJ","lossJ","bridgeLossJ","stringLossJ"],["x","v","b","vb","workJ","lossJ","bridgeLossJ","stringLossJ"],["workJ","lossJ","bridgeLossJ","stringLossJ"],["x","v","workJ","lossJ","radiationLossJ","structuralLossJ"],["workJ","lossJ","jointLossJ","lastJointForce"],["x","v","z","time","lossJ","impulseNs","lastResidual"]];
 const e0=hammer.energy();
 if(prior){if(prior.velocity!==velocity||prior.scale!==scale||prior.state.length!==obj.length)throw Error("checkpoint");for(let k=0;k<obj.length;k++)for(const f of fields[k]){const v=prior.state[k][f];if(ArrayBuffer.isView(obj[k][f]))obj[k][f].set(v);else obj[k][f]=v;}if(Math.abs(hammer.energy()-prior.finalEnergyJ)>1e-12)throw Error("restore");}
 const originalIncrement=board.increment.bind(board),unit=originalIncrement(1,true);let cache=null;
 board.increment=(f,responseOnly=false)=>{if(responseOnly)return originalIncrement(f,true);if(!cache)cache=originalIncrement(0);return Float64Array.from(cache,(v,i)=>v+f*unit[i]);};const originalStep=board.step.bind(board);board.step=f=>{originalStep(f);cache=null;};
 const trace=modes.map(()=>new Float64Array(n)),v0=new Float64Array(modes.length);let maxBalance=0,maxIncrease=0,prev=hammer.energy(),peakForce=0,zeroSteps=0,detached=!!prior;
 for(let i=0;i<2*n;i++){
  if(i%2===0)v0.set(board.v);
  if(!detached){const s=hammer.step();peakForce=Math.max(peakForce,s.sum);zeroSteps=s.sum>1e-9?0:zeroSteps+1;if(zeroSteps>rate*.002&&hammer.v<0&&hammer.compression().every(d=>d<-.002))detached=true;}
  else{b.step();hammer.x+=hammer.h*hammer.v;hammer.time+=hammer.h;const d=hammer.compression();if(d.some(q=>q>0))throw Error("recontact");for(let j=0;j<3;j++){const q=hp.relaxMemory(d[j],hammer.z[j],hammer.h,hammer.felt);hammer.z[j]=q.z;hammer.lossJ+=q.lossJ;}}
  if(i%2===1){for(let j=0;j<modes.length;j++)trace[j][i>>1]=(board.v[j]-v0[j])*outRate;const e=hammer.energy();maxBalance=Math.max(maxBalance,Math.abs(e+b.lossJ+hammer.lossJ-e0));maxIncrease=Math.max(maxIncrease,e-prev);prev=e;}
 }
 if(!detached||maxBalance>1e-9||maxIncrease>1e-9)throw Error("mechanical invariant");
 const listeners=[{x:.90,y:.38,z:1},{x:1.20,y:.38,z:1}],kernels=listeners.map(l=>{const grid=hp.radiationGrid(p,l,{nx:64,ny:50});return modes.map(m=>hp.radiationKernel(grid,(x,y)=>hp.surfaceShape(m,x,y),outRate));});
 const maxDelay=Math.max(...kernels.flat().map(k=>k.offset+k.taps.length-1));let N=1;while(N<n+maxDelay)N*=2;
 const acc=[0,1].map(()=>({re:new Float64Array(N),im:new Float64Array(N)})),re=new Float64Array(N),im=new Float64Array(N),kr=new Float64Array(N),ki=new Float64Array(N);
 for(let m=0;m<modes.length;m++){re.fill(0);im.fill(0);re.set(trace[m]);hp.fft(re,im);for(let ch=0;ch<2;ch++){const k=kernels[ch][m],u=acc[ch];kr.fill(0);ki.fill(0);kr.set(k.taps,k.offset);hp.fft(kr,ki);for(let i=0;i<=N/2;i++){u.re[i]+=re[i]*kr[i]-im[i]*ki[i];u.im[i]+=re[i]*ki[i]+im[i]*kr[i];}}}
 const channels=acc.map(({re,im})=>{for(let i=1;i<N/2;i++){re[N-i]=re[i];im[N-i]=-im[i];}im[0]=im[N/2]=0;hp.fft(re,im,true);return re.slice(0,n+maxDelay);});
 const state=obj.map((o,k)=>Object.fromEntries(fields[k].map(f=>[f,ArrayBuffer.isView(o[f])?Array.from(o[f]):o[f]])));
 return {channels,checkpoint:{state,velocity,scale,finalEnergyJ:hammer.energy(),elapsed:(prior?.elapsed??0)+seconds},meta:{seconds,velocity,scale,maxBalance,maxIncrease,peakForce,finalEnergyJ:hammer.energy(),boardEnergyJ:board.energy(),radLossJ:board.radiationLossJ,structuralLossJ:board.structuralLossJ,peakPa:Math.max(...channels.map(x=>x.reduce((s,v)=>Math.max(s,Math.abs(v)),0))) }};
}
