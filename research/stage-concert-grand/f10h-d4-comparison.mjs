import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {inspect24,makeSequence} from './f9-rattle-comparison.mjs';
import {levelCrossing} from './f9-long-analysis.mjs';
import {contextualCrossing} from './f9-acceptance-analysis.mjs';
const [input,out]=process.argv.slice(2);
if(!input||!out)throw Error('input and output required');
const data=['e','f','g'].map(stage=>JSON.parse(readFileSync(new URL('../../audio/analysis_f10'+stage+'_d4_ci.json',import.meta.url),'utf8')));
const sources=[],metrics=[],gain=.36767023440034063,threshold=.0006518758466381057;
mkdirSync(out,{recursive:true});
for(const touch of [24,127]){
 const clips=[],clipS=touch===24?15:35;
 for(const [i,label,model] of [[0,'D4','D4'],[1,'S50','D4-loss50'],[2,'S25','D4-loss25']]){
  const c=data[i].cases.find(x=>x.case===model&&x.midi===60&&x.midiVelocity===touch);
  if(!c||c.status!=='completed'||c.clipped!==0||c.gain!==gain||c.threshold!==threshold)throw Error('incomparable source');
  const duration=touch===24?20:40,stem=model+'_MIDI60_touch'+touch+'_'+duration+'s',dir=join(input,label+'-'+touch);
  const meta=JSON.parse(readFileSync(join(dir,stem+'_rattle.json'),'utf8'));
  const analysis=JSON.parse(readFileSync(join(dir,stem+'_float_analysis.json'),'utf8'));
  if(meta.case!==model||meta.midi!==60||meta.midiVelocity!==touch||meta.duration!==duration||meta.gain!==gain||meta.peak!==c.peak||meta.clipped!==0||meta.threshold!==threshold)throw Error('metadata mismatch');
  const pcm=readFileSync(join(dir,stem+'_24bit.wav'));
  if(inspect24(pcm).frames!==c.pair.frames||c.pair.frames!==duration*48000+239||analysis.rate!==48000||analysis.windowS!==.5)throw Error('source shape');
  const rms=analysis.windows.map(w=>w.rms);
  if(rms.length!==duration*2-1||rms.some(v=>!Number.isFinite(v)||v<=0))throw Error('invalid RMS');
  const cross=contextualCrossing(analysis.windows,threshold);
  if(JSON.stringify(cross)!==JSON.stringify(c.contextualCrossing))throw Error('crossing mismatch');
  const relative=Object.fromEntries([20,40,60].map(d=>[d,levelCrossing(rms,.5,d)]));
  if(JSON.stringify(relative)!==JSON.stringify(c.relativeDrops))throw Error('relative crossing mismatch');
  metrics.push({label,touch,crossing:cross,relative,rmsAtTimes:[0,2,5,10,15,19,29,34,39].filter(t=>t<analysis.analyzedThroughS).map(t=>({s:t,rms:rms[2*t],relativeDb:20*Math.log10(rms[2*t]/rms[0])})),partialDrops:analysis.partialDrops});
  sources.push({label,touch,runId:data[i].runId,artifactId:c.artifactId,sha256:createHash('sha256').update(pcm).digest('hex')});
  clips.push(pcm);
 }
 const output=makeSequence(clips,{clipFrames:clipS*48000,gapFrames:48000,fadeFrames:2400});
 if(inspect24(output).frames!==(3*clipS+2)*48000)throw Error('sequence length');
 const dst=inspect24(output).pcm;
 for(let k=0;k<3;k++){
  const src=inspect24(clips[k]).pcm,p=k*(clipS+1)*48000*6,end=(clipS*48000-2400)*6;
  if(!Buffer.from(dst.subarray(p,p+end)).equals(Buffer.from(src.subarray(0,end))))throw Error('PCM prefix altered');
  if(k<2&&dst.subarray(p+clipS*48000*6,p+(clipS+1)*48000*6).some(v=>v!==0))throw Error('gap not zero');
 }
 writeFileSync(join(out,'C4_touch'+touch+'_D4-S50-S25_24bit.wav'),output,{flag:'wx'});
}
writeFileSync(join(out,'comparison.json'),JSON.stringify({gain,threshold,metrics},null,2),{flag:'wx'});
writeFileSync(join(out,'manifest.json'),JSON.stringify({order:['D4','S50','S25'],softStartsS:[0,16,32],strongStartsS:[0,36,72],softClipS:15,strongClipS:35,gapS:1,fadeS:.05,normalization:false,sources},null,2),{flag:'wx'});
console.log('F10H_COMPARISON '+JSON.stringify(metrics.map(({partialDrops,...m})=>m)));
