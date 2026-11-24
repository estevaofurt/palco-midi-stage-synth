// F9.9: 24-bit listening export at the same gain and editorial fade as F8 PCM16.
export function wave24(channels,rate,gain){
 if(!Array.isArray(channels)||channels.length!==2||channels[0].length!==channels[1].length||!Number.isInteger(rate)||rate<8000||rate>384000||!Number.isFinite(gain)||gain<=0)throw RangeError('wave24 options');
 const n=channels[0].length,fade=Math.round(.04*rate);
 if(n<fade||n*6+36>0xffffffff)throw RangeError('wave24 duration');
 const bytes=new Uint8Array(44+n*6),v=new DataView(bytes.buffer),str=(i,s)=>{for(let j=0;j<s.length;j++)bytes[i+j]=s.charCodeAt(j);};
 str(0,'RIFF');v.setUint32(4,bytes.length-8,true);str(8,'WAVE');str(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,2,true);v.setUint32(24,rate,true);v.setUint32(28,rate*6,true);v.setUint16(32,6,true);v.setUint16(34,24,true);str(36,'data');v.setUint32(40,n*6,true);
 let peak=0,clipped=0;
 for(let i=0;i<n;i++){const w=i<n-fade?1:.5*(1+Math.cos(Math.PI*(i-(n-fade))/(fade-1)));for(let ch=0;ch<2;ch++){const x=channels[ch][i]*gain*w;if(!Number.isFinite(x))throw RangeError('nonfinite PCM');peak=Math.max(peak,Math.abs(x));if(Math.abs(x)>1)clipped++;const q=Math.round(Math.max(-1,Math.min(1,x))*8388607),j=44+i*6+ch*3;bytes[j]=q&255;bytes[j+1]=(q>>8)&255;bytes[j+2]=(q>>16)&255;}}
 return {bytes,peak,clipped};
}
