// Concatenate canonical stereo PCM24 clips with exact zero gaps.
// Preserve sample bytes; no gain, crossfade, or overlapping strikes.
function parse(b){
 const v=new DataView(b.buffer,b.byteOffset,b.byteLength),tag=i=>String.fromCharCode(...b.subarray(i,i+4));
 if(b.length<44||tag(0)!=='RIFF'||tag(8)!=='WAVE'||tag(12)!=='fmt '||tag(36)!=='data'||v.getUint32(4,true)!==b.length-8||v.getUint32(16,true)!==16||v.getUint16(20,true)!==1||v.getUint16(22,true)!==2||v.getUint32(24,true)!==48000||v.getUint32(28,true)!==288000||v.getUint16(32,true)!==6||v.getUint16(34,true)!==24||v.getUint32(40,true)!==b.length-44||(b.length-44)%6||b.length===44)throw Error('canonical stereo PCM24 required');
 return b.subarray(44);
}
export function concatenate24(clips,gapFrames=24000){
 if(!Array.isArray(clips)||!clips.length||!Number.isSafeInteger(gapFrames)||gapFrames<0)throw RangeError('clips or gap');
 const data=clips.map(parse),n=data.reduce((s,b)=>s+b.length,0)+(clips.length-1)*gapFrames*6;
 if(n+36>0xffffffff)throw RangeError('RIFF limit');
 const out=new Uint8Array(44+n),v=new DataView(out.buffer);out.set(clips[0].subarray(0,44));v.setUint32(4,n+36,true);v.setUint32(40,n,true);
 let offset=44;const placements=[];
 for(const b of data){placements.push({startFrame:(offset-44)/6,frames:b.length/6});out.set(b,offset);offset+=b.length+gapFrames*6;}
 return {bytes:out,placements,frames:n/6};
}
