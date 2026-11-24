import {readFileSync,readdirSync,writeFileSync,mkdirSync,copyFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const [dir,out]=process.argv.slice(2),velocities=[.06,.09,.12,.15],rows=[];
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
const medium=rows.find(r=>r.velocity===.15);
const result={scope:'matched digital gain, experimental hammer speeds, not calibrated MIDI dynamics',rows:rows.map(r=>({...r,initialRelativeTo015Db:20*Math.log10(r.pcm.rms24/medium.pcm.rms24)}))};
writeFileSync(out+'/manifest.json',JSON.stringify(result,null,2),{flag:'wx'});
writeFileSync(out+'/LEIA-ME.txt','Dó4 - comparação de toques muito suaves, WAV24 estéreo 48 kHz. 0.15 m/s é o arquivo original escolhido pelo usuário. 0.06/0.09/0.12 m/s são novos ensaios de percussão, todos com mesmo ganho, feltro 150% e perdas B. Desative normalização automática. Não são pp/ppp calibrados.\n'.replace(/\n/g,' '),{flag:'wx'});
console.log('F917C_BUNDLE '+JSON.stringify(result.rows.map(r=>({velocity:r.velocity,initialDbFS:r.initialDbFS,relativeDb:r.initialRelativeToMediumDb,contactSpanS:r.attack.contactSpanS,peak:r.pcm.peak24}))));
