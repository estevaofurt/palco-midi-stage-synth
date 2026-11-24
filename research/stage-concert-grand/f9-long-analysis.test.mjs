import {analyzeSustain,levelCrossing} from './f9-long-analysis.mjs';
import {fft} from './f8-render.mjs';
export function runTests(){
 let n=0;const check=(label,ok)=>{if(!ok)throw Error(label);n++;};
 const rate=8192,N=rate*5,f=256,x=Float64Array.from({length:N},(_,i)=>Math.sin(2*Math.PI*f*i/rate)*10**(-Math.floor(i/(rate*.5))*10/20));
 const y=analyzeSustain([x,Float64Array.from(x,v=>-v)],rate,fft,{f1:f,B:0,partials:3});
 check('stereo polarity not cancelled',Math.abs(y.windows[0].rms-Math.SQRT1_2)<1e-10);
 check('partial power',Math.abs(y.windows[0].partials[0].rms-Math.SQRT1_2)<.001);
 check('harmonic isolation',y.windows[0].partials[1].rms<1e-4);
 check('20 dB crossing',y.broadband.drops[20].startS===1);
 check('60 dB crossing confirmed',y.broadband.drops[60].status==='observed-window'&&y.broadband.drops[60].startS===3);
 check('transient crossing rejected',levelCrossing([1,.01,1,.01],.5,20).status==='not-observed');
 check('short signal censored',levelCrossing([1,.8,.7],.5,60).status==='not-observed');
 check('last window not sufficient',levelCrossing([1,.5,.001],.5,60).status==='not-observed');
 check('silence rejected as reference',levelCrossing([0,0],.5,20).status==='no-reference');
 const z=analyzeSustain([Float64Array.from(x,v=>v*.1)],rate,fft,{f1:f,B:0,partials:3});
 check('gain independent',z.broadband.drops[40].startS===y.broadband.drops[40].startS&&Math.abs(z.windows[0].rms/y.windows[0].rms-.1)<1e-10);
 check('complete windows',y.windows.length===10&&y.discardedFrames===0);
 check('exclude editorial fade',analyzeSustain([x],rate,fft,{f1:f,B:0,partials:3,excludeEndS:.04}).windows.length===9);
 let reject=false;try{analyzeSustain([x],rate,fft,{f1:f,B:-1})}catch{reject=true}check('reject unphysical B',reject);
 return n;
}
console.log('F9.5 tests passed:',runTests());
