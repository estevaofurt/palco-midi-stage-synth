import {readFileSync} from 'node:fs';
import {fitStiffString,auditC5Report} from './c5-b-sensitivity.mjs';
const report=JSON.parse(readFileSync(new URL('./C5_C4_verified_numeric_report.json',import.meta.url),'utf8'));
function runTests(fit,audit,report){
  const a=(x,m)=>{if(!x)throw Error(m)};
  const near=(x,y,t)=>Math.abs(x-y)<=t;
  const peaks=(B,f0=261.5)=>[2,3,4,5,6,7,8].map(n=>({n,freq_hz:n*f0*Math.sqrt(1+B*n*n)}));
  const rejects=(fn)=>{let x=false;try{fn()}catch(e){x=true}a(x,'should reject')};
  const cases=[
    ['exact B recovery',()=>a(near(fit(peaks(.0003)).B,.0003,1e-12),'B')],
    ['fundamental convention',()=>a(near(fit(peaks(.0003)).f1Hz,261.5*Math.sqrt(1.0003),1e-9),'f1')],
    ['exact fit residual',()=>a(fit(peaks(.0003)).residualHzRms<1e-9,'residual')],
    ['frequency scale invariance',()=>a(near(fit(peaks(.0003,440)).B,.0003,1e-12),'scale')],
    ['order invariance',()=>a(near(fit(peaks(.0003).reverse()).B,.0003,1e-12),'order')],
    ['outlier changes fit',()=>{const p=peaks(.0003);p[6].freq_hz+=3;a(Math.abs(fit(p).B-.0003)>1e-5,'outlier')}],
    ['too few partials',()=>rejects(()=>fit(peaks(.0003).slice(0,3)))],
    ['duplicates rejected',()=>rejects(()=>fit([...peaks(.0003),peaks(.0003)[0]]))],
    ['nonfinite rejected',()=>rejects(()=>fit([...peaks(.0003).slice(0,6),{n:8,freq_hz:NaN}]))],
    ['negative stiffness rejected',()=>rejects(()=>fit(peaks(-.0003)))],
    ['all nine archived C5 windows',()=>a(audit(report).results.length===9,'windows')],
    ['source identity enforced',()=>rejects(()=>audit({...report,source_instrument:'Yamaha C3X'}))],
    ['no fake C3X acceptance',()=>rejects(()=>audit({...report,commercial_c3x_calibration_approved:true}))],
    ['holdout bounds finite',()=>a(audit(report).results.every(x=>x.looMinB>0&&x.looMaxB>=x.looMinB&&x.residualHzRms>=0),'bounds')]
  ];for(const [name,fn] of cases){fn();}return cases.map(c=>c[0]);
}
const tests=runTests(fitStiffString,auditC5Report,report);
for(const t of tests)console.log('PASS '+t);
console.log(`${tests.length}/${tests.length} tests passed`);
console.log(JSON.stringify(auditC5Report(report),null,2));
