// F8 offline research render, no samples. Gain and final export fade only.
export function fft(re,im,inverse=false){
 const N=re.length;for(let i=1,j=0;i<N;i++){let b=N>>1;for(;j&b;b>>=1)j^=b;j^=b;if(i<j){let t=re[i];re[i]=re[j];re[j]=t;t=im[i];im[i]=im[j];im[j]=t;}}
 for(let size=2;size<=N;size*=2){const angle=(inverse?2:-2)*Math.PI/size,c=Math.cos(angle),s=Math.sin(angle),half=size/2;for(let i=0;i<N;i+=size){let wr=1,wi=0;for(let j=0;j<half;j++){const u=i+j,v=u+half,tr=re[v]*wr-im[v]*wi,ti=re[v]*wi+im[v]*wr;re[v]=re[u]-tr;im[v]=im[u]-ti;re[u]+=tr;im[u]+=ti;const nr=wr*c-wi*s;wi=wr*s+wi*c;wr=nr;}}}
 if(inverse)for(let i=0;i<N;i++){re[i]/=N;im[i]/=N;}
}

export function makeRenderer(hp,{rate=96000,outRate=48000,seconds=1.2,cut=3000,nx=64,ny=50}={}){
 const p=hp.plateDesign(),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>hp.ribDesign(p,{xM})),patch={xM:.83,yM:.46,dxM:.04,dyM:.025},wires=[-.5,0,.5].map(c=>hp.makeDesign(hp.solidWire,{f1Hz:440*2**(-9/12+c/1200)}));
 const modes=hp.mindlinModes(p,ribs,{basisHz:4000},hp).modes.filter(m=>m.frequencyHz<cut),listeners=[{x:.90,y:.38,z:1},{x:1.20,y:.38,z:1}],factor=rate/outRate,n=Math.round(seconds*outRate);
 if(!Number.isInteger(factor)||factor<1)throw Error('rate');
 const kernels=listeners.map(l=>{const grid=hp.radiationGrid(p,l,{nx,ny});return modes.map(m=>hp.radiationKernel(grid,(x,y)=>hp.surfaceShape(m,x,y),outRate));});
 const maxDelay=Math.max(...kernels.flat().map(k=>k.offset+k.taps.length-1));let N=1;while(N<n+maxDelay)N*=2;
 // Precompute exact geometric kernel DFTs only over the retained PCM band; overlap/add unnecessary for finite trace.
 const bins=Math.min(N/2,Math.floor(12000*N/outRate));
 const spectra=kernels.map(ks=>ks.map(k=>{const re=new Float64Array(N),im=new Float64Array(N);re.set(k.taps,k.offset);fft(re,im);return {re:re.slice(0,bins+1),im:im.slice(0,bins+1)};}));
 function render(velocity,scale){
  const bridge=new hp.PolarizedBridge(wires,{sampleRate:rate,stiffness:[0,2e6],damping:[0,5]},hp),board=new hp.ResistiveBoard(p,modes,patch,bridge.h,{radiation:{scale}},hp),b=new hp.BoardCoupledBridge(bridge,board),hammer=new hp.PolarizedHammer(b,{velocityMps:velocity});
  // Cache the affine board solve: free and forced response are linear in port force.
  const originalIncrement=board.increment.bind(board),unit=originalIncrement(1,true);let cache=null;
  board.increment=(f,responseOnly=false)=>{if(responseOnly)return originalIncrement(f,true);if(!cache)cache=originalIncrement(0);return Float64Array.from(cache,(v,i)=>v+f*unit[i]);};
  const originalStep=board.step.bind(board);board.step=f=>{originalStep(f);cache=null;};
  const trace=modes.map(()=>new Float64Array(n)),v0=new Float64Array(modes.length),e0=hammer.energy();let maxBalance=0,maxIncrease=0,prev=e0,peakForce=0,first=0,last=0,zeroSteps=0,detached=false,detachedAt=null;
  for(let i=0;i<n*factor;i++){
   if(i%factor===0)v0.set(board.v);
   if(!detached){
    const s=hammer.step();peakForce=Math.max(peakForce,s.sum);if(s.sum>1e-9){if(!first)first=i;last=i;zeroSteps=0;}else zeroSteps++;
    // Keep the hammer model through separation; after gap > 2 mm and negative velocity,
    // continue free bridge motion while checking that the retreating hammer never recontacts.
    if(zeroSteps>rate*.002&&hammer.v<0&&hammer.compression().every(d=>d<-.002)){detached=true;detachedAt=i/rate;}
   }else{
    b.step();hammer.x+=hammer.h*hammer.v;hammer.time+=hammer.h;
    if(hammer.compression().some(d=>d>0))throw Error('unexpected recontact');
    const z0=hammer.z.slice();for(let j=0;j<3;j++){const q=hp.relaxMemory(hammer.compression()[j],z0[j],hammer.h,hammer.felt);hammer.z[j]=q.z;hammer.lossJ+=q.lossJ;}
   }
   if(i%factor===factor-1){for(let j=0;j<modes.length;j++)trace[j][Math.floor(i/factor)]=(board.v[j]-v0[j])*outRate;const e=hammer.energy();maxBalance=Math.max(maxBalance,Math.abs(e+b.lossJ+hammer.lossJ-e0));maxIncrease=Math.max(maxIncrease,e-prev);prev=e;}
  }
  const acc=spectra.map(()=>({re:new Float64Array(N),im:new Float64Array(N)}));
  for(let m=0;m<modes.length;m++){const re=new Float64Array(N),im=new Float64Array(N);re.set(trace[m]);fft(re,im);for(let ch=0;ch<2;ch++){const k=spectra[ch][m],u=acc[ch];for(let i=0;i<=bins;i++){const f=i*outRate/N,lp=f<=8000?1:.5*(1+Math.cos(Math.PI*(f-8000)/4000));u.re[i]+=lp*(re[i]*k.re[i]-im[i]*k.im[i]);u.im[i]+=lp*(re[i]*k.im[i]+im[i]*k.re[i]);}}}
  const channels=acc.map(({re,im})=>{for(let i=1;i<=bins&&i<N/2;i++){re[N-i]=re[i];im[N-i]=-im[i];}im[0]=im[N/2]=0;fft(re,im,true);return re.slice(0,n+maxDelay);});
  let peak=0,early=0,tail=0;for(const ch of channels){for(let i=0;i<ch.length;i++){if(!Number.isFinite(ch[i]))throw Error('nonfinite audio');peak=Math.max(peak,Math.abs(ch[i]));if(i<outRate*.1)early+=ch[i]**2;if(i>=outRate*(seconds-.1)&&i<outRate*seconds)tail+=ch[i]**2;}}
  if(maxBalance>1e-9||maxIncrease>1e-9||!detached||peak<=0)throw Error('render invariant '+JSON.stringify({maxBalance,maxIncrease,detached,peak}));
  return {channels,meta:{velocity,scale,rate,outRate,seconds,cut,modes:modes.length,peakPa:peak,earlyRmsPa:Math.sqrt(early/(2*outRate*.1)),tailRmsPa:Math.sqrt(tail/(2*outRate*.1)),maxBalance,maxIncrease,peakForce,contactMs:1000*(last-first+1)/rate,detachedAt,finalEnergyJ:hammer.energy(),boardEnergyJ:board.energy(),radiationLossJ:board.radiationLossJ,structuralLossJ:board.structuralLossJ}};
 }
 return {render,outRate};
}

