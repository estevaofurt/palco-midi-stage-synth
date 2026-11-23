/** Numeric, original-source-attributed spectral anchors, never source WAV/AIFF. */
import {readFileSync,writeFileSync} from 'node:fs';
if(process.argv.length!==4)throw Error('usage: node scripts/extract_iowa_spectral_targets.mjs input.json output.json');
const report=JSON.parse(readFileSync(process.argv[2],'utf8'));
const keys=[36,48,60,72,84],dynamics=['pp','mf','ff'];
if(report.notes?.length!==keys.length*dynamics.length)throw Error('Expected 5 register x 3 dynamics of Iowa originals');
const manifest=[];
for(const key of keys){
 for(const dynamic of dynamics){
  const entries=report.notes.filter(x=>x.key===key&&x.dynamic===dynamic);
  if(entries.length!==1)throw Error('Not exactly one matching instrument-note for '+key+':'+dynamic);
  const n=entries[0];
  if(!n.instrument?.includes('Steinway')||!/^[a-f\d]{64}$/.test(n.provenance.sha256))
    throw Error('Missing Steinway provenance / SHA256');
  const harmonics=n.real.earlySpectrum.harmonics;
  if(harmonics.length<2||harmonics[0].n!==1)throw Error('Invalid spectral harmonics');
  const db=harmonics.map(x=>[x.n,Number.isFinite(x.relativeDb)?Math.round(x.relativeDb*10)/10:null]);
  const prev=n.stage.D_hybrid?.earlySpectrum.harmonics||[];
  const current=prev.map(x=>[x.n,Number.isFinite(x.relativeDb)?Math.round(x.relativeDb*10)/10:null]);
  manifest.push({key,dynamic,sourceSha256:n.provenance.sha256,onsetSeconds:n.analysis.offsetSeconds,
    earlyFftSize:n.real.earlySpectrum.fftSize,earlyWindowSeconds:n.real.earlySpectrum.windowStart,
    partialsRelativeDb:db,hybridDCurrentDb:current,
    bEstimate:n.real.bSampleCount>=3?n.real.bMedian:null,
    bCandidateCount:n.real.bSampleCount,
    relativeSpectralErrorDb:n.shapeDifferences.D_hybrid.meanAbsDb,
    warnings:['Measured relative spectrum includes microphone position and room response.',
       'The sample note and musical dynamics are source labels; physical hammer velocity not known.']});
 }
}
const result={schema:'stage-iowa-early-spectral-targets-15-v1',basis:'Iowa Steinway B 2001 original 44.1kHz 16-bit stereo AIFF',
  licenseBasis:'https://theremin.music.uiowa.edu/MIS.html',
  sourceManifest:'research/commercial_audio/iowa_steinway_b_verified_original_sha256.json',
  processing:'ffmpeg downmix to 48k float mono; onset detection; Hann FFT at 18 ms window start; normalized to fundamental; 0.1 dB rounding.',
  caution:'These are radiated-acoustic observations, NOT measured hammer force, string partial amplitudes, bridge admittance, or perceptual fidelity scores.',
  records:manifest};
writeFileSync(process.argv[3],JSON.stringify(result,null,2)+'\n');
console.log('SPECTRAL TARGETS',manifest.length,'instrument-level reference spectra (numeric only, 8 partials each)');
for(const r of manifest)
 console.log('TARGET '+r.key+'/'+r.dynamic+' spectrum_dB='+JSON.stringify(r.partialsRelativeDb)+' D_current='+JSON.stringify(r.hybridDCurrentDb)+' B_estimate='+r.bEstimate);
