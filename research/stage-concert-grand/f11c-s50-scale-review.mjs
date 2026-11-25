import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {auditScale,TOUCHES} from './f11b-s50-scale-audit.mjs';
import {inspect24,header} from './f9-rattle-comparison.mjs';
import {inspectPair} from './f9-soft-pcm-audit.mjs';
const [input,out]=process.argv.slice(2);
if(!input||!out)throw Error('input/output required');
const reference=JSON.parse(readFileSync(new URL('../../audio/analysis_f10h_d4_ci.json',import.meta.url),'utf8')).cases;
const notes=Array.from({length:20},(_,i)=>53+i),cases=[],sources=[],clips=new Map,partials=new Map;
const old=new Set(reference.map(x=>x.midi));
for(const midi of notes)for(const touch of TOUCHES){
 const root=old.has(midi)?touch===127?'g':'h':'a',prefix=root==='g'?'F10G-S50':root==='h'?'F10H-S50':'F11A-S50';
 const dir=join(input,root,prefix+'-midi'+midi+'-touch'+touch);
 const files=readdirSync(dir),find=suffix=>{const q=files.filter(f=>f.endsWith(suffix));if(q.length!==1)throw Error('expected unique '+suffix+' '+dir);return join(dir,q[0])};
 const result=JSON.parse(readFileSync(find('_rattle.json'),'utf8')),analysis=JSON.parse(readFileSync(find('_float_analysis.json'),'utf8'));
 const pcm=readFileSync(find('_24bit.wav')),base=readFileSync(find('_3s.wav'));
 if(result.midi!==midi||result.midiVelocity!==touch||result.duration!==3||result.gain!==.2757526758002555||result.clipped!==0||inspect24(pcm).frames!==144239)throw Error('source metadata');
 const pair=inspectPair(base,pcm);
 if(Math.abs(pair.peak24-result.peak)>.5/8388607+1e-12||analysis.windowS!==.5||analysis.rate!==48000)throw Error('PCM mismatch');
 const ref=reference.find(x=>x.midi===midi&&x.midiVelocity===touch);
 if(ref&&(ref.peak!==result.peak||JSON.stringify(ref.rms)!==JSON.stringify(result.rms)))throw Error('frozen reference mismatch');
 const key=midi+':'+touch;
 const ps=analysis.windows.filter(w=>[0,2].includes(w.startS));
 if(ps.length!==2||ps.some((w,i)=>Math.abs(w.rms-result.rms.find(v=>v.startS===w.startS).rms)>1e-12||w.partials.length!==10))throw Error('partial metadata');
 cases.push({...result,runId:root==='g'?45509969698:root==='h'?45511128271:45518512147,artifactId:ref?.artifactId??null});
 partials.set(key,ps);
 sources.push({midi,touch,artifact:prefix+'-midi'+midi+'-touch'+touch,sha256:createHash('sha256').update(pcm).digest('hex'),frames:pair.frames});
 clips.set(key,inspect24(pcm).pcm);
}
const audit=auditScale(cases);
if(audit.valid!==60||audit.missing.length||audit.rejected.length||audit.pairs.length!==57)throw Error('incomplete scale');
const details=audit.flagged.map(p=>({...p,partialWindows:partials.get(p.from+':'+p.touch).map((a,i)=>{
 const b=partials.get(p.to+':'+p.touch)[i];
 return {startS:a.startS,partials:a.partials.map((x,k)=>({h:k+1,fromRms:x.rms,toRms:b.partials[k].rms,fromContrastDb:x.contrastDb,toContrastDb:b.partials[k].contrastDb,deltaDb:x.rms>0&&b.partials[k].rms>0?20*Math.log10(b.partials[k].rms/x.rms):null}))};
})}));
mkdirSync(out,{recursive:true});
for(const touch of TOUCHES){
 // Preserve complete source clips including original fade and 239-frame propagation tail.
 const clipFrames=144239,gapFrames=12000,stride=clipFrames+gapFrames;
 const wave=header(notes.length*clipFrames+(notes.length-1)*gapFrames),dst=wave.subarray(44);
 notes.forEach((midi,i)=>{const src=clips.get(midi+':'+touch),p=i*stride*6;dst.set(src,p);if(!Buffer.from(dst.subarray(p,p+src.length)).equals(Buffer.from(src)))throw Error('PCM prefix mismatch');});
 writeFileSync(join(out,'S50_chromatic_touch'+touch+'_24bit.wav'),wave,{flag:'wx'});
}
writeFileSync(join(out,'cases.json'),JSON.stringify({cases},null,2),{flag:'wx'});
writeFileSync(join(out,'audit.json'),JSON.stringify({...audit,flaggedDetails:details},null,2),{flag:'wx'});
writeFileSync(join(out,'manifest.json'),JSON.stringify({notes,touches:TOUCHES,format:'48k stereo PCM24',gain:audit.gain,clipFrames:144239,gapFrames:12000,startsS:notes.map((_,i)=>i*156239/48000),normalization:false,scope:'sequential single-note clips, not polyphony',sources},null,2),{flag:'wx'});
console.log('F11C_SCALE_AUDIT '+JSON.stringify({valid:audit.valid,expected:audit.expected,flagged:audit.flagged,dynamics:audit.dynamics,maxPeak:Math.max(...audit.rows.map(x=>x.peak))}));
