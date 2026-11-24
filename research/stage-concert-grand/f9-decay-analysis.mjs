// F9.3: analysis and lossless PCM excerpt only. No DSP changes.
export function decaySummary(rms,secondsPerWindow=1){
 if(!Array.isArray(rms)||rms.length<2||!Number.isFinite(secondsPerWindow)||secondsPerWindow<=0||rms.some(x=>!Number.isFinite(x)||x<=0))throw new RangeError('positive RMS windows required');
 const points=rms.map((x,i)=>({startS:i*secondsPerWindow,endS:(i+1)*secondsPerWindow,rms:x,relativeDb:20*(Math.log10(x)-Math.log10(rms[0]))}));
 function fit(first,last){
  const p=points.slice(first,last+1),t=p.map(q=>(q.startS+q.endS)/2),y=p.map(q=>q.relativeDb),mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
  const tx=mean(t),yx=mean(y),xx=t.reduce((s,x)=>s+(x-tx)**2,0),xy=t.reduce((s,x,i)=>s+(x-tx)*(y[i]-yx),0),yy=y.reduce((s,x)=>s+(x-yx)**2,0);
  return {startS:p[0].startS,endS:p.at(-1).endS,dbPerSecond:xy/xx,rSquared:yy===0?null:Math.max(0,Math.min(1,xy**2/(xx*yy)))};
 }
 return {points,early:fit(0,Math.min(2,rms.length-1)),late:rms.length>=6?fit(3,rms.length-1):null,monotonic:points.every((p,i)=>i===0||p.rms<=points[i-1].rms)};
}
function tag(b,o){return String.fromCharCode(...b.subarray(o,o+4))}
export function parsePcm16(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.length<44)throw new RangeError('WAV bytes');
 const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
 if(tag(bytes,0)!=='RIFF'||tag(bytes,8)!=='WAVE'||v.getUint32(4,true)+8!==bytes.length)throw new Error('RIFF/WAVE size');
 let fmt=null,data=null;
 for(let i=12;i<bytes.length;){
  if(i+8>bytes.length)throw new Error('truncated chunk');
  const name=tag(bytes,i),n=v.getUint32(i+4,true),p=i+8,end=p+n;
  if(end+(n&1)>bytes.length)throw new Error('chunk bounds');
  if(name==='fmt '){
   if(fmt||n<16||v.getUint16(p,true)!==1||v.getUint16(p+14,true)!==16)throw new Error('PCM16 only');
   const channels=v.getUint16(p+2,true),rate=v.getUint32(p+4,true),align=v.getUint16(p+12,true);
   if(!channels||!rate||align!==2*channels||v.getUint32(p+8,true)!==rate*align)throw new Error('PCM format');
   fmt={channels,rate,align};
  }
  if(name==='data'){if(data)throw new Error('duplicate data');data=bytes.subarray(p,end);}
  i=end+(n&1);
 }
 if(!fmt||!data||!data.length||data.length%fmt.align)throw new Error('missing or incomplete PCM');
 return {...fmt,data,frames:data.length/fmt.align};
}
export function excerptPcm16(bytes,seconds=5){
 const q=parsePcm16(bytes),frames=seconds*q.rate;
 if(!Number.isSafeInteger(frames)||frames<=0||frames>q.frames)throw new RangeError('excerpt duration');
 const n=frames*q.align,out=new Uint8Array(44+n),v=new DataView(out.buffer),put=(o,s)=>{for(let i=0;i<s.length;i++)out[o+i]=s.charCodeAt(i)};
 put(0,'RIFF');v.setUint32(4,36+n,true);put(8,'WAVE');put(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,q.channels,true);v.setUint32(24,q.rate,true);v.setUint32(28,q.rate*q.align,true);v.setUint16(32,q.align,true);v.setUint16(34,16,true);put(36,'data');v.setUint32(40,n,true);out.set(q.data.subarray(0,n),44);
 return out;
}
export function pcmWindows(bytes,seconds=1){
 const q=parsePcm16(bytes),n=seconds*q.rate;
 if(!Number.isSafeInteger(n)||n<1)throw new RangeError('window duration');
 const v=new DataView(q.data.buffer,q.data.byteOffset,q.data.byteLength),rms=[];
 for(let start=0;start+n<=q.frames;start+=n){let sum=0;for(let i=start*q.channels;i<(start+n)*q.channels;i++){const x=v.getInt16(i*2,true)/32768;sum+=x*x;}rms.push(Math.sqrt(sum/(n*q.channels)));}
 return {rms,secondsPerWindow:seconds,discardedFrames:q.frames% n};
}
