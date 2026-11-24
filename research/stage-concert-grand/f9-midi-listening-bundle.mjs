import {readFileSync,writeFileSync,mkdirSync,copyFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {hammerSpeed} from './f9-midi-velocity.mjs';
import {concatenate24} from './f9-midi-listening-sequence.mjs';
import {inspectPair} from './f9-soft-pcm-audit.mjs';
import {decodeCanonical24,attackSpectrum} from './f9-attack-spectrum.mjs';
import {fft} from './f8-render.mjs';
const [dir,out]=process.argv.slice(2),levels=[1,4,8,12,16,20,24,36,52,76,100,127],gain=.36767023440034063;
mkdirSync(out,{recursive:true});const rows=[],clips=[];
for(const m of levels){
 const stem='C4_MIDI'+String(m).padStart(3,'0')+'_2s',base=dir+'/F918A-midi'+m+'/'+stem,meta=JSON.parse(readFileSync(base+'.json')),a=JSON.parse(readFileSync(base+'_float_analysis.json'));
 if(meta.midiVelocity!==m||meta.velocity!==hammerSpeed(m)||meta.duration!==2||meta.gain!==gain||meta.feltFactor!==1.5||meta.clipped!==0||meta.chunks.length!==2||meta.chunks.some(c=>c.midiVelocity!==m||c.maxBalance>1e-9||c.maxIncrease>1e-9))throw Error('render metadata mismatch');
 const pcm16=readFileSync(base+'.wav'),pcm24=readFileSync(base+'_24bit.wav'),q=inspectPair(pcm16,pcm24);
 if(q.frames!==96239||Math.abs(q.rms24-a.windows[0].rms)>.5/8388607+1e-12||Math.abs(q.peak24-meta.peak)>.5/8388607+1e-12)throw Error('PCM mismatch');
 const channels=decodeCanonical24(pcm24),spectrum=attackSpectrum(channels,48000,fft,{startS:0,endS:.05});
 const file=stem+'_24bit.wav';
 copyFileSync(base+'_24bit.wav',out+'/'+file);clips.push(pcm24);
 rows.push({midiVelocity:m,velocity:meta.velocity,file,sha256:createHash('sha256').update(pcm24).digest('hex'),pcm:q,attack:meta.chunks[0].attack,spectrum});
}
const sequences=[];
for(const [name,count] of [['01_MIDI_SUAVE_CRESCENTE',7],['02_MIDI_DINAMICA_COMPLETA',levels.length]]){
 const q=concatenate24(clips.slice(0,count));const file=name+'.wav';
 writeFileSync(out+'/'+file,q.bytes,{flag:'wx'});
 sequences.push({file,seconds:q.frames/48000,placements:q.placements.map((p,i)=>({...p,midiVelocity:levels[i],startS:p.startFrame/48000}))});
}
const result={scope:'independent physical strikes concatenated losslessly, 2s per strike plus acoustic delay and .5s silence, editorial 40ms end fade from original export; not repeated-note/pedal simulation',gain,rows,sequences,monotoneInitialRms:rows.every((r,i)=>i===0||r.pcm.rms24>rows[i-1].pcm.rms24)};
writeFileSync(out+'/manifest.json',JSON.stringify(result,null,2),{flag:'wx'});
writeFileSync(out+'/LEIA-ME.txt','Ouça 01 para níveis MIDI 1 a 24 e 02 para toda a progressão. As notas são Dó4 isolados, não execução MIDI em tempo real. Cada nota tem 2 s de render mais atraso acústico, fade editorial de 40 ms e 0,5 s de silêncio entre notas. Não avalie sustain longo por estes trechos. Mantenha volume fixo e desative normalização. Os arquivos individuais são idênticos aos trechos das sequências.\n',{flag:'wx'});
console.log('F918A_LISTENING '+JSON.stringify(result));
