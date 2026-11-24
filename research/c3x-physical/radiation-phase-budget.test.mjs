import { auditPhaseBudget } from './radiation-phase-budget.mjs';
function runPhaseBudgetTests(audit) {
  const base={frequencyHz:1308.1278265,sampleRateHz:48000,speedOfSoundMps:343,maxPhaseErrorDeg:5,elapsedSeconds:2,residualOffsetUs:0,relativeClockDriftPpm:0,relativeChannelDelayUs:0,pathLengthUncertaintyM:0};
  const check=(condition,msg)=>{if(!condition) throw Error(msg);};
  const close=(a,b)=>Math.abs(a-b)<1e-9;
  const cases=[
    ['zero uncertainty passes',()=>{const x=audit(base);check(x.measuredWithinBudget&&x.predictionWithinBudget&&x.measuredPhaseDeg===0,'zero');}],
    ['phase formula and maximum delay',()=>{const x=audit({...base,frequencyHz:1000,residualOffsetUs:10});check(close(x.measuredPhaseDeg,3.6)&&close(x.maxTimeUs,5/360000*1e6),'phase');}],
    ['one sample at 48 kHz',()=>{const x=audit(base);check(close(x.oneSamplePhaseDeg,360*base.frequencyHz/48000)&&x.oneSamplePhaseDeg>5,'sample');}],
    ['relative clock drift accumulates',()=>{const x=audit({...base,relativeClockDriftPpm:10,elapsedSeconds:2});check(x.driftUs===20&&!x.measuredWithinBudget,'drift');}],
    ['offset and residual sensor latency summed',()=>{const x=audit({...base,residualOffsetUs:4,relativeChannelDelayUs:7});check(x.timingUs===11&&!x.measuredWithinBudget,'timing');}],
    ['geometry affects prediction not measured transfer',()=>{const x=audit({...base,pathLengthUncertaintyM:.01});check(x.measuredWithinBudget&&!x.predictionWithinBudget&&close(x.geometryUs,.01/343*1e6),'geometry');}],
    ['boundary exactly accepted',()=>{const x=audit({...base,frequencyHz:1000});check(audit({...base,frequencyHz:1000,residualOffsetUs:x.maxTimeUs}).measuredWithinBudget,'boundary');}],
    ['higher partial tightens tolerance',()=>{const a=audit({...base,frequencyHz:500});const b=audit({...base,frequencyHz:2000});check(close(a.maxTimeUs,4*b.maxTimeUs),'frequency');}],
    ['remaining geometry budget nonnegative',()=>{check(audit({...base,residualOffsetUs:50}).remainingPathUncertaintyM===0,'remaining');}],
    ['explicit values required; no zero default',()=>{let bad={...base};delete bad.relativeChannelDelayUs;let rejected=false;try{audit(bad);}catch(e){rejected=e instanceof RangeError;}check(rejected,'missing');}],
    ['invalid or nonfinite values rejected',()=>{for(const patch of [{sampleRateHz:0},{relativeClockDriftPpm:-1},{frequencyHz:NaN},{pathLengthUncertaintyM:Infinity},{maxPhaseErrorDeg:180},{frequencyHz:24000}]){let rejected=false;try{audit({...base,...patch});}catch(e){rejected=e instanceof RangeError;}check(rejected,JSON.stringify(patch));}}],
    ['higher sample rate does not remove clock error',()=>{const a=audit({...base,residualOffsetUs:20});const b=audit({...base,residualOffsetUs:20,sampleRateHz:96000});check(a.measuredPhaseDeg===b.measuredPhaseDeg&&!b.measuredWithinBudget&&close(a.oneSamplePhaseDeg,2*b.oneSamplePhaseDeg),'rate');}]
  ];
  for(const [name,test] of cases){try{test();}catch(e){throw Error(name+': '+e.message);}}
  return {passed:cases.length,names:cases.map(c=>c[0])};
}
const result = runPhaseBudgetTests(auditPhaseBudget);
for (const name of result.names) console.log('PASS '+name);
console.log(`${result.passed}/${result.passed} tests passed`);
