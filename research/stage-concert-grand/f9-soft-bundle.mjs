import {readFileSync,readdirSync,writeFileSync,mkdirSync,copyFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const [dir,out]=process.argv.slice(2),velocities=[.15,.25,.35,.5,1,2.5],rows=[];
mkdirSync(out,{recursive:true});
for(const sub of readdirSync(dir)){
 const d=dir+'/'+sub;
 for(const file of readdirSync(d).filter(f=>/^v[0-9.]+\.json$/.test(f))){
  const m=JSON.parse(readFileSync(d+'/'+file));if(!velocities.includes(m.velocity)||rows.some(r=>r.velocity===m.velocity)||m.gain!==.36767023440034063||m.feltFactor!==1.5)throw Error('manifest mismatch');
  const audio=readFileSync(d+'/'+m.file);if(createHash('sha256').update(audio).digest('hex')!==m.sha256.pcm24)throw Error('audio digest mismatch');
  copyFileSync(d+'/'+m.file,out+'/'+m.file);rows.push(m);
 }
}
rows.sort((a,b)=>a.velocity-b.velocity);
if(rows.length!==velocities.length||rows.some((r,i)=>r.velocity!==velocities[i]||(i&&r.pcm.rms24<=rows[i-1].pcm.rms24)))throw Error('missing or nonmonotonic levels');
const medium=rows.find(r=>r.velocity===1);
const result={scope:'matched digital gain, experimental hammer speeds, not calibrated MIDI dynamics',rows:rows.map(r=>({...r,initialRelativeToMediumDb:20*Math.log10(r.pcm.rms24/medium.pcm.rms24)}))};
writeFileSync(out+'/manifest.json',JSON.stringify(result,null,2),{flag:'wx'});
writeFileSync(out+'/LEIA-ME.txt','Comparacao de toque C4, feltro 150%. WAV stereo 48 kHz / 24 bits. Mesma regulagem de volume em todos os arquivos; desative normalizacao automatica. Velocidades 0.15, 0.25, 0.35 m/s sao novos candidatos suaves de 12 s. 0.5, 1 e 2.5 m/s sao os arquivos anteriores verificados, com duracoes 40, 20 e 40 s. Nao sao dinamicas pp/mf/ff calibradas. Compare ataque, brilho e intensidade.\n',{flag:'wx'});
console.log('F917A_BUNDLE '+JSON.stringify(result.rows.map(r=>({velocity:r.velocity,initialDbFS:r.initialDbFS,relativeDb:r.initialRelativeToMediumDb,contactSpanS:r.attack.contactSpanS,peak:r.pcm.peak24}))));
