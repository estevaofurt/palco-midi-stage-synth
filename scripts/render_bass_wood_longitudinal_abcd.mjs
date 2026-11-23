/**
 * Offline listening study — 4 distinct presentations of the exact same MIDI:
 * D v1.12.7 frozen, +wood board, +longitudinal only, +both.
 * NO CHANGE to public synthesizer or existing preset defaults.
 * All files share ONE gain, 24-bit stereo/48kHz, no FX, no external piano PCM.
 */
import {mkdirSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
import {HybridPianoEngine as StableD} from '../physical-piano-hybrid-v127.js';
import {HybridPianoEngine as Candidate} from '../physical-piano-hybrid.js';

const SR=48000,BL=128,DURATION=19.5,GAP=.9;
const LENGTH=Math.ceil(DURATION*SR/BL)*BL;
const events=[];let nextId=1;
const ev=(t,type,p={})=>events.push({block:Math.round(t*SR/BL),type,...p});
function note(key,velocity,start,duration=.85){
 const id=nextId++;
 ev(start,'on',{id,key,speed:velocity/127,hardness:.58,character:'american',
   brightness:.5,send:0,decayScale:1});
 ev(start+duration,'off',{id,fast:false,release:.40});
}
// C1-A1: focus on low bridge + longitudinal character.
note(24,80,.45,1.2);
note(33,80,2.55,1.2);
note(36,32,4.65,1.25);
note(36,80,6.75,1.25);
note(36,120,8.85,1.25);
note(48,80,10.95,1.3);
note(60,80,13.05,1.25); // middle-C guard MUST be identical.
for(const [key,d] of [[36,0],[43,.008],[48,.016],[52,.025],[55,.033]])
 note(key,80,15.16+d,2.25);
events.sort((a,b)=>a.block-b.block||({off:0,on:1}[a.type]-{off:0,on:1}[b.type])||a.id-b.id);

function render(Model,study){
 const e=Model===StableD?new Model(SR,'studio'):new Model(SR,'studio',study);
 const L=new Float32Array(BL),R=new Float32Array(BL),out=new Float32Array(LENGTH*2);
 let idx=0;
 for(let pos=0;pos<LENGTH;pos+=BL){
   while(idx<events.length&&events[idx].block===pos/BL){
     const a=events[idx++];
     if(a.type==='on')e.noteOn(a);else e.noteOff(a.id,a.fast,a.release);
   }
   e.render(L,R,null,BL);
   for(let i=0;i<BL;i++){
     const l=L[i],r=R[i];if(!Number.isFinite(l)||!Number.isFinite(r))throw Error('nonfinite PCM');
     out[2*(pos+i)]=l;out[2*(pos+i)+1]=r;
   }
 }
 if(idx!==events.length)throw Error('unplayed MIDI');
 return out;
}
const maxabs=x=>{let p=0;for(const a of x)p=Math.max(p,Math.abs(a));return p};
function distance(a,b){
 let s=0,ref=0,diff=0;
 for(let i=0;i<a.length;i++){
   const d=a[i]-b[i];s+=d*d;ref+=a[i]*a[i];if(d!==0)diff++;
 }
 return {differentSamples:diff,relativeRms:Math.sqrt(s/Math.max(1e-18,ref))};
}
function wave(path,pcm,g){
 const bytes=pcm.length*3,buf=Buffer.allocUnsafe(bytes+44);
 buf.write('RIFF',0);buf.writeUInt32LE(buf.length-8,4);
 buf.write('WAVEfmt ',8);buf.writeUInt32LE(16,16);
 buf.writeUInt16LE(1,20);buf.writeUInt16LE(2,22);
 buf.writeUInt32LE(SR,24);buf.writeUInt32LE(SR*6,28);
 buf.writeUInt16LE(6,32);buf.writeUInt16LE(24,34);
 buf.write('data',36);buf.writeUInt32LE(bytes,40);
 let pos=44;
 for(const sample of pcm){
   const x=Math.max(-.99999,Math.min(.99999,sample*g));
   buf.writeIntLE(Math.round(x*8388607),pos,3);pos+=3;
 }
 writeFileSync(path,buf);
 return {name:path.split('/').pop(),bytes:buf.length,frames:pcm.length/2};
}
const dir=process.argv[2]||'artifacts/piano-bass-wood-study';
mkdirSync(dir,{recursive:true});
const modes=[
 {id:'01',key:'stable',title:'D v1.12.7 — timbre criticado (controle)',pcm:render(StableD,'off')},
 {id:'02',key:'wood',title:'D com radiação do tampo (somente)',pcm:render(Candidate,'wood')},
 {id:'03',key:'longitudinal',title:'D com vibração longitudinal (somente)',pcm:render(Candidate,'longitudinal')},
 {id:'04',key:'combined',title:'D com tampo + longitudinal',pcm:render(Candidate,'combined')}
];
const globalPeak=Math.max(...modes.map(x=>maxabs(x.pcm)));
const commonGain=.84/globalPeak;
let combinedLength=modes.reduce((s,m)=>s+m.pcm.length,0)+
  (modes.length-1)*Math.round(GAP*SR)*2;
const concatenated=new Float32Array(combinedLength);let offset=0;
for(const m of modes){
 m.startSeconds=offset/2/SR;
 concatenated.set(m.pcm,offset);offset+=m.pcm.length+Math.round(GAP*SR)*2;
}
const files=[];
for(const m of modes){
 files.push(wave(join(dir,`${m.id}_${m.key}_48k_estereo_24bit.wav`),m.pcm,commonGain));
}
files.push(wave(join(dir,'05_COMPARACAO_D_QUATRO_MODELOS_ABCD.wav'),concatenated,commonGain));
const comparisons=modes.slice(1).map(m=>({mode:m.key,...distance(modes[0].pcm,m.pcm)}));
if(comparisons.some(x=>x.differentSamples<500))
 throw Error('one or more models have no audible PCM difference');
const audit={schema:'stage-bass-wood-longitudinal-four-way-v1',
  soundEngine:'Stage D original engine; historical v1.12.7 and research branch',
  sampleRate:SR,channels:2,bits:24,gapSeconds:GAP,
  commonGain,perFileNormalization:false,fx:'off',quality:'studio',
  notes:'C1, A1, C2 pp/mf/ff, C3 mf, C4 mf, C2-G2-C3-E3-G3 chord',
  models:modes.map(({id,key,title,startSeconds})=>({id,key,title,startSeconds})),
  comparisons,files,originalPianoRecordingsEmbedded:false,
  comments:'Uncalibrated reduced soundboard and nonlinear string experiments, NOT physically identified wooden plate or true longitudinal modes; neither is an authenticated grand piano or improved acoustic realism.'
};
writeFileSync(join(dir,'metadata.json'),JSON.stringify(audit,null,2)+'\n');
writeFileSync(join(dir,'LEIA-ME.txt'),
  'STAGE SYNTH — TESTE AUDITIVO DOS GRAVES\n\n' +
  '01 = D 1.12.7 sem alterações (controle).\n' +
  '02 = D com tampo de madeira reduzido, sem novas cordas longitudinais.\n' +
  '03 = D com componentes longitudinais não lineares, sem tampo novo.\n' +
  '04 = D com ambos os mecanismos.\n' +
  '05 = As 4 versões em sequência, com 0,9 segundo de silêncio.\n\n' +
  'Todas usam a MESMA sequência MIDI, o MESMO ganho linear, sem efeitos externos.\n' +
  'PCM WAV estéreo 48kHz 24bit.\n' +
  'IMPORTANTE: pesquisa sonora, não medição física do piano; afinação e espectro não foram homologados.\n' +
  'Compare o som de C1/A1/C2/C3, batida de madeira, harmônicos e corpo sustentado.\n',
 'utf8');
console.log(JSON.stringify({globalPeak,commonGain,comparisons,files,starts:audit.models.map(x=>({mode:x.key,t:x.startSeconds}))},null,2));
