import {readFileSync,writeFileSync} from 'node:fs';
import {POSITIONS,PEDAL_PROXIES,assessCandidate,rankCandidates} from './f9-pedal-sensitivity.mjs';
const [dir,out]=process.argv.slice(2);
const base=JSON.parse(readFileSync(new URL('./audio/analysis_f9_14b_ci.json',import.meta.url)));
if(base.runId!==45427666254||base.cases.length!==5)throw Error('base provenance');
const open=base.cases.find(c=>c.position===.27&&c.pedal===1),rows=[];
for(const position of POSITIONS)for(const pedal of PEDAL_PROXIES){
 const stem=dir+'/F914C-pos-'+position+'-proxy-'+pedal+'/C4_v1_board0.5_angle0.5_spread0.5_both-half_off_pedal'+pedal+'_pos'+position+'_3s';
 const m=JSON.parse(readFileSync(stem+'.json')),a=JSON.parse(readFileSync(stem+'_float_analysis.json'));
 if(m.duration!==3||m.velocity!==1||m.damperFraction!==position||m.pedal!==pedal||m.gain!==.36767023440034063||m.clipped!==0||a.windowS!==.25||a.windows.length!==11||m.chunks.length!==3||m.chunks.some(c=>c.maxBalance>1e-9||c.maxIncrease>1e-9))throw Error('incompatible candidate');
 rows.push(assessCandidate({position,pedal,windows:a.windows},base.cases.find(c=>c.position===position&&c.pedal===0),open));
}
const ranked=rankCandidates(rows),result={scope:'passive coefficient sensitivity, not a calibrated pedal geometry or listening approval',referenceRun:base.runId,rows,ranked,selectedForFurtherListening:ranked[0]??null};
writeFileSync(out,JSON.stringify(result,null,2),{flag:'wx'});
console.log('F914C_COMPARISON '+JSON.stringify(result));
