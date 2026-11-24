import {readFileSync,writeFileSync} from 'node:fs';
import {comparePartialWindows} from './f9-harmonic-comparison.mjs';
const [dir,out]=process.argv.slice(2);
const base=JSON.parse(readFileSync(new URL('./audio/analysis_f9_9_both_half_ci.json',import.meta.url)));
if(base.runId!==45415259799||base.lossCase!=='both-half'||base.export.clipped!==0)throw Error('unexpected control');
const layers=['v1','v8','v16'].map(layer=>{
 const ref=JSON.parse(readFileSync(dir+'/c5-'+layer+'.json'));
 if(ref.windowS!==.5||ref.rate!==48000||ref.onsetS!==.005||ref.bands.length!==10)throw Error('incompatible reference');
 return {layer,analyzedThroughS:ref.analyzedThroughS,referenceBroadband:ref.broadband,referencePartials:ref.partialDrops,comparison:comparePartialWindows(base.floatWindows,ref.windows)};
});
const result={scope:'numeric-only C5 reference; same estimator and shared 0.5 s windows, not calibrated velocity or SPL; sparse Stage summary; no audio copied into engine',sourceCommit:'3382bf9496bba2486f5ab0de55a264d1dfc38404',license:'CC BY 3.0; Alexander Holm; Salamander Grand Piano v3',controlRun:base.runId,layers};
writeFileSync(out,JSON.stringify(result,null,2),{flag:'wx'});
console.log('F916_HARMONICS '+JSON.stringify(layers.map(x=>({layer:x.layer,byPartial:x.comparison.byPartial,windows:x.comparison.windows.filter(w=>[0,1,4,10,14].includes(w.startS))}))));
