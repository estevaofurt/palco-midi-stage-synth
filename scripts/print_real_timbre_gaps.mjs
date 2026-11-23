/**
 * Prints a bounded diagnostic digest; piano reference recordings stay in CI temp.
 * Mean absolute dB of surviving relative harmonics is NOT a perceptual fidelity score.
 */
import {readFileSync} from 'node:fs';
if(process.argv.length!==3)throw Error('usage: node scripts/print_real_timbre_gaps.mjs /tmp/e0-report.json');
const notes=JSON.parse(readFileSync(process.argv[2],'utf8')).notes;
for(const n of notes){
  const ref=n.real;
  console.log('Iowa '+n.key+' '+n.dynamic+' | onset '+n.analysis.offsetSeconds.toFixed(3)+
    ' s | measured B '+(ref.bMedian??'undetermined')+
    ' | reference original '+n.provenance.sha256.slice(0,12));
  const candidates=['A_modal','B_v195','C_mechanical','D_hybrid'];
  for(const engine of candidates){
    const result=n.stage[engine],delta=n.shapeDifferences[engine];
    const early=result.earlySpectrum;
    const realEarly=ref.earlySpectrum;
    const earlyDiff=[];
    for(const a of realEarly.harmonics){
      if(a.n===1||!Number.isFinite(a.relativeDb)||a.relativeDb<-32)continue;
      const b=early.harmonics.find(x=>x.n===a.n);
      if(!b||!Number.isFinite(b.relativeDb))continue;
      earlyDiff.push([a.n,Math.round((b.relativeDb-a.relativeDb)*10)/10]);
    }
    const scalar=(delta.meanAbsDb??delta.exploratoryMeanAbsDb);
    console.log('  '+engine.padEnd(12)+' model-minus-reference (harmonic): |Δ|='+
       (scalar===null||scalar===undefined?'n/a':scalar.toFixed(1)+'dB')+
       '; comparable=+delta.comparablePartials+
       '; early deviations model-minus-ref='+JSON.stringify(earlyDiff.slice(0,8))+
       '; lateDecDb='+result.lateDecayDb);
  }
}
