import {solidWire,auditV10C4} from './c4-wire-consistency.mjs';
function comparePublishedWire(solidWire,auditV10C4){
  // Röslau Blue Label, nominal neighboring gauge weights, not measurements of a C3X.
  const rows=[{diameterMm:1.025,massGm:6.47},{diameterMm:1.050,massGm:6.79}];
  const a=auditV10C4();
  const points=rows.map(p=>({...p,impliedDensityKgM3:p.massGm/1000/(Math.PI*(p.diameterMm/1000)**2/4)}));
  const t=(a.base.diameterM*1000-rows[0].diameterMm)/(rows[1].diameterMm-rows[0].diameterMm);
  const interpolatedGm=rows[0].massGm+t*(rows[1].massGm-rows[0].massGm);
  // INRIA RT-0425 appendix A and B model tables, C4 only. E is the Stage hypothesis,
  // not inferred as a measured material modulus from that report.
  const variants=[{label:'appendix A',diameterM:.001006,tensionN:741},{label:'appendix B',diameterM:.001064,tensionN:829}].map(p=>({...p,...solidWire({...p,lengthM:.657,youngPa:200e9,densityKgM3:7850})}));
  return {scope:'manufacturer nominal wire and published simulation inputs; neither identifies C3X',points,interpolatedGm,excessPct:100*(a.v10Mu*1000/interpolatedGm-1),variants};
}
function checks(solidWire,auditV10C4){
  const x=comparePublishedWire(solidWire,auditV10C4),a=auditV10C4();
  const assert=(v,m)=>{if(!v)throw Error(m)};
  const cases=[
    ['catalog brackets V10 diameter',()=>assert(a.base.diameterM*1000>1.025&&a.base.diameterM*1000<1.05,'bracket')],
    ['nominal catalog masses consistent with steel density',()=>assert(x.points.every(p=>Math.abs(p.impliedDensityKgM3-7850)<15),'density')],
    ['interpolation within endpoints',()=>assert(x.interpolatedGm>6.47&&x.interpolatedGm<6.79,'interp')],
    ['catalog confirms mass discrepancy',()=>assert(x.excessPct>30&&x.excessPct<33,'gap')],
    ['two published model variants remain distinct',()=>assert(x.variants[0].diameterM!==x.variants[1].diameterM&&x.variants[0].B!==x.variants[1].B,'variant')],
    ['published model variants give near-C4 frequencies in simplified equation',()=>assert(x.variants.every(p=>Math.abs(p.f1Hz-262.22)<1),'f1')]
  ];
  for(const [n,f] of cases)f();
  return cases.map(c=>c[0]);
}
const passed=checks(solidWire,auditV10C4);for(const n of passed)console.log('PASS '+n);console.log(`${passed.length}/${passed.length} passed`);console.log(JSON.stringify(comparePublishedWire(solidWire,auditV10C4),null,2));
