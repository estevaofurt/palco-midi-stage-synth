import {polarizationLedger} from './f9-aftersound-ledger.mjs';
import {locateSuspectModes} from './f9-rattle-selective.mjs';
import {modalCoefficients} from './exact-modal.mjs';
import {cholesky} from './radiation-loading.mjs';
import {applyLocalLoss} from './f10c-d-local.mjs';
import {bassCandidate,BASS_ANCHORS} from './f11c-bass-candidates.mjs';
import {woundWire} from './f11c-wound-wire.mjs';
import {VariableHammer} from './f11d-variable-hammer.mjs';
import {hammerSpeed} from './f9-midi-velocity.mjs';
import {feltParameters} from './f9-felt-sensitivity.mjs';
export const BASS_NOTES=Object.freeze(BASS_ANCHORS.map(x=>x.midi));
export function bassWires(midi,count){
 if(!BASS_NOTES.includes(midi)||![1,2].includes(count))throw RangeError('bass pilot');
 const wire=bassCandidate(midi);
 return (count===1?[0]:[-.5,.5]).map(c=>woundWire({...wire,f1Hz:wire.f1Hz*2**(c/1200)}));
}
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
// Isolated bass pilot, same passive board and S50 loss coefficients, not a measured scale.
export function renderBassPilot(hp,{midi=36,count=1,midiVelocity=76,seconds=.5,prior=null}={}){
 const velocity=hammerSpeed(midiVelocity),scale=1,boardFactor=.5,angleRad=.5,spreadCents=.5,lossCase='S50-bass',multiplier=3,felt=feltParameters(1.5);
 if(!Number.isFinite(seconds)||seconds<=0||!Number.isFinite(velocity)||velocity<=0)throw RangeError('bass options');
 if(prior&&(prior.bassPilot!==true||prior.midi!==midi||prior.count!==count||prior.midiVelocity!==midiVelocity))throw Error('bass checkpoint mismatch');
 const losses={verticalLoss:[.1,.0002],horizontalLoss:[.05,.00012]};let selection=null;
 class HybridBoard extends hp.ResistiveBoard{
  constructor(p,modes,patch,h,options,helpers){
   if(options.loss0!==1||options.lossSlope!==.00025)throw Error('baseline loss changed');
   super(p,modes,patch,h,{...options,loss0:options.loss0*multiplier,lossSlope:options.lossSlope*multiplier},helpers);
   const ids=locateSuspectModes(this.modes),chosen=new Set(ids),before=this.modes.map(m=>m.coeff);
   if(multiplier!==4){
    for(const i of ids){
     const q=before[i],d=2*(4+.001*2*Math.PI*q.frequencyHz);
     this.modes[i].coeff=modalCoefficients({massKg:q.massKg,frequencyHz:q.frequencyHz,dampingNsM:d,dt:q.dt});
    }
    this.blocks=this.blocks.map(b=>{
     if(!b.indices.some(i=>chosen.has(i)))return b;
     const g=b.indices.map(i=>Math.sqrt(this.modes[i].coeff.G));
     return {...b,g,L:cholesky(b.R.map((row,i)=>row.map((v,j)=>+(i===j)+g[i]*v*g[j]/h)))};
    });
    const response=this.increment(1,true);this.G=this.modes.reduce((s,m,i)=>s+m.w*response[i],0);
   }
   if(!(this.G>0)||this.modes.some((m,i)=>!chosen.has(i)&&m.coeff!==before[i]))throw Error('hybrid scope');
   selection={modeCount:this.modes.length,globalMultiplier:multiplier,suspectMultiplier:4,modifiedCount:multiplier===4?0:ids.length,modes:ids.map(i=>({index:i,frequencyHz:this.modes[i].frequencyHz,damping:this.modes[i].coeff.dampingNsM}))};
  }
 }

 const rate=96000,outRate=48000,n=Math.round(seconds*outRate),p=hp.plateDesign(),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>hp.ribDesign(p,{xM})),patch={xM:.83,yM:.46,dxM:.04,dyM:.025},wires=bassWires(midi,count);
 const modes=hp.mindlinModes(p,ribs,{basisHz:4000},hp).modes.filter(m=>m.frequencyHz<3000);
 const bridge=new hp.PolarizedBridge(wires,{sampleRate:rate,stiffness:[0,2e6],damping:[0,5],angleRad,...losses},hp),board=new HybridBoard(p,modes,patch,bridge.h,{loss0:2*boardFactor,lossSlope:.0005*boardFactor,radiation:{scale}},hp),local=applyLocalLoss(board,'local8'),b=new hp.BoardCoupledBridge(bridge,board),hammer=new VariableHammer(b,{velocityMps:velocity,felt});
 const obj=[bridge.vAxis,bridge.hAxis,bridge,board,b,hammer];
 const fields=[["x","v","b","vb","workJ","lossJ","bridgeLossJ","stringLossJ"],["x","v","b","vb","workJ","lossJ","bridgeLossJ","stringLossJ"],["workJ","lossJ","bridgeLossJ","stringLossJ"],["x","v","workJ","lossJ","radiationLossJ","structuralLossJ"],["workJ","lossJ","jointLossJ","lastJointForce"],["x","v","z","time","lossJ","impulseNs","lastResidual"]];
 const e0=hammer.energy();
 if(prior){if(prior.velocity!==velocity||prior.scale!==scale||prior.boardFactor!==boardFactor||prior.angleRad!==angleRad||prior.spreadCents!==spreadCents||prior.lossCase!==lossCase||prior.state.length!==obj.length)throw Error("checkpoint");for(let k=0;k<obj.length;k++)for(const f of fields[k]){const v=prior.state[k][f];if(ArrayBuffer.isView(obj[k][f]))obj[k][f].set(v);else obj[k][f]=v;}if(Math.abs(hammer.energy()-prior.finalEnergyJ)>1e-12)throw Error("restore");}
 fastBoard(board);
 const trace=modes.map(()=>new Float64Array(n)),v0=new Float64Array(modes.length);let maxBalance=0,maxIncrease=0,prev=hammer.energy(),peakForce=0,zeroSteps=0,detached=!!prior;
 for(let i=0;i<2*n;i++){
  if(i%2===0)v0.set(board.v);
  if(!detached){const s=hammer.step();peakForce=Math.max(peakForce,s.sum);zeroSteps=s.sum>1e-9?0:zeroSteps+1;if(zeroSteps>rate*.002&&hammer.v<0&&hammer.compression().every(d=>d<-.002))detached=true;}
  else{b.step();hammer.x+=hammer.h*hammer.v;hammer.time+=hammer.h;const d=hammer.compression();if(d.some(q=>q>0))throw Error("recontact");for(let j=0;j<count;j++){const q=relaxFree(d[j],hammer.z[j],hammer.h,hammer.felt);hammer.z[j]=q.z;hammer.lossJ+=q.lossJ;}}
  if(i%2===1){for(let j=0;j<modes.length;j++)trace[j][i>>1]=(board.v[j]-v0[j])*outRate;const e=hammer.energy();maxBalance=Math.max(maxBalance,Math.abs(e+b.lossJ+hammer.lossJ-e0));maxIncrease=Math.max(maxIncrease,e-prev);prev=e;}
 }
 if(!detached||maxBalance>1e-9||maxIncrease>1e-9)throw Error("mechanical invariant");
 const listeners=[{x:.90,y:.38,z:1},{x:1.20,y:.38,z:1}],kernels=listeners.map(l=>{const grid=hp.radiationGrid(p,l,{nx:64,ny:50});return modes.map(m=>hp.radiationKernel(grid,(x,y)=>hp.surfaceShape(m,x,y),outRate));});
 const maxDelay=Math.max(...kernels.flat().map(k=>k.offset+k.taps.length-1));let N=1;while(N<n+maxDelay)N*=2;
 const acc=[0,1].map(()=>({re:new Float64Array(N),im:new Float64Array(N)})),re=new Float64Array(N),im=new Float64Array(N),kr=new Float64Array(N),ki=new Float64Array(N);
 for(let m=0;m<modes.length;m++){re.fill(0);im.fill(0);re.set(trace[m]);hp.fft(re,im);for(let ch=0;ch<2;ch++){const k=kernels[ch][m],u=acc[ch];kr.fill(0);ki.fill(0);kr.set(k.taps,k.offset);hp.fft(kr,ki);for(let i=0;i<=N/2;i++){u.re[i]+=re[i]*kr[i]-im[i]*ki[i];u.im[i]+=re[i]*ki[i]+im[i]*kr[i];}}}
 const channels=acc.map(({re,im})=>{for(let i=1;i<N/2;i++){re[N-i]=re[i];im[N-i]=-im[i];}im[0]=im[N/2]=0;hp.fft(re,im,true);return re.slice(0,n+maxDelay);});
 const state=obj.map((o,k)=>Object.fromEntries(fields[k].map(f=>[f,ArrayBuffer.isView(o[f])?Array.from(o[f]):o[f]])));
 return {channels,checkpoint:{bassPilot:true,midi,count,midiVelocity,state,velocity,scale,boardFactor,angleRad,spreadCents,lossCase,finalEnergyJ:hammer.energy(),elapsed:(prior?.elapsed??0)+seconds},meta:{midi,count,midiVelocity,wire:bassCandidate(midi),wires,selection,local,boardSignature:board.modes.map(m=>[m.frequencyHz,m.coeff.dampingNsM]),feltFactor:1.5,actualStringLoss:losses,seconds,velocity,scale,boardFactor,angleRad,spreadCents,lossCase,polarization:polarizationLedger(bridge),maxBalance,maxIncrease,peakForce,reboundMps:hammer.v,contactResidual:hammer.lastResidual,finalEnergyJ:hammer.energy(),boardEnergyJ:board.energy(),radLossJ:board.radiationLossJ,structuralLossJ:board.structuralLossJ,peakPa:Math.max(...channels.map(x=>x.reduce((s,v)=>Math.max(s,Math.abs(v)),0))) }};
}
