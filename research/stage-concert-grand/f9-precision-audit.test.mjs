import {compareQuantization,decodePcmChannels} from './f9-precision-audit.mjs';
import {waveBytes} from './f8-render.mjs';
import {parsePcm16} from './f9-decay-analysis.mjs';
export function checks(){
 let count=0;const check=(m,v)=>{if(!v)throw Error(m);count++;};const rate=8000;
 const x=Float64Array.from({length:rate*3},(_,i)=>Math.sin(2*Math.PI*250*i/rate)*[.1,.00001,.000001][Math.floor(i/rate)]);
 const channels=[x,x],wav=waveBytes(channels,rate,1),q=decodePcmChannels(wav.bytes,parsePcm16);
 const a=compareQuantization(channels,q.channels,q.rate,{gain:1,windowS:1,excludeEndS:0});
 check('PCM format',q.rate===rate&&q.channels.length===2&&q.channels[0].length===x.length);
 check('initial high fidelity',a.windows[0].quantizationSnrDb>70);
 check('quiet tail erased by quantization',a.windows[1].zeroFraction===1&&a.windows[1].floatRms>0&&a.windows[1].pcmRms===0);
 check('quiet tail zero SNR',Math.abs(a.windows[1].quantizationSnrDb)<1e-12);
 check('exclude editorial fade',compareQuantization(channels,q.channels,rate,{gain:1,windowS:1}).windows.length===2);
 check('no clipping',a.windows.every(w=>w.clipped===0));
 check('error finite',a.windows.every(w=>Number.isFinite(w.errorRms)));
 let rejected=false;try{compareQuantization(channels,[new Int16Array(2),new Int16Array(2)],rate)}catch{rejected=true}check('reject mismatched length',rejected);
 return count;
}
console.log('Precision audit tests passed:',checks());
