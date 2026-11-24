import {readFileSync} from 'node:fs';
import {solidWire} from '../c3x-physical/c4-wire-consistency.mjs';
import {partialHz,centsRatio,fitPitchFixedB} from '../c3x-physical/c5-dispersion-holdout.mjs';
import {makeDesign,compareReference} from './c4-design.mjs';
const report=JSON.parse(readFileSync(new URL('../c3x-physical/C5_C4_verified_numeric_report.json',import.meta.url),'utf8'));
function runChecks(solidWire,report,helpers){
  const d=makeDesign(solidWire),x=compareReference(report,d,helpers);
  const a=(v,m)=>{if(!v)throw Error(m)},near=(p,q,t)=>Math.abs(p-q)<t;
  const reject=fn=>{let bad=false;try{fn()}catch(e){bad=true}a(bad,'expected rejection')};
  const cases=[
    ['C4 equal-temperament target',()=>a(near(d.f1Hz,440*2**(-9/12),1e-9),'f1')],
    ['mass from geometry',()=>a(near(d.linearDensityKgM,7850*Math.PI*.00096**2/4,1e-15),'mu')],
    ['rigidity from geometry',()=>a(near(d.EI,200e9*Math.PI*.00096**4/64,1e-15),'EI')],
    ['positive tension and impedance',()=>a(d.tensionN>0&&d.transverseImpedanceNsM>0,'positive')],
    ['B in prior descriptive C5 span',()=>a(d.B>.000275619&&d.B<.000310843,'B')],
    ['not mass fitted to pitch',()=>a(makeDesign(solidWire,{f1Hz:262}).linearDensityKgM===d.linearDensityKgM,'mu invariant')],
    ['geometry change recalculates tension',()=>a(makeDesign(solidWire,{diameterM:.001}).tensionN>d.tensionN,'tension')],
    ['impossible tension rejected',()=>reject(()=>makeDesign(solidWire,{lengthM:.001,f1Hz:1}))],
    ['missing or invalid material rejected',()=>reject(()=>makeDesign(solidWire,{densityKgM3:0}))],
    ['C5 identity enforced',()=>reject(()=>compareReference({...report,source_instrument:'Yamaha C3X'},d,helpers))],
    ['same 28 reserved peaks',()=>a(x.count===28&&x.rows.length===8&&x.excluded.length===1,'count')],
    ['retrospective frequency comparison improves each scored window',()=>a(x.improvedWindows===8&&x.designRms<x.legacyRms,'comparison')]
  ];
  for(const [name,fn] of cases){try{fn()}catch(e){throw Error(name+': '+e.message)}}return cases.map(c=>c[0]);
}
const helpers={partialHz,centsRatio,fitPitchFixedB};const passed=runChecks(solidWire,report,helpers);for(const n of passed)console.log('PASS '+n);console.log(`${passed.length}/${passed.length} tests passed`);const design=makeDesign(solidWire);console.log(JSON.stringify({design,comparison:compareReference(report,design,helpers)},null,2));
