import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {inspect24,makeSequence,selfTest} from './f9-rattle-comparison.mjs';
const [cDir,eDir,outDir]=process.argv.slice(2);
const data=JSON.parse(readFileSync(new URL('../../audio/analysis_f9_19e_long_comparison.json',import.meta.url),'utf8'));
const comparison=selfTest(data.cases);
console.log('F919F_SMOKE: 8 cases, 32 windows; PCM prefix, fade, gap and validation checks passed');
if(!cDir&&!eDir&&!outDir)process.exit(0);
if(!cDir||!eDir||!outDir)throw Error('usage: node f9-rattle-comparison-demo.mjs C_DIR E_DIR OUT_DIR');
mkdirSync(outDir,{recursive:true});
const sources=[];
for(const midi of [76,127]){
 const clips=[];
 for(const [label,model] of [['C','global4'],['D','hybridGlobal3'],['E','hybridGlobal2']]){
  const c=data.cases.find(x=>x.case===model&&x.midiVelocity===midi);
  const prefix=label==='C'?'F919C':'F919E',root=label==='C'?cDir:eDir;
  const dir=join(root,prefix+'-midi'+midi+'-'+model);
  const stem='C4_MIDI'+String(midi).padStart(3,'0')+'_'+model+'_'+c.duration+'s';
  const m=JSON.parse(readFileSync(join(dir,stem+'_rattle.json'),'utf8'));
  if(m.case!==model||m.midiVelocity!==midi||m.duration!==c.duration||m.gain!==c.gain||m.peak!==c.peak||m.clipped!==0||
     m.contextualCrossing.startS!==c.contextualCrossing.startS)throw Error('source metadata mismatch '+stem);
  const pcm=readFileSync(join(dir,stem+'_24bit.wav'));
  if(inspect24(pcm).frames!==c.pair.frames)throw Error('source frames mismatch '+stem);
  sources.push({label,midi,runId:c.runId,artifactId:c.artifactId,file:stem+'_24bit.wav',sha256:createHash('sha256').update(pcm).digest('hex')});
  clips.push(pcm);
 }
 const output=makeSequence(clips);
 if(inspect24(output).frames!==528000)throw Error('expected 11s');
 writeFileSync(join(outDir,'C4_MIDI'+midi+'_C-D-E_24bit.wav'),output,{flag:'wx'});
}
writeFileSync(join(outDir,'comparison.json'),JSON.stringify(comparison,null,2),{flag:'wx'});
writeFileSync(join(outDir,'manifest.json'),JSON.stringify({format:'48k stereo PCM24',order:['C','D','E'],startsS:[0,4,8],clipS:3,gapS:1,fadeOutS:.05,normalization:false,sources},null,2),{flag:'wx'});
console.log('F919F_EXPORT: 2 fixed-gain 11s sequences, C/D/E, SHA256 manifest');
