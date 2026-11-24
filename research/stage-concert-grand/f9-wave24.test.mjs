import {wave24} from './f9-wave24.mjs';
import {waveBytes} from './f8-render.mjs';
export function checks(){
 let count=0;const check=(m,v)=>{if(!v)throw Error(m);count++;};const rate=8000,n=rate,x=Float64Array.from({length:n},(_,i)=>i===0?-.25:i===1?.25:1e-6),y=Float64Array.from(x,v=>-v),a=wave24([x,y],rate,1),b=waveBytes([x,y],rate,1),v=new DataView(a.bytes.buffer),q=(i,ch)=>{const j=44+i*6+ch*3;return ((a.bytes[j]|a.bytes[j+1]<<8|a.bytes[j+2]<<16)<<8)>>8;};
 check('RIFF PCM 24-bit stereo',String.fromCharCode(...a.bytes.slice(0,4))==='RIFF'&&v.getUint16(20,true)===1&&v.getUint16(22,true)===2&&v.getUint16(34,true)===24);
 check('sizes and rate',v.getUint32(4,true)===a.bytes.length-8&&v.getUint32(40,true)===n*6&&v.getUint32(28,true)===rate*6&&v.getUint16(32,true)===6);
 check('signed negative and positive samples',q(0,0)===Math.round(-.25*8388607)&&q(0,1)===Math.round(.25*8388607));
 check('quiet tail retained',q(2,0)!==0&&q(2,1)!==0);
 check('same peak and clipping as PCM16',a.peak===b.peak&&a.clipped===b.clipped&&a.clipped===0);
 check('last frame fade zero',q(n-1,0)===0&&q(n-1,1)===0);
 check('clipping reported',wave24([x,y],rate,5).clipped===4);
 let bad=false;try{wave24([x,y.subarray(1)],rate,1)}catch{bad=true;}check('mismatched channels rejected',bad);
 return count;
}
console.log('F9.9 PCM24 tests passed:',checks());
