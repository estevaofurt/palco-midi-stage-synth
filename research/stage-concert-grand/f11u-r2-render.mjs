import {SharedBoard} from './f9-shared-board.mjs';
import {fastSharedBoard} from './f9-sympathetic-network.mjs';
import {MultiHammerNetwork,SimultaneousHammers} from './f11r-multi-hammer-network.mjs';
import {locateSuspectModes} from './f9-rattle-selective.mjs';
import {modalCoefficients} from './exact-modal.mjs';
import {cholesky} from './radiation-loading.mjs';
import {applyLocalLoss} from './f10c-d-local.mjs';
import {bassWires,BASS_NOTES} from './f11d-bass-render.mjs';
import {scaleWire,SCALE_NOTES} from './f11a-s50-scale.mjs';
import {feltParameters} from './f9-felt-sensitivity.mjs';
import {hammerSpeed} from './f9-midi-velocity.mjs';
import {SUPPORT_VARIANTS} from './f11q-bass-support-trial.mjs';
import {PolyDamperController} from './f11u-release-damper.mjs';
import {distributedStep} from './f11u-r2-distributed.mjs';
// First sustained simultaneous chord, no release/pedal/retrigger yet.
// Identical conjugate patch for every note is a deliberate diagnostic geometry,
// matching isolated S50, not a calibrated spatial layout.
export function buildChord(hp,{notes=[48,64,67,72],midiVelocity=76,variant='K750'}={}){
 if(!['A','K750','K1000'].includes(variant)||![24,76,127].includes(midiVelocity)||notes.length<1||notes.length>6||new Set(notes).size!==notes.length||notes.some(m=>!BASS_NOTES.includes(m)&&!SCALE_NOTES.includes(m)))throw RangeError('chord scope');
 const rate=96000,outRate=48000,p=hp.plateDesign(),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>hp.ribDesign(p,{xM})),patch={xM:.83,yM:.46,dxM:.04,dyM:.025};
 const modes=hp.mindlinModes(p,ribs,{basisHz:4000},hp).modes.filter(m=>m.frequencyHz<3000);
 const bridges=notes.map(midi=>{
  const bass=BASS_NOTES.includes(midi),wires=bass?bassWires(midi,2):[-.5,0,.5].map(c=>scaleWire(hp,midi,c));
  return new hp.PolarizedBridge(wires,{sampleRate:rate,stiffness:[bass?SUPPORT_VARIANTS[variant]:0,2e6],damping:[0,5],angleRad:.5,verticalLoss:[.1,.0002],horizontalLoss:[.05,.00012]},hp);
 });
 const board=new SharedBoard(p,modes,notes.map(()=>({...patch})),1/rate,{loss0:3,lossSlope:.00075,radiation:{scale:1}},hp);
 const ids=locateSuspectModes(board.modes),chosen=new Set(ids);
 for(const i of ids){const q=board.modes[i].coeff;board.modes[i].coeff=modalCoefficients({massKg:q.massKg,frequencyHz:q.frequencyHz,dampingNsM:2*(4+.001*2*Math.PI*q.frequencyHz),dt:q.dt});}
 board.blocks=board.blocks.map(b=>{
  if(!b.indices.some(i=>chosen.has(i)))return b;
  const g=b.indices.map(i=>Math.sqrt(board.modes[i].coeff.G));
  return {...b,g,L:cholesky(b.R.map((row,i)=>row.map((v,j)=>+(i===j)+g[i]*v*g[j]/board.h)))};
 });
 const response=board.increment(1,true);board.G=board.modes.reduce((s,m,i)=>s+m.w*response[i],0);
 const local=applyLocalLoss(board,'local8');
 // Rebuild reciprocal multi-port compliance after all modal loss modifications.
 board.responses=board.weights.map((_,j)=>board.incrementPorts(board.weights.map((_,i)=>+(i===j)),true));
 board.portG=board.weights.map(w=>board.responses.map(dx=>w.reduce((s,x,i)=>s+x*dx[i],0)));
 const network=new MultiHammerNetwork(bridges,board,notes.map(()=>({k:1e7,c:1})));
 fastSharedBoard(board);
 const hammers=new SimultaneousHammers(network,notes.map(()=>({velocityMps:hammerSpeed(midiVelocity),felt:feltParameters(1.5)})));
 return {p,modes,board,network,hammers,rate,outRate,notes:notes.slice(),midiVelocity,variant,local,boardSignature:board.modes.map(m=>[m.frequencyHz,m.coeff.dampingNsM])};
}
export function renderDistributedTrial(hp,options={}){
 const seconds=options.seconds??3, strength=options.strength??1;
 if(![10,25,50].includes(strength))throw RangeError('strength');
 if(!Number.isFinite(seconds)||seconds<.05||seconds>3)throw RangeError('chord duration');
 const {p,modes,board,network,hammers,rate,outRate,notes,midiVelocity,variant,local,boardSignature}=buildChord(hp,options),n=Math.round(seconds*outRate);
 if(options.events!==undefined&&!Array.isArray(options.events))throw RangeError('chord events');
 const events=options.events??[],control=events.length?new PolyDamperController(notes,events,seconds):null;
 const trace=modes.map(()=>new Float64Array(n)),v0=new Float64Array(modes.length),peaks=notes.map(()=>0);
 const e0=hammers.energy();let prev=e0,maxBalance=0,maxIncrease=0,contactResidual=0,zeroSteps=0,detached=false,damperLossJ=0;
 for(let i=0;i<2*n;i++){
  if(i%2===0)v0.set(board.v);
  if(!detached){
   const f=hammers.step();let sum=0;f.forEach((row,g)=>{const q=row.reduce((s,x)=>s+x,0);peaks[g]=Math.max(peaks[g],q);sum+=q;});
   contactResidual=Math.max(contactResidual,hammers.lastResidual);zeroSteps=sum>1e-9?0:zeroSteps+1;
   if(zeroSteps>rate*.002&&hammers.hammers.every(a=>a.v<0)&&hammers.compression().every(d=>d<-.002))detached=true;
  }else{
   if(control)damperLossJ+=distributedStep(network,control.coefficientsAt((i+.5)/rate),strength,options.both!==false);else network.step();
   for(const a of hammers.hammers)a.x+=hammers.h*a.v;
   const d=hammers.compression();if(d.some(x=>x>=0))throw Error('recontact');
   for(let j=0;j<d.length;j++){const f=hammers.hammers[network.contacts[j].g].felt,z=hammers.z[j],a=hammers.h*f.kr/(2*f.viscosity),next=z*(1-a)/(1+a);hammers.z[j]=next;hammers.lossJ+=f.viscosity*(next-z)**2/hammers.h;}
  }
  if(i%2===1){for(let j=0;j<modes.length;j++)trace[j][i>>1]=(board.v[j]-v0[j])*outRate;const e=hammers.energy();maxBalance=Math.max(maxBalance,Math.abs(e+network.lossJ+hammers.lossJ+damperLossJ-e0));maxIncrease=Math.max(maxIncrease,e-prev);prev=e;}
 }
 if(!detached||!peaks.every(x=>x>0)||maxBalance>1e-9||maxIncrease>1e-9||contactResidual>1e-8)throw Error('chord mechanical gate');
 const listeners=[{x:.90,y:.38,z:1},{x:1.20,y:.38,z:1}],kernels=listeners.map(l=>{const grid=hp.radiationGrid(p,l,{nx:64,ny:50});return modes.map(m=>hp.radiationKernel(grid,(x,y)=>hp.surfaceShape(m,x,y),outRate));});
 const maxDelay=Math.max(...kernels.flat().map(k=>k.offset+k.taps.length-1));let N=1;while(N<n+maxDelay)N*=2;
 const acc=[0,1].map(()=>({re:new Float64Array(N),im:new Float64Array(N)})),re=new Float64Array(N),im=new Float64Array(N),kr=new Float64Array(N),ki=new Float64Array(N);
 for(let m=0;m<modes.length;m++){re.fill(0);im.fill(0);re.set(trace[m]);hp.fft(re,im);for(let ch=0;ch<2;ch++){const k=kernels[ch][m],u=acc[ch];kr.fill(0);ki.fill(0);kr.set(k.taps,k.offset);hp.fft(kr,ki);for(let i=0;i<=N/2;i++){u.re[i]+=re[i]*kr[i]-im[i]*ki[i];u.im[i]+=re[i]*ki[i]+im[i]*kr[i];}}}
 const channels=acc.map(({re,im})=>{for(let i=1;i<N/2;i++){re[N-i]=re[i];im[N-i]=-im[i];}im[0]=im[N/2]=0;hp.fft(re,im,true);return re.slice(0,n+maxDelay);});

 return {channels,meta:{strength,both:options.both!==false,notes,midiVelocity,variant,seconds,boardSignature,modeCount:modes.length,local,patch:'coincident original diagnostic ports',maxBalance,maxIncrease,contactResidual,peaks,rebound:hammers.hammers.map(a=>a.v),sharedBoard:true,held:!control,pedal:events.some(e=>e.type==='pedal'&&e.value===127),events:events.map(e=>({...e})),damperLossJ,releaseModel:control?'R2 distributed modal velocity damping':'none',initialEnergyJ:e0,finalEnergyJ:hammers.energy(),boardEnergyJ:board.energy(),radiationLossJ:board.radiationLossJ,structuralLossJ:board.structuralLossJ}};
}
