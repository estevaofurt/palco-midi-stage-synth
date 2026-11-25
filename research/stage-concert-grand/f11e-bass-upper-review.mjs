import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {join} from 'node:path';
import {inspect24,header} from './f9-rattle-comparison.mjs';
import {inspectPair} from './f9-soft-pcm-audit.mjs';
import {createHash} from 'node:crypto';
const [input,out]=process.argv.slice(2);
if(!input||!out)throw Error('input/output required');
const gain=.2757526758002555;
function readCase(dir,midi,touch,count=null){
 const files=readdirSync(dir),find=s=>{const q=files.filter(f=>f.endsWith(s));if(q.length!==1)throw Error('unique source '+s+' '+dir);return join(dir,q[0])};
 const result=JSON.parse(readFileSync(find('_rattle.json'),'utf8')),analysis=JSON.parse(readFileSync(find('_float_analysis.json'),'utf8'));
 const raw=JSON.parse(readFileSync(find('_3s.json'),'utf8')),pcm=readFileSync(find('_24bit.wav')),base=readFileSync(find('_3s.wav')),pair=inspectPair(base,pcm);
 if(result.midi!==midi||result.midiVelocity!==touch||result.gain!==gain||result.clipped!==0||result.duration!==3||pair.frames!==144239||Math.abs(pair.peak24-result.peak)>.5/8388607+1e-12||raw.chunks.length!==3||count!==null&&result.count!==count)throw Error('metadata mismatch');
 return {result,analysis,raw,pcm:inspect24(pcm).pcm,hash:createHash('sha256').update(pcm).digest('hex')};
}
const notes=[65,66,70,71,72],diagnostics=[];
for(const midi of notes)for(const touch of [24,76,127]){
 const root=midi===72?touch===127?'g':'h':'a',prefix=root==='g'?'F10G-S50':root==='h'?'F10H-S50':'F11A-S50';
 const q=readCase(join(input,root,prefix+'-midi'+midi+'-touch'+touch),midi,touch);
 const energy=q.raw.chunks.map((c,i)=>{
  const v=c.polarization.vertical,u=c.polarization.horizontal,sum=x=>x.reduce((s,y)=>s+y,0);
  const values={endS:i+1,verticalWireJ:sum(v.wireJ),horizontalWireJ:sum(u.wireJ),boardJ:c.boardEnergyJ,radiationLossJ:c.radLossJ,structuralLossJ:c.structuralLossJ,stringLossJ:c.polarization.stringLossJ};
  if(Object.values(values).some(x=>!Number.isFinite(x)))throw Error('invalid energy ledger');
  return values;
 });
 diagnostics.push({midi,touch,hash:q.hash,rms:q.result.rms,energy,partials:q.analysis.windows.filter(w=>[0,1,2].includes(w.startS)).map(w=>({startS:w.startS,partials:w.partials}))});
}
mkdirSync(out,{recursive:true});
const manifest=[];
for(const touch of [24,76,127]){
 const entries=[];
 for(const midi of [36,43,48])for(const count of [1,2]){
  const dir=join(input,'bass','F11D-bass-midi'+midi+'-strings'+count+'-touch'+touch);
  const q=readCase(dir,midi,touch,count);entries.push({midi,count,touch,hash:q.hash,pcm:q.pcm});
 }
 const n=144239,gap=24000,output=header(entries.length*n+(entries.length-1)*gap),dst=output.subarray(44);
 entries.forEach(({pcm,...m},i)=>{const pos=i*(n+gap)*6;dst.set(pcm,pos);if(!Buffer.from(dst.subarray(pos,pos+pcm.length)).equals(Buffer.from(pcm)))throw Error('PCM changed');manifest.push({...m,startS:i*(n+gap)/48000});});
 writeFileSync(join(out,'S50_bass_touch'+touch+'_one-two_24bit.wav'),output,{flag:'wx'});
}
writeFileSync(join(out,'upper-register-diagnostics.json'),JSON.stringify({scope:'chunk-end mechanical energy and acoustic band RMS; correlation only, not proof of cause',diagnostics},null,2),{flag:'wx'});
writeFileSync(join(out,'manifest.json'),JSON.stringify({gain,normalization:false,format:'48k stereo PCM24',manifest},null,2),{flag:'wx'});
console.log('F11E_UPPER_DIAG '+JSON.stringify(diagnostics.map(q=>({midi:q.midi,touch:q.touch,rms2:q.rms.find(w=>w.startS===2).rms,energy:q.energy,partial2:q.partials.find(w=>w.startS===2).partials.slice(0,3)}))));
