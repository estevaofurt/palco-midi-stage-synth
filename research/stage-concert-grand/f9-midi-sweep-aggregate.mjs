import {readFileSync,writeFileSync} from 'node:fs';
import {hammerSpeed} from './f9-midi-velocity.mjs';
import {summarizeVelocitySweep} from './f9-midi-sweep-analysis.mjs';
const [dir,out]=process.argv.slice(2),rows=[];
for(let i=0;i<8;i++){
 const q=JSON.parse(readFileSync(dir+'/F918B-shard'+i+'/shard.json'));
 if(q.shard!==i||q.rows.length!==Math.min(16,127-i*16))throw Error('shard mismatch');
 rows.push(...q.rows);
}
const summary=summarizeVelocitySweep(rows,hammerSpeed);
const historic=JSON.parse(readFileSync(new URL('./audio/analysis_f9_18_ci.json',import.meta.url)));
const parity=historic.smoke.map(r=>{const q=rows[r.midiVelocity-1];return {midiVelocity:r.midiVelocity,rmsDifferencePa:q.rmsPa-r.rmsPa,forceDifferenceN:q.peakForce-r.peakForce};});
if(parity.some(r=>Math.abs(r.rmsDifferencePa)>1e-12||Math.abs(r.forceDifferenceN)>1e-12))throw Error('historical regression');
const result={scope:'127 independent 0.1s physical strikes, unfiltered pressure before export; 0–50ms Hann spectral shape, not loudness or sustain',summary,parity,rows};
writeFileSync(out,JSON.stringify(result,null,2),{flag:'wx'});
console.log('F918B_SUMMARY '+JSON.stringify({count:summary.count,rangeRmsDb:summary.rangeRmsDb,maxBalanceJ:summary.maxBalanceJ,maxIncreaseJ:summary.maxIncreaseJ,metrics:summary.metrics,parity}));
