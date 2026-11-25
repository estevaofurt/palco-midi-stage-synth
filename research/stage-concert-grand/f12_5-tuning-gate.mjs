import {createHash} from 'node:crypto';
// F12.5 preliminary release-gate report validator. This is not a pitch detector,
// authentication mechanism, or an export pipeline. Review evidence must be
// independently produced and verified against the exact candidate binary.
export const PIANO_NOTES=Object.freeze(Array.from({length:88},(_,i)=>21+i));
export const AF_TOUCHES=Object.freeze([24,76,127]);
export const AF_REVIEWS=Object.freeze(['partials','unison','intervals','pedals','polyphony','rates','offlineRegression','listening']);
const isSha=x=>typeof x==='string'&&/^[a-f0-9]{40}$/.test(x);
const isHash=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const nonempty=x=>typeof x==='string'&&x.trim().length>0;
const validHz=x=>Number.isFinite(x)&&x>0;
const cents=(f,t)=>1200*Math.log2(f/t);
export function targetCurveDigest(targets){
 return createHash('sha256').update(JSON.stringify([...targets].sort((a,b)=>a.midi-b.midi).map(t=>[t.midi,t.hz]))).digest('hex');
}
export function validateTuningReport(report,candidate){
 const issues=[],rows=[],seen=new Set,targets=new Map;
 const issue=(code,detail)=>issues.push({code,detail});
 if(!candidate||!isSha(candidate.commit)||!isHash(candidate.binarySha256)||!isHash(candidate.configSha256))throw Error('invalid expected export candidate identity');
 if(!report||typeof report!=='object')return {eligible:false,issues:[{code:'report',detail:'missing report'}],rows};
 for(const key of ['commit','binarySha256','configSha256'])if(report.candidate?.[key]!==candidate[key])issue('candidate',key);
 if(report.schema!=='AF-1')issue('schema','expected AF-1');
 if(report.referenceA4Hz!==440)issue('reference','A4 must be 440 Hz');
 if(!isHash(report.targetCurveSha256)||report.targetCurveSha256!==candidate.targetCurveSha256||!isHash(candidate.targetCurveSha256))issue('curve','predeclared curve digest mismatch');
 for(const t of Array.isArray(report.targets)?report.targets:[]){
  if(!t||!PIANO_NOTES.includes(t.midi)||!validHz(t.hz)||targets.has(t.midi)){issue('target','invalid or duplicate target');continue;}
  targets.set(t.midi,t.hz);
 }
 if(targets.size===88&&targetCurveDigest([...targets].map(([midi,hz])=>({midi,hz})))!==candidate.targetCurveSha256)issue('curve','actual target values do not match digest');
 if(targets.size!==88||targets.get(69)!==440||PIANO_NOTES.some((m,i)=>i&&targets.get(m)<=targets.get(m-1)))issue('targets','complete increasing 88-note curve required');
 for(const c of Array.isArray(report.cases)?report.cases:[]){
  if(!c||typeof c!=='object'){issue('case','invalid row');continue;}
  const key=c.midi+':'+c.touch;
  if(!PIANO_NOTES.includes(c.midi)||!AF_TOUCHES.includes(c.touch)||seen.has(key)){issue('case',key+' invalid or duplicate');continue;}
  seen.add(key);
  const target=targets.get(c.midi),w=Array.isArray(c.windows)?c.windows:[],usable=[];
  if(!isHash(c.pcmSha256)||!nonempty(c.evidence))issue('evidence',key);
  // A distinct early, middle and late measured window is necessary. The actual
  // durations and estimator uncertainties remain recorded, not inferred.
  if(w.length<3||w[0]?.startS>.5||w.some((q,i)=>!q||!Number.isFinite(q.startS)||!Number.isFinite(q.endS)||q.startS<0||q.endS<=q.startS||i&&(!w[i-1]||q.startS<w[i-1].endS)))issue('windows',key);
  for(const q of w){
   if(!q||q.status!=='reliable'||!validHz(q.fundamentalHz)||!Number.isFinite(q.uncertaintyCents)||q.uncertaintyCents<0||!validHz(target)){issue('indeterminate',key+' @ '+q?.startS);continue;}
   usable.push({offset:cents(q.fundamentalHz,target),uncertainty:q.uncertaintyCents});
  }
  if(usable.length!==w.length||usable.length<3)continue;
  const maxError=Math.max(...usable.map(q=>Math.abs(q.offset)+q.uncertainty));
  const span=Math.max(...usable.map(q=>q.offset+q.uncertainty))-Math.min(...usable.map(q=>q.offset-q.uncertainty));
  const pass=maxError<=5&&span<=5;
  rows.push({midi:c.midi,touch:c.touch,maxErrorCents:maxError,spanCents:span,pass});
  if(!pass)issue('pitch',key+' exceeds provisional 5-cent bounds including uncertainty');
 }
 if(seen.size!==264||rows.length!==264)issue('coverage','88 keys x three intensities required; indeterminate does not pass');
 for(const name of AF_REVIEWS){
  const q=report.reviews?.[name];
  if(q?.status!=='pass'||!nonempty(q.evidence)||!nonempty(q.reviewer)||q.candidateSha256!==candidate.binarySha256)issue('review',name);
 }
 return {eligible:issues.length===0,issues,rows,expectedCases:264,completeCases:rows.length};
}
export function assertTuningReport(report,candidate){
 const result=validateTuningReport(report,candidate);
 if(!result.eligible)throw Error('AF tuning gate blocked: '+result.issues.map(x=>x.code+': '+x.detail).join('; '));
 return result;
}
