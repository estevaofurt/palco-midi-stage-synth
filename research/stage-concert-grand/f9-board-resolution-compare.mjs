import {readFileSync,writeFileSync} from 'node:fs';
import {BOARD_RESOLUTIONS} from './f9-board-resolution-parameters.mjs';
import {compareResolutions} from './f9-board-resolution-analysis.mjs';
const [dir,out]=process.argv.slice(2),cases=Object.keys(BOARD_RESOLUTIONS).map(resolution=>{
 const stem=dir+'/F916B-'+resolution+'/C4_v1_board0.5_angle0.5_spread0.5_both-half_'+resolution+'_3s';
 const m=JSON.parse(readFileSync(stem+'.json')),a=JSON.parse(readFileSync(stem+'_float_analysis.json'));
 if(m.resolution!==resolution||m.duration!==3||m.velocity!==1||m.gain!==.36767023440034063||m.clipped!==0||m.chunks.length!==3||a.windows.length!==5||a.windowS!==.5||m.chunks.some(c=>c.resolution!==resolution||c.maxBalance>1e-9||c.maxIncrease>1e-9))throw Error('incompatible resolution render');
 return {resolution,windows:a.windows,meta:m.chunks[0],peak:m.peak};
});
const comparisons=cases.slice(1).map((b,i)=>compareResolutions(cases[i],b));
const result={scope:'numerical basis/cutoff sensitivity, not physical calibration or convergence proof; 3-second experiment; fixed gain and radiation grid',cases,comparisons};
writeFileSync(out,JSON.stringify(result,null,2),{flag:'wx'});
console.log('F916B_COMPARISON '+JSON.stringify(comparisons.map(({from,to,global,byPartial})=>({from,to,global,byPartial}))));
