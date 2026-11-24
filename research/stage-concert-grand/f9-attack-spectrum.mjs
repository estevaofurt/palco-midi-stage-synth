// Shape-only spectral comparison of a fixed, early time window. No audio modification.
export function attackSpectrum(channels,rate,fft,{startS=0,endS=.1}={}){
 if(!Array.isArray(channels)||!channels.length||!Number.isFinite(rate)||rate<24000||!Number.isFinite(startS)||!Number.isFinite(endS)||startS<0||endS<=startS)throw RangeError('attack window');
 const start=Math.round(startS*rate),n=Math.round(endS*rate)-start;if(n<4||channels.some(c=>c.length<start+n))throw RangeError('attack samples');
 let N=1;while(N<n)N*=2;
 const power=new Float64Array(N/2+1);let w2=0,rms2=0;
 const w=Float64Array.from({length:n},(_,i)=>.5-.5*Math.cos(2*Math.PI*i/(n-1)));
 for(const x of w)w2+=x*x;
 for(const c of channels){
  const re=new Float64Array(N),im=new Float64Array(N);
  for(let i=0;i<n;i++){const x=c[start+i];if(!Number.isFinite(x))throw Error('nonfinite PCM');re[i]=x*w[i];rms2+=x*x;}
  fft(re,im);
  for(let k=1;k<N/2;k++)power[k]+=2*(re[k]**2+im[k]**2)/(N*w2*channels.length);
 }
 const edges=[0,1000,3000,6000,12000],bands=edges.slice(0,-1).map((lo,i)=>({loHz:lo,hiHz:edges[i+1],energy:0}));let energy=0,weighted=0;
 for(let k=1;k<N/2;k++){const f=k*rate/N;if(f>=12000)break;const p=power[k];energy+=p;weighted+=f*p;bands.find(b=>f>=b.loHz&&f<b.hiHz).energy+=p;}
 if(!(energy>0))throw Error('silent attack');
 return {startS,endS,rms:Math.sqrt(rms2/(n*channels.length)),centroidHz:weighted/energy,bands:bands.map(b=>({...b,fraction:b.energy/energy})),upperFraction:bands.slice(1).reduce((a,b)=>a+b.energy,0)/energy};
}
export function decodeCanonical24(bytes){
 const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),tag=i=>String.fromCharCode(...bytes.subarray(i,i+4));
 if(bytes.length<44||tag(0)!=='RIFF'||tag(8)!=='WAVE'||tag(12)!=='fmt '||tag(36)!=='data'||v.getUint32(4,true)!==bytes.length-8||v.getUint32(16,true)!==16||v.getUint16(20,true)!==1||v.getUint16(22,true)!==2||v.getUint32(24,true)!==48000||v.getUint16(34,true)!==24||v.getUint16(32,true)!==6||v.getUint32(28,true)!==288000||v.getUint32(40,true)!==bytes.length-44||(bytes.length-44)%6)throw Error('canonical stereo PCM24 required');
 const frames=(bytes.length-44)/6;
 return [0,1].map(ch=>Float64Array.from({length:frames},(_,i)=>{const j=44+i*6+ch*3;return ((bytes[j]|bytes[j+1]<<8|bytes[j+2]<<16)<<8>>8)/8388607;}));
}
