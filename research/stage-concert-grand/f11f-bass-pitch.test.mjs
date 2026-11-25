import {pitchSpectrum,cents} from './f11f-bass-pitch.mjs';
let n=0;const check=(m,b)=>{if(!b)throw Error(m);n++};
const rate=48000,f=65.40639132514966,B=.00013738165667578992,N=rate*4;
const signal=(shift=0,stiff=true)=>Float64Array.from({length:N},(_,i)=>[1,2,3].reduce((s,h)=>s+.1/h*Math.sin(2*Math.PI*h*f*2**(shift/1200)*(stiff?Math.sqrt((1+B*h*h)/(1+B)):1)*i/rate),0));
for(const shift of [-18,0,12]){
 const x=signal(shift),q=pitchSpectrum([x,x],rate,0,4,f,B);
 check('fundamental '+shift,Math.abs(q.partials[0].peak.centsFromHarmonic-shift)<.1);
 check('stiff partial '+shift,Math.abs(q.partials[2].peak.centsFromStiff-shift)<.1);
 check('dominant '+shift,q.dominant===1);
}
const zero=new Float64Array(N),z=pitchSpectrum([zero,zero],rate,0,4,f,B);
check('silence',z.dominant===null&&z.partials.every(x=>!x.usable));
console.log('F11F_PITCH_TESTS '+n);
