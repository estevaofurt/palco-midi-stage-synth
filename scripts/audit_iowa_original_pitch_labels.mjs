/**
 * AUDIT ONLY: numeric pitch-label evidence from Iowa ORIGINAL SHA-verified
 * AIFF source, decoded by the existing Python acquisition script into runner
 * TEMP 48k mono PCM. Do not write/import PCM into git or published assets.
 *
 * node scripts/audit_iowa_original_pitch_labels.mjs \
 *    RUNNER_TEMP/manifest.json RUNNER_TEMP/report.json
 */
import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {auditPitchLabel} from '../research/iowa-f0-label-audit.mjs';
import {compareOctaveHarmonicSupport} from '../research/iowa-pitch-harmonic-comb.mjs';
const EXPECTED=new URL('../research/commercial_audio/iowa_steinway_b_verified_original_sha256.json',import.meta.url);
const meta=JSON.parse(readFileSync(EXPECTED,'utf8'));
const pitches=new Map([['C2',36],['C3',48],['C4',60],['C5',72],['C6',84]]);
function decodePCM(raw){
 if(raw.byteLength%4)throw Error('unaligned f32le audio');
 const out=new Float32Array(raw.byteLength/4);
 for(let i=0;i<out.length;i++)out[i]=raw.readFloatLE(4*i);
 return out;
}
function onset(samples,rate){
 const block=Math.round(rate*.005);
 const count=Math.floor(Math.min(samples.length,rate*2)/block);
 const rms=new Float64Array(count);
 let max=0;
 for(let j=0;j<count;j++){
  let e=0;for(let i=0;i<block;i++)e+=samples[j*block+i]**2;
  rms[j]=Math.sqrt(e/block);max=Math.max(max,rms[j]);
 }
 if(!(max>1e-6))return null;
 for(let i=0;i<count-1;i++)
  if(rms[i]>.035*max && rms[i+1]>.035*max)return i*block;
 return null;
}
export function evaluateManifest(manifest){
 const expected=new Map();
 for(const item of meta.items)expected.set(item.id,item);
 if(meta.verifiedOriginalFileCount!==15||expected.size!==15)
  throw Error('unexpected approved Iowa origin manifest');
 if(!Array.isArray(manifest.notes)||manifest.notes.length!==15)
  throw Error('expected 15 original Iowa notes');
 const output=[],seen=new Set();
 for(const item of manifest.notes){
  const m=/^iowa-steinway-model-b-(C[2-6])-(pp|mf|ff)$/.exec(item.id);
  if(!m||seen.has(item.id))throw Error('duplicate/unexpected source id '+item.id);
  seen.add(item.id);
  const reference=expected.get('iowa-steinway-b-'+m[1].toLowerCase()+'-'+m[2]);
  if(!reference)throw Error('no pinned original for '+item.id);
  if(reference.sha256!==item.sha256||reference.bytes!==item.bytes)
   throw Error('original Iowa bytes/SHA256 do not match pinned manifest '+item.id);
  if(item.key!==pitches.get(m[1])||item.dynamic!==m[2]||
     item.originalRate!==44100||item.originalChannels!==2||
     item.originalFormat!=='pcm_s16be')
   throw Error('unexpected original recording identity/codec '+item.id);
  const pcm=decodePCM(readFileSync(item.pcmPath));
  const onsetFrame=onset(pcm,48000);
  if(onsetFrame===null||pcm.length-onsetFrame<1.5*48000){
   output.push({id:item.id,key:item.key,dynamic:item.dynamic,sha256:item.sha256,
     classification:'inconclusive',reason:'undetectable onset or insufficient 1.5s after it'});
   continue;
  }
  const aligned=pcm.subarray(onsetFrame,onsetFrame+Math.floor(48000*1.5));
  const result=auditPitchLabel(aligned,{key:item.key,sampleRate:48000});
  const spectral=compareOctaveHarmonicSupport(aligned,{key:item.key,sampleRate:48000});
  const jointLabelAssessment=result.classification==='label-consistent'&&spectral.classification==='spectral-supports-label'?
   'dual-method-consistent':
   result.classification==='label-mismatch-candidate'&&spectral.classification==='spectral-mismatch-candidate'?
   'dual-method-mismatch-candidate':
   result.classification==='label-consistent'&&spectral.classification==='spectral-mismatch-candidate'?
   'contradictory-methods':
   'not-dual-verified';
  output.push({id:item.id,key:item.key,dynamic:item.dynamic,
   sourceSha256:item.sha256,bytes:item.bytes,
   onsetSeconds:Number((onsetFrame/48000).toFixed(3)),
   ...result,spectral,jointLabelAssessment});
 }
 if(seen.size!==15)throw Error('incomplete 15-note matrix');
 const counts={},jointCounts={};
 for(const o of output){
  counts[o.classification]=(counts[o.classification]||0)+1;
  jointCounts[o.jointLabelAssessment]=(jointCounts[o.jointLabelAssessment]||0)+1;
 }
 return {
  schema:'stage-iowa-original-pitch-label-audit-v1',
  method:'two independent windows, YIN CMND, 48->24 kHz',
  rightsAndHashes:'15 original Iowa AIFF bytes and SHA256 checked against prior approved source manifest',
  noPhysicalParametersIdentified:true,
  noAudioUploaded:true,doesNotCalibrateStage:true,
  warning:'YIN may yield octave bias under inharmonic piano partials; mismatch is a candidate to inspect, not proof of mislabelling. Nominal Iowa pp/mf/ff not calibrated MIDI velocity.',
  counts,jointCounts,results:output
 };
}
if(process.argv[1]&&fileURLToPath(import.meta.url)===process.argv[1]){
 const [input,out]=process.argv.slice(2);
 if(!input||!out)throw Error('usage: node scripts/audit_iowa_original_pitch_labels.mjs manifest.json report.json');
 const report=evaluateManifest(JSON.parse(readFileSync(input,'utf8')));
 writeFileSync(out,JSON.stringify(report,null,2)+'\n');
 for(const item of report.results)
  console.log('IOWA_PITCH '+item.id+' '+item.classification+
   ' f0='+item.f0Hz+' Hz offset='+item.centsFromLabel+
   'c agreement='+item.agreementCents+'c spectral='+item.spectral.classification+
   ' joint='+item.jointLabelAssessment);
 console.log('IOWA_PITCH_COUNTS '+JSON.stringify(report.counts));
 console.log('IOWA_PITCH_JOINT '+JSON.stringify(report.jointCounts));
}
