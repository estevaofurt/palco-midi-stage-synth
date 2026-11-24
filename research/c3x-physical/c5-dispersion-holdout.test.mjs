import {readFileSync} from 'node:fs';
import {fitStiffString} from './c5-b-sensitivity.mjs';
import {partialHz,centsRatio,fitPitchFixedB,evaluateDispersion} from './c5-dispersion-holdout.mjs';
const report=JSON.parse(readFileSync(new URL('./C5_C4_verified_numeric_report.json',import.meta.url),'utf8'));
function tests(fit,report){
  const a=(v,m)=>{if(!v)throw Error(m);},near=(x,y,t)=>Math.abs(x-y)<t;
  const reject=fn=>{let failed=false;try{fn()}catch(e){failed=true}a(failed,'expected rejection');};
  const b=.0003,f=261.6,p=[2,3,4,5,6,7,8].map(n=>({n,freq_hz:partialHz(n,f,b)}));
  const cases=[
    ['first partial invariant',()=>a(partialHz(1,f,b)===f,'f1')],
    ['ideal string',()=>a(partialHz(8,f,0)===8*f,'ideal')],
    ['rigidity raises upper partials',()=>a(partialHz(8,f,.0005)>partialHz(8,f,b),'B')],
    ['pitch scales all frequencies',()=>a(near(centsRatio(partialHz(8,f*2,b),partialHz(8,f,b)),1200,1e-9),'pitch')],
    ['same pitch different B changes partial ratios',()=>a(centsRatio(partialHz(8,f,.0005),partialHz(8,f,b))>centsRatio(partialHz(2,f,.0005),partialHz(2,f,b)),'shape')],
    ['recover pitch at known B',()=>a(near(fitPitchFixedB(p,b),f,1e-9),'fit')],
    ['wrong B cannot fit every partial by tuning',()=>{const q=fitPitchFixedB(p,.0005);a(Math.abs(centsRatio(partialHz(8,q,.0005),p[6].freq_hz))>1,'wrong B');}],
    ['invalid partial and B rejected',()=>{reject(()=>partialHz(0,f,b));reject(()=>partialHz(1,f,-1));reject(()=>partialHz(1,NaN,b));}],
    ['duplicate peaks rejected',()=>reject(()=>fitPitchFixedB([p[0],p[0]],b))],
    ['invalid measured peaks rejected',()=>reject(()=>fitPitchFixedB([{n:2,freq_hz:0},p[1]],b))],
    ['archived windows disjoint by partial',()=>a(evaluateDispersion(report,fit).rows.every(r=>r.train.every(n=>n<=8)&&r.hold.every(n=>n>=9)),'split')],
    ['eight scored windows and one excluded',()=>{const x=evaluateDispersion(report,fit);a(x.rows.length===8&&x.excluded.length===1&&x.excluded[0].layer==='v1','count');}],
    ['C3X substitution rejected',()=>reject(()=>evaluateDispersion({...report,source_instrument:'Yamaha C3X'},fit))],
    ['V10 tuning correction preserves EI relation',()=>{const x=evaluateDispersion(report,fit);a(near(x.fixedB*(1-x.baseB),x.baseB,1e-15),'EI');}],
    ['held-out scores finite and 28 peaks',()=>{const x=evaluateDispersion(report,fit);a(Number.isFinite(x.freeRmsCents)&&Number.isFinite(x.fixedRmsCents)&&x.holdoutCount===28,'rms');}]
  ];for(const [name,fn] of cases){try{fn()}catch(e){throw Error(name+': '+e.message)}}return cases.map(c=>c[0]);
}
const passed=tests(fitStiffString,report);for(const name of passed)console.log('PASS '+name);console.log(`${passed.length}/${passed.length} tests passed`);console.log(JSON.stringify(evaluateDispersion(report,fitStiffString),null,2));
