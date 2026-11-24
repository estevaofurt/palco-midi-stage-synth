// Strict audit of the canonical stereo PCM exports used by the research renderer.
export function inspectPair(a,b){
 const parse=(bytes,bits)=>{
  const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),tag=i=>String.fromCharCode(...bytes.subarray(i,i+4)),align=bits/4;
  if(bytes.length<44||tag(0)!=='RIFF'||tag(8)!=='WAVE'||tag(12)!=='fmt '||tag(36)!=='data'||v.getUint32(4,true)!==bytes.length-8||v.getUint32(16,true)!==16||v.getUint16(20,true)!==1||v.getUint16(22,true)!==2||v.getUint32(24,true)!==48000||v.getUint16(32,true)!==align||v.getUint32(28,true)!==48000*align||v.getUint16(34,true)!==bits||v.getUint32(40,true)!==bytes.length-44||(bytes.length-44)%align)throw Error('unexpected canonical WAV');
  const samples=(bytes.length-44)/(bits/8),sample=i=>{const j=44+i*(bits/8);return bits===16?v.getInt16(j,true)/32767:((bytes[j]|bytes[j+1]<<8|bytes[j+2]<<16)<<8>>8)/8388607;};
  return {samples,sample};
 };
 const x=parse(a,16),y=parse(b,24);if(x.samples!==y.samples||x.samples<48000)throw Error('PCM length mismatch');
 let rms16=0,rms24=0,peak16=0,peak24=0,maxPairError=0;
 for(let i=0;i<x.samples;i++){const u=x.sample(i),v=y.sample(i);if(Math.abs(u)>1||Math.abs(v)>1)throw Error('PCM range');if(i<48000){rms16+=u*u;rms24+=v*v;}peak16=Math.max(peak16,Math.abs(u));peak24=Math.max(peak24,Math.abs(v));maxPairError=Math.max(maxPairError,Math.abs(u-v));}
 if(maxPairError>.5/32767+.5/8388607+1e-12)throw Error('PCM versions are not the same quantized signal');
 return {frames:x.samples/2,rate:48000,rms16:Math.sqrt(rms16/48000),rms24:Math.sqrt(rms24/48000),peak16,peak24,maxPairError};
}
