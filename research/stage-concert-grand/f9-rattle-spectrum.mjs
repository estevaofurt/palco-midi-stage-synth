// F9.19: locate persistent off-partial spectral energy in verified C4 WAVs.
// Off-partial is a diagnostic classification, not evidence of mechanical noise.
export function partialCenters(f1,B,limitHz){
 if(![f1,B,limitHz].every(Number.isFinite)||f1<=0||B<0||limitHz<f1)throw RangeError('partial parameters');
 const out=[];
 for(let h=1;h<1000;h++){const f=h*f1*Math.sqrt((1+B*h*h)/(1+B));if(f>limitHz)break;out.push({h,f});}
 return out;
}
export function inspectRattleWindow(channels,rate,fft,{startS=0,endS=.5,f1=261.6255653005986,B=.0002964404840492155,limitHz=6000}={}){
 if(!Array.isArray(channels)||!channels.length||!Number.isFinite(rate)||rate<16000||!Number.isFinite(startS)||!Number.isFinite(endS)||startS<0||endS<=startS||!Number.isFinite(limitHz)||limitHz>=rate/2)throw RangeError('window');
 const start=Math.round(startS*rate),n=Math.round(endS*rate)-start;
 if(n<rate*.25||channels.some(c=>c.length<start+n))throw RangeError('samples');
 let N=1;while(N<n)N*=2;
 const w=Float64Array.from({length:n},(_,i)=>.5-.5*Math.cos(2*Math.PI*i/(n-1))),w2=w.reduce((s,x)=>s+x*x,0),p=new Float64Array(N/2+1);
 for(const c of channels){
  const re=new Float64Array(N),im=new Float64Array(N);
  for(let i=0;i<n;i++){const x=c[start+i];if(!Number.isFinite(x))throw Error('nonfinite sample');re[i]=x*w[i];}
  fft(re,im);for(let k=1;k<N/2;k++)p[k]+=2*(re[k]**2+im[k]**2)/(N*w2*channels.length);
 }
 const centers=partialCenters(f1,B,limitHz*1.1),df=rate/N,k0=Math.ceil(30/df),k1=Math.floor(limitHz/df);
 const nearest=f=>centers.reduce((a,b)=>Math.abs(f-b.f)<Math.abs(f-a.f)?b:a);
 const inside=(f,c,wide)=>Math.abs(f-c.f)<=Math.max(wide?12:6,df*(wide?5:3),c.f*(wide?.008:.004));
 let total=0,narrowOff=0,wideOff=0,max=0;const peaks=[];
 for(let k=k0;k<=k1;k++){
  const f=k*df,c=nearest(f),power=p[k];total+=power;max=Math.max(max,power);
  if(!inside(f,c,false))narrowOff+=power;
  if(!inside(f,c,true)){wideOff+=power;if(p[k]>0&&p[k]>p[k-1]&&p[k]>=p[k+1])peaks.push({frequencyHz:f,nearestPartial:c.h,partialHz:c.f,offsetHz:f-c.f,power});}
 }
 if(!(total>0&&max>0))throw Error('silent analysis band');
 return {startS,endS,binHz:df,analysisBandHz:[30,limitHz],rmsBand:Math.sqrt(total),narrowOffFraction:narrowOff/total,wideOffFraction:wideOff/total,offPeaks:peaks.sort((a,b)=>b.power-a.power).slice(0,8).map(q=>({...q,relativeToMaxBinDb:10*Math.log10(q.power/max)}))};
}
