import {fft} from './f8-render.mjs';
export const cents=(f,ref)=>1200*Math.log2(f/ref);
export function pitchSpectrum(channels,rate,startS,endS,f1,B){
 const n=Math.round((endS-startS)*rate),offset=Math.round(startS*rate);
 if(!Number.isInteger(rate)||rate<8000||n<rate/2||offset<0||channels.length!==2||channels.some(c=>c.length<offset+n)||!(f1>0)||!Number.isFinite(B)||B<0)throw Error('pitch window');
 let N=1;while(N<4*n)N*=2;
 const power=new Float64Array(N/2+1),binHz=rate/N;
 let sq=0,ws=0;const win=Float64Array.from({length:n},(_,i)=>.5-.5*Math.cos(2*Math.PI*i/(n-1)));ws=win.reduce((a,b)=>a+b,0);
 for(const c of channels){const re=new Float64Array(N),im=new Float64Array(N);for(let i=0;i<n;i++){const x=c[offset+i];if(!Number.isFinite(x))throw Error('sample');sq+=x*x;re[i]=x*win[i];}fft(re,im);for(let k=1;k<N/2;k++)power[k]+=(re[k]**2+im[k]**2)*2/(ws*ws);}
 const partials=[];
 for(let h=1;h<=8;h++){
  const ideal=h*f1,expected=ideal*Math.sqrt((1+B*h*h)/(1+B)),lo=Math.max(2,Math.floor(expected*2**(-150/1200)/binHz)),hi=Math.min(N/2-2,Math.ceil(expected*2**(150/1200)/binHz));
  let peaks=[];
  for(let k=lo;k<=hi;k++)if(power[k]>0&&power[k]>=power[k-1]&&power[k]>power[k+1]){
   const a=Math.log(Math.max(power[k-1],1e-300)),b=Math.log(power[k]),c=Math.log(Math.max(power[k+1],1e-300)),d=.5*(a-c)/(a-2*b+c),hz=(k+Math.max(-.5,Math.min(.5,d)))*binHz;
   peaks.push({hz,db:10*Math.log10(power[k]),centsFromHarmonic:cents(hz,ideal),centsFromStiff:cents(hz,expected)});
  }
  peaks.sort((a,b)=>b.db-a.db);
  const strongest=peaks[0]??null;
  partials.push({h,expectedHz:expected,stiffnessCents:cents(expected,ideal),peak:strongest,otherPeaks:peaks.slice(1).filter(p=>p.db>=strongest.db-25&&Math.abs(p.hz-strongest.hz)>=2/(endS-startS)).slice(0,3)});
 }
 const top=Math.max(...partials.map(p=>p.peak?.db??-Infinity));
 for(const p of partials)p.usable=!!p.peak&&p.peak.db>=Math.max(-95,top-40);
 const dominant=partials.filter(p=>p.usable).sort((a,b)=>b.peak.db-a.peak.db)[0]?.h??null;
 return {startS,endS,rms:Math.sqrt(sq/(2*n)),binHz,windowResolutionHz:1/(endS-startS),dominant,partials};
}
