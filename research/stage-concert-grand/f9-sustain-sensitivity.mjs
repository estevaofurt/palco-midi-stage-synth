// F9.4: isolated mechanical sensitivity diagnostic, derived from frozen F9.2; no acoustic output.
function fastBoard(board){
 const m=board.modes,n=m.length,h=board.h,dx=new Float64Array(n),base=new Float64Array(n),rhs=new Float64Array(n),unit=board.increment(1,true);
 const blocks=board.blocks.map(b=>({i:Int32Array.from(b.indices),g:Float64Array.from(b.g),L:b.L.map(x=>Float64Array.from(x)),R:b.R.map(x=>Float64Array.from(x))}));
 let cached=false;
 function calc(){
  for(const b of blocks){const is=b.i,g=b.g,L=b.L,N=is.length;
   for(let j=0;j<N;j++){const i=is[j],q=m[i].coeff;let t=((q.A-1)*board.x[i]+q.S*board.v[i])/g[j];for(let k=0;k<j;k++)t-=L[j][k]*rhs[k];rhs[j]=t/L[j][j];}
   for(let j=N-1;j>=0;j--){let t=rhs[j];for(let k=j+1;k<N;k++)t-=L[k][j]*rhs[k];rhs[j]=t/L[j][j];base[is[j]]=g[j]*rhs[j];}
  }cached=true;
 }
 board.free=()=>{if(!cached)calc();let pos=0,inc=0;for(let i=0;i<n;i++){pos+=m[i].w*board.x[i];inc+=m[i].w*base[i];}return pos+inc;};
 board.step=f=>{
  if(!cached)calc();for(let i=0;i<n;i++)dx[i]=base[i]+f*unit[i];
  let rad=0,local=0,work=0;for(const b of blocks){const is=b.i,N=is.length;for(let j=0;j<N;j++){const i=is[j],mode=m[i],q=mode.coeff,x=board.x[i],v=board.v[i],row=b.R[j];let z=0;for(let k=0;k<N;k++)z+=row[k]*dx[is[k]]/h;const rf=-z,F=mode.w*f+rf,xn=q.A*x+q.S*v+q.G*F,vn=q.H*x+q.D*v+q.J*F;
   rad-=rf*(xn-x);local+=F*(xn-x)+.5*(v*v-vn*vn+mode.lambda*(x*x-xn*xn));work+=mode.w*f*(xn-x);board.x[i]=xn;board.v[i]=vn;board.lastModalForce[i]=F;}}
  board.radiationLossJ+=rad;board.structuralLossJ+=local;board.lossJ+=rad+local;board.workJ+=work;cached=false;
 };
}
function relaxFree(d,z,h,p){
 if(d>=0)return (()=>{throw Error('free relaxation requires negative compression')})();
 const a=h*p.kr/(2*p.viscosity),next=z*(1-a)/(1+a);
 return {z:next,lossJ:p.viscosity*(next-z)**2/h};
}
// F9.1 continuous checkpoints: same mechanics and geometric kernels as F8, convolution overlap-add before common export filter.
export function diagnoseSustain(hp,{seconds=.5,velocity=1,scale=1,prior=null,lossFactor=1,boardFactor=1}={}){
 if(![lossFactor,boardFactor].every(x=>Number.isFinite(x)&&x>=0)||!Number.isFinite(seconds)||seconds<.1||Math.abs(seconds*10-Math.round(seconds*10))>1e-10||prior)throw new RangeError('diagnostic: start at impact, 0.1 s windows, nonnegative loss factors');
 const rate=96000,outRate=48000,n=Math.round(seconds*outRate),p=hp.plateDesign(),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>hp.ribDesign(p,{xM})),patch={xM:.83,yM:.46,dxM:.04,dyM:.025},wires=[-.5,0,.5].map(c=>hp.makeDesign(hp.solidWire,{f1Hz:440*2**(-9/12+c/1200)}));
 const modes=hp.mindlinModes(p,ribs,{basisHz:4000},hp).modes.filter(m=>m.frequencyHz<3000);
 const bridge=new hp.PolarizedBridge(wires,{sampleRate:rate,stiffness:[0,2e6],damping:[0,5],verticalLoss:[.4*lossFactor,.0002*lossFactor],horizontalLoss:[.2*lossFactor,.00012*lossFactor]},hp),board=new hp.ResistiveBoard(p,modes,patch,bridge.h,{loss0:2*boardFactor,lossSlope:.0005*boardFactor,radiation:{scale}},hp),b=new hp.BoardCoupledBridge(bridge,board),hammer=new hp.PolarizedHammer(b,{velocityMps:velocity});
 const obj=[bridge.vAxis,bridge.hAxis,bridge,board,b,hammer];
 const fields=[["x","v","b","vb","workJ","lossJ","bridgeLossJ","stringLossJ"],["x","v","b","vb","workJ","lossJ","bridgeLossJ","stringLossJ"],["workJ","lossJ","bridgeLossJ","stringLossJ"],["x","v","workJ","lossJ","radiationLossJ","structuralLossJ"],["workJ","lossJ","jointLossJ","lastJointForce"],["x","v","z","time","lossJ","impulseNs","lastResidual"]];
 const e0=hammer.energy();
 if(prior){if(prior.velocity!==velocity||prior.scale!==scale||prior.state.length!==obj.length)throw Error("checkpoint");for(let k=0;k<obj.length;k++)for(const f of fields[k]){const v=prior.state[k][f];if(ArrayBuffer.isView(obj[k][f]))obj[k][f].set(v);else obj[k][f]=v;}if(Math.abs(hammer.energy()-prior.finalEnergyJ)>1e-12)throw Error("restore");}
 fastBoard(board);
 const trace=[],v0=new Float64Array(modes.length),windows=[];let boardV2=0,winN=0;let maxBalance=0,maxIncrease=0,prev=hammer.energy(),peakForce=0,zeroSteps=0,detached=!!prior;
 for(let i=0;i<2*n;i++){
  
  if(!detached){const s=hammer.step();peakForce=Math.max(peakForce,s.sum);zeroSteps=s.sum>1e-9?0:zeroSteps+1;if(zeroSteps>rate*.002&&hammer.v<0&&hammer.compression().every(d=>d<-.002))detached=true;}
  else{b.step();hammer.x+=hammer.h*hammer.v;hammer.time+=hammer.h;const d=hammer.compression();if(d.some(q=>q>0))throw Error("recontact");for(let j=0;j<3;j++){const q=relaxFree(d[j],hammer.z[j],hammer.h,hammer.felt);hammer.z[j]=q.z;hammer.lossJ+=q.lossJ;}}
  if(i%2===1){boardV2+=board.v.reduce((s,v)=>s+v*v,0);winN++;if(winN===4800){windows.push({time:(i+1)/rate,boardVelocityNormRms:Math.sqrt(boardV2/winN),boardEnergyJ:board.energy(),stringLossJ:bridge.stringLossJ,bridgeLossJ:bridge.bridgeLossJ,jointLossJ:b.jointLossJ,radLossJ:board.radiationLossJ,structuralLossJ:board.structuralLossJ,hammerLossJ:hammer.lossJ});boardV2=0;winN=0;}const e=hammer.energy();maxBalance=Math.max(maxBalance,Math.abs(e+b.lossJ+hammer.lossJ-e0));maxIncrease=Math.max(maxIncrease,e-prev);prev=e;}
 }
 if(!detached||maxBalance>1e-9||maxIncrease>1e-9)throw Error("mechanical invariant");
 return {seconds,lossFactor,boardFactor,maxBalance,maxIncrease,peakForce,finalEnergyJ:hammer.energy(),windows};
}