export function waveBytes(channels,rate,gain){
 const n=channels[0].length,b=new Uint8Array(44+n*4),v=new DataView(b.buffer),str=(i,s)=>{for(let j=0;j<s.length;j++)b[i+j]=s.charCodeAt(j);};
 str(0,"RIFF");v.setUint32(4,b.length-8,true);str(8,"WAVE");str(12,"fmt ");v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,2,true);v.setUint32(24,rate,true);v.setUint32(28,rate*4,true);v.setUint16(32,4,true);v.setUint16(34,16,true);str(36,"data");v.setUint32(40,n*4,true);
 let clipped=0,peak=0;const fade=Math.round(.04*rate);for(let i=0;i<n;i++){const w=i<n-fade?1:.5*(1+Math.cos(Math.PI*(i-(n-fade))/(fade-1)));for(let j=0;j<2;j++){const z=channels[j][i]*gain*w;if(Math.abs(z)>1)clipped++;peak=Math.max(peak,Math.abs(z));v.setInt16(44+i*4+2*j,Math.round(Math.max(-1,Math.min(1,z))*32767),true);}}
 return {bytes:b,clipped,peak};
}

export function base64(b){const alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";let s="";for(let i=0;i<b.length;i+=3){const n=b[i]*65536+(b[i+1]??0)*256+(b[i+2]??0);s+=alphabet[(n>>18)&63]+alphabet[(n>>12)&63]+(i+1<b.length?alphabet[(n>>6)&63]:"=")+(i+2<b.length?alphabet[n&63]:"=");}return s;}
