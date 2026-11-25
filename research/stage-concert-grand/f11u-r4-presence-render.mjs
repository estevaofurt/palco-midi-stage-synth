import {buildChord} from './f11s-held-chord-render.mjs';
import {solveMultiContact} from './f11r-multi-hammer-network.mjs';
import {relaxMemory,memoryEnergy,frozenMemoryForce} from './felt-memory.mjs';
import {hammerSpeed} from './f9-midi-velocity.mjs';
import {feltParameters} from './f9-felt-sensitivity.mjs';
import {cholesky,solveCholesky} from './radiation-loading.mjs';
import {dampAxis} from './f11u-r2-distributed.mjs';

// F11u: continuous mechanical state, independently launched hammers.
// Damper forces are eliminated by a Schur complement during hammer contact.
export function renderPresenceTrial(hp,{notes,events,seconds=10,variant='K750',releaseRate=25,distance=1}){
 if(![1,.6,.3].includes(distance)||releaseRate!==25)throw RangeError('presence trial scope');
 if(![10,25].includes(releaseRate))throw RangeError('releaseRate');
 if(!Number.isFinite(seconds)||seconds<.05||seconds>15||!Array.isArray(events)||!events.length)throw RangeError('phrase');
 const {p,modes,board,network,rate,outRate}=buildChord(hp,{notes,variant});
 const n=Math.round(seconds*outRate),h=network.h,G=network.G,contacts=network.contacts;
 const felt=feltParameters(1.5),mass=.01,held=new Set(),active=new Map(),levels=notes.map(()=>1),hits=[];
 let last=-1,pedal=false;
 for(const e of events){
  if(!Number.isSafeInteger(e.ms)||e.ms<last||e.ms<0||e.ms>=seconds*1000)throw RangeError('event time');last=e.ms;
  if(e.type==='pedal'){if(![0,127].includes(e.value))throw RangeError('pedal');}
  else if(!notes.includes(e.midi)||!['on','off'].includes(e.type)||e.type==='on'&&(!Number.isInteger(e.velocity)||e.velocity<1||e.velocity>127))throw RangeError('note event');
 }
 const trace=modes.map(()=>new Float64Array(n)),v0=new Float64Array(modes.length);
 let cursor=0,inputJ=0,retiredJ=0,feltLossJ=0,damperLossJ=0,maxBalance=0,maxIncrease=0,maxResidual=0,prev=0;
 const ids=g=>contacts.map((c,i)=>c.g===g?i:-1).filter(i=>i>=0);
 const energy=()=>{const x=network.displacement();return network.energy()+[...active].reduce((s,[g,a])=>s+.5*mass*a.v*a.v+ids(g).reduce((u,i)=>u+memoryEnergy(a.x-x[i],a.z[i],felt),0),0);};
 for(let k=0;k<2*n;k++){
  const t=k/rate;
  let injected=0;
  while(cursor<events.length&&events[cursor].ms*rate/1000<=k){
   const e=events[cursor++],g=notes.indexOf(e.midi);
   if(e.type==='pedal'){pedal=e.value===127;continue;}
   if(e.type==='off'){if(!held.delete(g))throw Error('orphan off');continue;}
   if(held.has(g)||active.has(g))throw Error('repeat before release or hammer separation');
   held.add(g);levels[g]=0; // key lifts damper before hammer launch; prescribed action.
   const x=network.displacement(),v=hammerSpeed(e.velocity);
   const a={x:Math.min(...ids(g).map(i=>x[i]))-.0002,v,z:contacts.map(()=>0),peak:0,zero:0,midi:e.midi,ms:e.ms};
   active.set(g,a);const j=.5*mass*v*v;inputJ+=j;injected+=j;
  }
  for(let g=0;g<notes.length;g++){const target=held.has(g)||pedal?0:1;levels[g]=target>levels[g]?Math.min(target,levels[g]+h/.025):Math.max(target,levels[g]-h/.025);}
  if(k%2===0)v0.set(board.v);
  if(!active.size)network.step();
  else{
   const before=network.displacement(),free=network.freeContacts();
   const H=contacts.map((c,i)=>active.has(c.g)?i:-1).filter(i=>i>=0);
   // A hammer and damper never act at the same diagnostic contact.
   const D=[]; // distributed damping is split after the contact solve
   const A=D.map((i,p)=>D.map((j,q)=>G[i][j]+(p===q?h/levels[contacts[i].g]:0)));
   const L=D.length?cholesky(A):null;
   const solve=b=>D.length?solveCholesky(L,b):[];
   const df=solve(D.map(i=>before[i]-free[i]));
   const response=H.map(j=>solve(D.map(i=>G[i][j])));
   const corrected=H.map(i=>free[i]+D.reduce((s,j,d)=>s+G[i][j]*df[d],0));
   const C=H.map((i,p)=>H.map((j,q)=>G[i][j]-D.reduce((s,d,l)=>s+G[i][d]*response[q][l],0)+(contacts[i].g===contacts[j].g?h*h/(2*mass):0)));
   for(let i=0;i<C.length;i++)for(let j=0;j<i;j++)C[i][j]=C[j][i]=.5*(C[i][j]+C[j][i]);
   const d0=H.map(i=>active.get(contacts[i].g).x-before[i]);
   const z=H.map((i,j)=>{const a=active.get(contacts[i].g),q=relaxMemory(d0[j],a.z[i],h/2,felt);a.z[i]=q.z;feltLossJ+=q.lossJ;return q.z;});
   const f=solveMultiContact(d0,H.map((i,j)=>{const a=active.get(contacts[i].g);return a.x+h*a.v-corrected[j];}),C,z,H.map(()=>felt)).forces;
   const forces=network.zero.map(r=>r.slice()),dforces=df.map((v,i)=>v-H.reduce((s,j,k)=>s+response[k][i]*f[k],0));
   H.forEach((i,j)=>{const c=contacts[i];forces[c.g][c.j]=f[j];});
   D.forEach((i,j)=>{const c=contacts[i];forces[c.g][c.j]=dforces[j];});
   for(const [g,a] of active){const sum=forces[g].reduce((s,v)=>s+v,0);a.x+=h*a.v-h*h*sum/(2*mass);a.v-=h*sum/mass;a.peak=Math.max(a.peak,sum);a.zero=sum<1e-9?a.zero+1:0;}
   network.step(forces);
   const after=network.displacement();
   D.forEach((i,j)=>{const dx=after[i]-before[i],loss=levels[contacts[i].g]*dx*dx/h;if(Math.abs(dforces[j]*dx+loss)>1e-10)throw Error('damper work');damperLossJ+=loss;});
   H.forEach((i,j)=>{const a=active.get(contacts[i].g),d1=a.x-after[i];maxResidual=Math.max(maxResidual,Math.abs(f[j]-frozenMemoryForce(d0[j],d1,z[j],felt)));const q=relaxMemory(d1,z[j],h/2,felt);a.z[i]=q.z;feltLossJ+=q.lossJ;});
   for(const [g,a] of active){if(a.zero>rate*.002&&a.v<0&&ids(g).every(i=>a.x-after[i]<-.002)){if(!(a.peak>0))throw Error('missing strike');retiredJ+=.5*mass*a.v*a.v+ids(g).reduce((s,i)=>s+memoryEnergy(a.x-after[i],a.z[i],felt),0);hits.push({midi:a.midi,ms:a.ms,peak:a.peak});active.delete(g);}}
  }
  for(let g=0;g<notes.length;g++)if(!active.has(g)&&levels[g]>0){const b=network.bridges[g],r=releaseRate*levels[g];damperLossJ+=dampAxis(b.vAxis,r)+dampAxis(b.hAxis,r);}
  if(k%2===1)for(let j=0;j<modes.length;j++)trace[j][k>>1]=(board.v[j]-v0[j])*outRate;
  const e=energy();maxBalance=Math.max(maxBalance,Math.abs(e+network.lossJ+feltLossJ+damperLossJ+retiredJ-inputJ));maxIncrease=Math.max(maxIncrease,e-prev-injected);prev=e;
 }
 if(active.size||held.size||pedal||cursor!==events.length||hits.length!==events.filter(e=>e.type==='on').length||maxBalance>1e-9||maxIncrease>1e-9||maxResidual>1e-8)throw Error('phrase mechanical gate '+JSON.stringify({maxBalance,maxIncrease,maxResidual,hits:hits.length,active:active.size,held:held.size,pedal}));
 const listeners=[{x:.90,y:.38,z:distance},{x:1.20,y:.38,z:distance}],kernels=listeners.map(l=>{const grid=hp.radiationGrid(p,l,{nx:64,ny:50});return modes.map(m=>hp.radiationKernel(grid,(x,y)=>hp.surfaceShape(m,x,y),outRate));});
 const maxDelay=Math.max(...kernels.flat().map(k=>k.offset+k.taps.length-1));let N=1;while(N<n+maxDelay)N*=2;
 const acc=[0,1].map(()=>({re:new Float64Array(N),im:new Float64Array(N)})),re=new Float64Array(N),im=new Float64Array(N),kr=new Float64Array(N),ki=new Float64Array(N);
 for(let m=0;m<modes.length;m++){re.fill(0);im.fill(0);re.set(trace[m]);hp.fft(re,im);for(let ch=0;ch<2;ch++){const k=kernels[ch][m],u=acc[ch];kr.fill(0);ki.fill(0);kr.set(k.taps,k.offset);hp.fft(kr,ki);for(let i=0;i<=N/2;i++){u.re[i]+=re[i]*kr[i]-im[i]*ki[i];u.im[i]+=re[i]*ki[i]+im[i]*kr[i];}}}
 const channels=acc.map(({re,im})=>{for(let i=1;i<N/2;i++){re[N-i]=re[i];im[N-i]=-im[i];}im[0]=im[N/2]=0;hp.fft(re,im,true);return re.slice(0,n+maxDelay);});

 return {channels,meta:{distance,listeners,maxDelay,releaseRate,notes,events,seconds,variant,modeCount:modes.length,hits,inputJ,retiredJ,feltLossJ,damperLossJ,maxBalance,maxIncrease,maxResidual,finalEnergyJ:energy(),sharedBoard:true}};
}
