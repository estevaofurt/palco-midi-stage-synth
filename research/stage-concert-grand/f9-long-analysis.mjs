// F9.5: fixed-window signal analysis, no DSP or gain adjustment.
export function levelCrossing(values,windowS,drop,hold=2){
 if(!values.length||!Number.isFinite(windowS)||windowS<=0||!Number.isFinite(drop)||drop<=0||!Number.isInteger(hold)||hold<1)throw RangeError('crossing parameters');
 const ref=values[0];if(!(ref>0)||!Number.isFinite(ref))return {status:'no-reference'};
 for(let i=1;i+hold<=values.length;i++){
  if(values.slice(i,i+hold).every(x=>Number.isFinite(x)&&x>=0&&x<=ref*10**(-drop/20)*(1+1e-12)))return {status:'observed-window',startS:i*windowS,endS:(i+1)*windowS,confirmedThroughS:(i+hold)*windowS};
 }
 return {status:'not-observed',analyzedThroughS:values.length*windowS};
}
export function analyzeSustain(channels,rate,fft,{onsetS=0,f1=261.6255653,B=.000296440484,windowS=.5,partials=10,excludeEndS=0}={}){
 if(!Array.isArray(channels)||!channels.length||!Number.isFinite(rate)||rate<8000||!Number.isFinite(onsetS)||onsetS<0||!Number.isFinite(excludeEndS)||excludeEndS<0||!Number.isFinite(f1)||f1<=0||!Number.isFinite(B)||B<0||!Number.isFinite(windowS)||windowS<.25||!Number.isInteger(partials)||partials<1||partials>12||channels.some(c=>c.length!==channels[0].length))throw RangeError('analysis parameters');
 const n=Math.round(windowS*rate),start=Math.round(onsetS*rate),end=channels[0].length-Math.ceil(excludeEndS*rate),count=Math.floor((end-start)/n);if(count<2)throw RangeError('at least two complete windows');
 const dt=n/rate;let N=1;while(N<n)N*=2;
 const w=Float64Array.from({length:n},(_,i)=>.5-.5*Math.cos(2*Math.PI*i/(n-1))),w2=w.reduce((s,x)=>s+x*x,0);
 const bands=Array.from({length:partials},(_,i)=>{const h=i+1,f=h*f1*Math.sqrt((1+B*h*h)/(1+B)),half=Math.max(f*(2**(20/1200)-1),4*rate/N);const lo=Math.max(1,Math.ceil((f-half)*N/rate)),hi=Math.min(N/2-1,Math.floor((f+half)*N/rate));if(hi<lo||f+5*half>=rate/2)throw RangeError('partial band beyond Nyquist');return {h,f,half,lo,hi};});
 const windows=[];
 for(let j=0;j<count;j++){
  const power=new Float64Array(N/2+1);let sum=0;
  for(const c of channels){const re=new Float64Array(N),im=new Float64Array(N);for(let i=0;i<n;i++){const x=c[start+j*n+i];if(!Number.isFinite(x))throw RangeError('nonfinite sample');sum+=x*x;re[i]=x*w[i];}fft(re,im);for(let k=1;k<N/2;k++)power[k]+=2*(re[k]**2+im[k]**2)/(N*w2*channels.length);}
  const levels=bands.map(b=>{let e=0,side=0,ns=0;for(let k=b.lo;k<=b.hi;k++)e+=power[k];const width=b.hi-b.lo+1;for(let k=b.lo-2*width;k<b.lo-width;k++)if(k>0){side+=power[k];ns++;}for(let k=b.hi+width+1;k<=b.hi+2*width;k++)if(k<N/2){side+=power[k];ns++;}const noise=ns?side/ns*width:0;return {rms:Math.sqrt(e),contrastDb:noise>0&&e>0?10*Math.log10(e/noise):null};});
  windows.push({startS:j*dt,endS:(j+1)*dt,rms:Math.sqrt(sum/(n*channels.length)),partials:levels});
 }
 const summary=values=>({referenceRms:values[0],drops:Object.fromEntries([20,40,60].map(d=>[d,levelCrossing(values,dt,d)]))});
 return {method:'nonoverlapping Hann spectral-band energy; channel powers averaged; broadband unweighted RMS; levels relative to first complete window; no noise-floor correction, no standard reverberation T60',rate,onsetS,excludeEndS,windowS:dt,analyzedThroughS:count*dt,discardedFrames:channels[0].length-start-count*n,bands,windows,broadband:summary(windows.map(w=>w.rms)),partialDrops:bands.map((b,i)=>({h:b.h,...summary(windows.map(w=>w.partials[i].rms)),warning:'check sideband contrast and recording noise before interpreting crossings'}))};
}
