import {decaySummary,parsePcm16,excerptPcm16,pcmWindows} from './f9-decay-analysis.mjs';
export function runTests(){
 let passed=0;const check=(name,fn)=>{if(!fn())throw Error(name);passed++;};const near=(a,b,e=1e-10)=>Math.abs(a-b)<e;const rejects=fn=>{try{fn();return false}catch{return true}};
 const e=decaySummary([1,.1,.01,.001,.0001,.00001]);
 check('exponential slope',()=>near(e.early.dbPerSecond,-20)&&near(e.late.dbPerSecond,-20)&&near(e.early.rSquared,1));
 check('gain invariance',()=>near(decaySummary([2,.2,.02]).early.dbPerSecond,e.early.dbPerSecond));
 check('constant signal',()=>decaySummary([1,1,1]).early.rSquared===null);
 check('nonmonotonic',()=>!decaySummary([1,.2,.3]).monotonic);
 check('invalid windows',()=>rejects(()=>decaySummary([1,0]))&&rejects(()=>decaySummary([1,NaN])));
 check('half-second spacing',()=>near(decaySummary([1,.1,.01],.5).early.dbPerSecond,-40));
 // PCM16 stereo fixture: 6 seconds at 4 Hz, alternating signs with a constant amplitude per second.
 const b=new Uint8Array(44+6*4*4),v=new DataView(b.buffer),s=(o,t)=>{for(let i=0;i<t.length;i++)b[o+i]=t.charCodeAt(i)};
 s(0,'RIFF');v.setUint32(4,b.length-8,true);s(8,'WAVE');s(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,2,true);v.setUint32(24,4,true);v.setUint32(28,16,true);v.setUint16(32,4,true);v.setUint16(34,16,true);s(36,'data');v.setUint32(40,b.length-44,true);
 for(let i=0;i<48;i++)v.setInt16(44+2*i,(i%2?-1:1)*8192/(1+Math.floor(i/8)),true);
 check('PCM parse',()=>parsePcm16(b).frames===24&&parsePcm16(b).channels===2);
 const cut=excerptPcm16(b,5);
 check('five-second exact PCM',()=>parsePcm16(cut).frames===20&&cut.length===124&&cut.subarray(44).every((x,i)=>x===b[44+i]));
 check('stereo energy not mono cancellation',()=>near(pcmWindows(b).rms[0],.25));
 check('reject duration and truncation',()=>rejects(()=>excerptPcm16(b,7))&&rejects(()=>parsePcm16(b.subarray(0,-1))));
 check('reject non-PCM16',()=>{const a=b.slice();new DataView(a.buffer).setUint16(34,24,true);return rejects(()=>parsePcm16(a));});
 const partial=excerptPcm16(b,5.5);
 check('exclude incomplete window',()=>pcmWindows(partial).rms.length===5&&pcmWindows(partial).discardedFrames===2);
 return passed;
}
console.log('F9.3 tests passed:',runTests());
