// Research measurement only: compare ideal pre-export floating signal to PCM16, excluding editorial fade.
export function compareQuantization(channels,pcm,rate,{gain=.36767023440034063,windowS=.5,excludeEndS=.04}={}){
 if(!Array.isArray(channels)||!channels.length||!Array.isArray(pcm)||pcm.length!==channels.length||!Number.isFinite(rate)||rate<=0||!Number.isFinite(gain)||gain<=0||!Number.isFinite(windowS)||windowS<=0||!Number.isFinite(excludeEndS)||excludeEndS<0)throw RangeError('audit options');
 const n=channels[0].length,step=Math.round(windowS*rate),end=n-Math.ceil(excludeEndS*rate);
 if(step<1||end<step||channels.some((x,i)=>x.length!==n||pcm[i].length!==n))throw RangeError('audit dimensions');
 const out=[];
 for(let s=0;s+step<=end;s+=step){
  let energy=0,quant=0,error=0,zero=0,peak=0,clipped=0;
  for(let ch=0;ch<channels.length;ch++)for(let i=s;i<s+step;i++){
   const x=channels[ch][i]*gain,z=pcm[ch][i];if(!Number.isFinite(x)||!Number.isInteger(z)||z<-32768||z>32767)throw RangeError('invalid sample');
   const y=z/32767;energy+=x*x;quant+=y*y;error+=(x-y)**2;zero+=+(z===0);peak=Math.max(peak,Math.abs(x));clipped+=+(Math.abs(x)>1);
  }
  const den=step*channels.length,db=x=>x>0?20*Math.log10(x):null,rms=Math.sqrt(energy/den),pcmRms=Math.sqrt(quant/den),errorRms=Math.sqrt(error/den);
  out.push({startS:s/rate,endS:(s+step)/rate,floatRms:rms,pcmRms,errorRms,floatDbFS:db(rms),pcmDbFS:db(pcmRms),quantizationSnrDb:errorRms>0&&rms>0?db(rms/errorRms):null,zeroFraction:zero/den,peak,clipped});
 }
 return {gain,rate,windowS:step/rate,excludeEndS,analyzedThroughS:out.at(-1).endS,windows:out,method:'same-signal error vs PCM16 /32767, no dither, no noise-floor correction; zero samples do not imply inaudibility'};
}
export function decodePcmChannels(bytes,parsePcm16){
 const q=parsePcm16(bytes),v=new DataView(q.data.buffer,q.data.byteOffset,q.data.byteLength);
 return {rate:q.rate,channels:Array.from({length:q.channels},(_,ch)=>Int16Array.from({length:q.frames},(_,i)=>v.getInt16(2*(i*q.channels+ch),true)))};
}
