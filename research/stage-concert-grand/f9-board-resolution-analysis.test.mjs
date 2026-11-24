import {compareResolutions} from './f9-board-resolution-analysis.mjs';
let n=0;const check=(m,b)=>{if(!b)throw Error(m);n++;};
const mk=(resolution,g=1)=>({resolution,windows:[0,.5,1].map(startS=>({startS,endS:startS+.5,rms:g,partials:Array.from({length:10},()=>({rms:g,contrastDb:30}))}))});
const a=mk('a'),b=mk('b',2);let q=compareResolutions(a,b);
check('known 6dB change',Math.abs(q.global.meanAbsDb-20*Math.log10(2))<1e-12&&q.byPartial.every(x=>x.count===3));
q=compareResolutions(a,a);check('identity zero',q.global.maxAbsDb===0&&q.byPartial.every(x=>x.maxAbsDb===0));
b.windows[1].partials[8].contrastDb=10;q=compareResolutions(a,b);check('censor low contrast',q.byPartial[8].count===2&&q.windows[1].partials[8].deltaDb===null);
let rejected=false;try{compareResolutions(a,{...b,windows:b.windows.slice(1)})}catch{rejected=true;}check('mismatched length rejected',rejected);
console.log('F9.16b analysis tests passed:',n);
