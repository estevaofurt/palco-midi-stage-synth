import {readFileSync,writeFileSync} from 'node:fs';
import {DYNAMIC_SPEEDS,compareDynamics} from './f9-dynamics-analysis.mjs';
const [folder,output]=process.argv.slice(2);
if(!folder||!output)throw Error('artifact folder and output required');
const entries=DYNAMIC_SPEEDS.map(velocity=>{
 const dir=folder+'/F910-velocity-'+velocity,stem=dir+'/C4_v'+velocity+'_board0.5_angle0.5_spread0.5_both-half_40s';
 const metadata=JSON.parse(readFileSync(stem+'.json','utf8')),analysis=JSON.parse(readFileSync(stem+'_float_analysis.json','utf8'));
 if(metadata.velocity!==velocity||metadata.duration!==40||metadata.lossCase!=='both-half'||metadata.clipped!==0||metadata.chunks.length!==40)throw Error('invalid render metadata');
 return {velocity,gain:metadata.gain,analysis};
});
const result=compareDynamics(entries);
writeFileSync(output,JSON.stringify(result,null,2),{flag:'wx'});
console.log('F910_DYNAMIC_SUMMARY '+JSON.stringify(result.entries.map(e=>({velocity:e.velocity,initialRms:e.initialRms,initialDbRelativeToMedium:e.initialDbRelativeToMedium,relativeDrops:e.relativeDrops,commonDrops:e.commonDrops,windows:e.windows.filter(w=>[0,10,19,29,39].includes(w.startS)).map(w=>({startS:w.startS,dbRelativeToMedium:w.dbRelativeToMedium,dbRelativeToOwnStart:w.dbRelativeToOwnStart}))}))));
