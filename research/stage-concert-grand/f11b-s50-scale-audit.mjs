// F11b: fixed-gain cross-key diagnostics, not a perceptual acceptance criterion.
export const TOUCHES=Object.freeze([24,76,127]);
const db=(a,b)=>20*Math.log10(a/b);
const positive=x=>Number.isFinite(x)&&x>0;
export function auditScale(cases,{notes=Array.from({length:20},(_,i)=>53+i),gain=.2757526758002555,attackJumpDb=6,tailJumpDb=9}={}){
 if(!Array.isArray(cases)||!notes.length||notes.some((m,i)=>!Number.isInteger(m)||i&&m<=notes[i-1])||!positive(gain)||!positive(attackJumpDb)||!positive(tailJumpDb))throw RangeError('audit scope');
 const byKey=new Map,rows=[],missing=[],rejected=[],pairs=[],dynamics=[];
 for(const c of cases){
  if(!notes.includes(c.midi)||!TOUCHES.includes(c.midiVelocity))throw Error('unexpected case');
  const key=c.midi+':'+c.midiVelocity;
  if(byKey.has(key))throw Error('duplicate case '+key);
  byKey.set(key,c);
 }
 for(const midi of notes)for(const touch of TOUCHES){
  const c=byKey.get(midi+':'+touch);
  if(!c){missing.push({midi,touch});continue}
  if(c.conclusion==='failure'){rejected.push({midi,touch,reason:c.reason??'CI failure',peak:c.peak??null,clipped:c.clipped??null});continue}
  const rms0=c.rms?.find(x=>x.startS===0)?.rms,rms2=c.rms?.find(x=>x.startS===2)?.rms;
  if(c.gain!==gain||c.duration!==3||!positive(rms0)||!positive(rms2)||!positive(c.peak)||c.peak>.85||c.clipped!==0||!Number.isFinite(c.maxBalance)||c.maxBalance>1e-9||!Number.isFinite(c.maxIncrease)||c.maxIncrease>1e-9)throw Error('invalid successful case '+midi+':'+touch);
  if(!Array.isArray(c.windows)||c.windows.length!==4||c.windows.some(w=>!positive(w.rmsBand)||!Number.isFinite(w.wideOffFraction)||w.wideOffFraction<0||w.wideOffFraction>1))throw Error('invalid spectrum');
  rows.push({midi,touch,peak:c.peak,rms0,rms2,decayDb:db(rms2,rms0),off:c.windows.map(w=>({fraction:w.wideOffFraction,power:w.wideOffFraction*w.rmsBand**2})),artifactId:c.artifactId??null});
 }
 for(const midi of notes){
  const q=TOUCHES.map(t=>rows.find(x=>x.midi===midi&&x.touch===t));
  if(q.every(Boolean))dynamics.push({midi,peakMonotonic:q.every((x,i)=>!i||x.peak>q[i-1].peak),attackMonotonic:q.every((x,i)=>!i||x.rms0>q[i-1].rms0),tailMonotonic:q.every((x,i)=>!i||x.rms2>q[i-1].rms2)});
  for(const touch of TOUCHES){
   const a=rows.find(x=>x.midi===midi&&x.touch===touch),b=rows.find(x=>x.midi===midi+1&&x.touch===touch);
   if(!a||!b)continue;
   const attackDb=db(b.rms0,a.rms0),tailDb=db(b.rms2,a.rms2);
   pairs.push({from:midi,to:midi+1,touch,attackDb,tailDb,decayDifferenceDb:b.decayDb-a.decayDb,flag:Math.abs(attackDb)>attackJumpDb||Math.abs(tailDb)>tailJumpDb});
  }
 }
 return {scope:'fixed-gain nonperceptual adjacent-key screen; thresholds are engineering triage, not measured piano standards',gain,attackJumpDb,tailJumpDb,expected:notes.length*TOUCHES.length,valid:rows.length,missing,rejected,rows,dynamics,pairs,flagged:pairs.filter(x=>x.flag)};
}
