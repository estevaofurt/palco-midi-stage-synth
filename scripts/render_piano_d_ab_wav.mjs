/**
 * Render offline authentic Stage D v1.12.6 and experimental v1.12.7.
 * Both use the ACTUAL archived/current project synthesis engines. No piano
 * recordings/samples, external DSP, MIDI files or third-party binaries.
 *
 * Output PCM WAVE 48kHz / stereo / 24-bit, matched single linear output gain,
 * fixed note/pedal schedule, no FX, no individually normalized files.
 *
 * Run: node scripts/render_piano_d_ab_wav.mjs <output-directory>
 */
import {writeFileSync,mkdirSync} from 'node:fs';
import {join} from 'node:path';
import {HybridPianoEngine as V126} from '../physical-piano-hybrid-v126.js';
import {HybridPianoEngine as V127} from '../physical-piano-hybrid.js';

const RATE=48000, BLOCK=128, DURATION=29.3, GAP_SECONDS=1.5;
const FRAMES=Math.ceil(DURATION*RATE/BLOCK)*BLOCK;
const EVENTS=[];
let nextId=1;
const schedule=(seconds,type,payload={})=>{
  if(!Number.isFinite(seconds)||seconds<0||seconds>=DURATION)throw new RangeError('bad event time');
  EVENTS.push({block:Math.round(seconds*RATE/BLOCK),seconds,type,...payload});
};
function note(key,velocity,on,held,hardness=.55){
  const id=nextId++;
  schedule(on,'on',{id,key,speed:velocity/127,hardness,brightness:.5,
    character:'american',send:0,decayScale:1});
  schedule(on+held,'off',{id,release:.42,fast:false});
}
// Repeated notes give controlled pp/mf/ff attack differences.
note(36,32,.45,1.40,.46);     // C2 pp
note(36,80,2.68,1.40,.53);    // C2 mf
note(36,120,4.91,1.37,.68);   // C2 ff
note(48,32,7.14,1.40,.46);    // C3 pp
note(48,80,9.37,1.40,.53);    // C3 mf
note(48,120,11.60,1.37,.68); // C3 ff
note(60,80,13.84,1.42,.55);  // C4 mf, unchanged engine guard
note(33,80,16.10,1.54,.55);  // A1 mf, very low bass
// A real chord: identical note/event positions and articulation.
for(const [k,delay] of [[36,0],[43,.006],[48,.012],[52,.018],[55,.023]])
  note(k,80,18.48+delay,1.72,.54);
// Passage with sustain: sympathetic strings and body respond over time.
schedule(21.87,'pedal',{value:127});
for(const [k,at,velocity] of [
  [36,22.04,74],[43,22.40,79],[48,22.78,81],
  [55,23.15,77],[60,23.53,84],[52,23.90,76],[48,24.30,73],
  [43,24.68,77],[36,25.05,80]])
  note(k,velocity,at,.46,.56);
schedule(25.98,'pedal',{value:0});

const ORDER={pedal:0,off:1,on:2};
EVENTS.sort((a,b)=>a.block-b.block||ORDER[a.type]-ORDER[b.type]||a.id-b.id);

function render(Model){
  const e=new Model(RATE,'studio'),left=new Float32Array(BLOCK),
    right=new Float32Array(BLOCK),interleaved=new Float32Array(FRAMES*2);
  let eventIndex=0;
  for(let pos=0;pos<FRAMES;pos+=BLOCK){
    const block=pos/BLOCK;
    while(eventIndex<EVENTS.length&&EVENTS[eventIndex].block===block){
      const ev=EVENTS[eventIndex++];
      if(ev.type==='on')e.noteOn(ev);
      else if(ev.type==='off')e.noteOff(ev.id,ev.fast,ev.release);
      else if(ev.type==='pedal')e.setSustain(ev.value);
    }
    e.render(left,right,null,BLOCK);
    for(let j=0;j<BLOCK;j++){
      const x=left[j],y=right[j];
      if(!Number.isFinite(x)||!Number.isFinite(y))
        throw Error('nonfinite audio at sample '+(pos+j));
      interleaved[2*(pos+j)]=x;
      interleaved[2*(pos+j)+1]=y;
    }
  }
  if(eventIndex!==EVENTS.length)throw Error('unplayed scheduled event(s)');
  return interleaved;
}
function peak(a){
  let p=0;for(const x of a){p=Math.max(p,Math.abs(x));}return p;
}
function writeWav(path,samples,gain){
  const frameCount=samples.length/2,bytes=frameCount*2*3,
    buf=Buffer.allocUnsafe(44+bytes);
  buf.write('RIFF',0,'ascii');buf.writeUInt32LE(36+bytes,4);
  buf.write('WAVE',8,'ascii');buf.write('fmt ',12,'ascii');
  buf.writeUInt32LE(16,16);buf.writeUInt16LE(1,20);
  buf.writeUInt16LE(2,22);buf.writeUInt32LE(RATE,24);
  buf.writeUInt32LE(RATE*6,28);buf.writeUInt16LE(6,32);
  buf.writeUInt16LE(24,34);buf.write('data',36,'ascii');
  buf.writeUInt32LE(bytes,40);
  let o=44;
  for(let i=0;i<samples.length;i++){
    const x=Math.max(-1,Math.min(1,samples[i]*gain));
    buf.writeIntLE(Math.round(x*8388607),o,3);o+=3;
  }
  writeFileSync(path,buf);
  return {file:path,samples:samples.length,frames:frameCount,
    durationSeconds:Number((frameCount/RATE).toFixed(4)),bytes:buf.length};
}
function linearError(a,b){
  let mismatch=0,sum=0;
  for(let i=0;i<a.length;i++){
    const d=a[i]-b[i];if(d!==0)mismatch++;
    sum+=d*d;
  }
  return {differentStereoSamples:mismatch,differenceRms:Math.sqrt(sum/a.length)};
}

const outDir=process.argv[2]||'artifacts/piano-d-ab';
mkdirSync(outDir,{recursive:true});
console.log('Rendering Stage D v1.12.6 archived synthesis engine, studio...');
const oldPCM=render(V126);
console.log('Rendering Stage D v1.12.7 finite-hammer synthesis engine, studio...');
const newPCM=render(V127);
const oldPeak=peak(oldPCM),newPeak=peak(newPCM);
if(!(oldPeak>.0001&&newPeak>.0001))throw Error('silent audio');
const linearGain=.86/Math.max(oldPeak,newPeak);
const gapFrames=Math.round(GAP_SECONDS*RATE);
const joint=new Float32Array(oldPCM.length+gapFrames*2+newPCM.length);
joint.set(oldPCM);joint.set(newPCM,oldPCM.length+gapFrames*2);

const filenames={
  old:'01_Stage_D_v1.12.6_original_48k_stereo_24bit.wav',
  new:'02_Stage_D_v1.12.7_martelo_48k_stereo_24bit.wav',
  ab:'03_COMPARACAO_AB_v126_depois_v127_48k_stereo_24bit.wav'
};
const outputs=[
 writeWav(join(outDir,filenames.old),oldPCM,linearGain),
 writeWav(join(outDir,filenames.new),newPCM,linearGain),
 writeWav(join(outDir,filenames.ab),joint,linearGain)
];
const result={
 schema:'stage-d-v126-v127-pcm24-a-b-v1',
 sampleRate:RATE,channels:2,pcmBits:24,quality:'studio',
 profile:'american',fx:'disabled',pedal:'off except melody',
 versions:[
  {name:'v1.12.6',import:'physical-piano-hybrid-v126.js',peakBeforeGain:oldPeak},
  {name:'v1.12.7',import:'physical-piano-hybrid.js',peakBeforeGain:newPeak}
 ],
 matchingGain:linearGain,individualNormalization:false,
 abGapSeconds:GAP_SECONDS,abSecondStartsSeconds:Number((FRAMES/RATE+GAP_SECONDS).toFixed(4)),
 program:[
  {time:0.45,key:36,dynamic:'pp',note:'C2'},
  {time:2.68,key:36,dynamic:'mf',note:'C2'},
  {time:4.91,key:36,dynamic:'ff',note:'C2'},
  {time:7.14,key:48,dynamic:'pp',note:'C3'},
  {time:9.37,key:48,dynamic:'mf',note:'C3'},
  {time:11.60,key:48,dynamic:'ff',note:'C3'},
  {time:13.84,key:60,dynamic:'mf',note:'C4'},
  {time:16.10,key:33,dynamic:'mf',note:'A1'},
  {time:18.48,kind:'chord',notes:'C2 G2 C3 E3 G3'},
  {time:21.87,kind:'pedalOn'},
  {time:22.04,kind:'melody',notes:'C2 G2 C3 G3 C4 E3 C3 G2 C2'},
  {time:25.98,kind:'pedalOff'}
 ],
 exactSameScheduledEvents:true,
 note:'Instrument names describe a qualitative American Grand preset; these are synthetic renderings, not Steinway piano recordings.',
 disclaimer:'Realistic piano timbre is not proven. Listening comparison may show improvement or degradation, especially in bass. No external instrument samples embedded.',
 comparison:linearError(oldPCM,newPCM),files:outputs
};
writeFileSync(join(outDir,'metadata.json'),JSON.stringify(result,null,2)+'\n');
const duration=(FRAMES/RATE).toFixed(2), second=result.abSecondStartsSeconds.toFixed(2);
const info=`STAGE SYNTH — COMPARAÇÃO AUDITIVA DO MOTOR D
Renderização dos motores REAIS do projeto, sem samples externos.
WAV PCM 24-bit • estéreo • 48.000 Hz • perfil American Grand • Estúdio • efeitos desligados.

ARQUIVOS
01_Stage_D_v1.12.6_original_48k_stereo_24bit.wav — motor D original (versão histórica arquivada)
02_Stage_D_v1.12.7_martelo_48k_stereo_24bit.wav — motor D com novo pulso de martelo grave
03_COMPARACAO_AB_v126_depois_v127_48k_stereo_24bit.wav — primeiro D 1.12.6, silêncio de 1,5s, depois D 1.12.7

COMPARAÇÃO A/B
0,00 a ${duration}s: versão 1.12.6
${duration}s a ${second}s: silêncio
${second}s em diante: versão 1.12.7

MESMAS NOTAS E VELOCIDADES MIDI NAS DUAS VERSÕES
0,45s  C2 pianíssimo (velocity 32)
2,68s  C2 médio (velocity 80)
4,91s  C2 forte (velocity 120)
7,14s  C3 pianíssimo (velocity 32)
9,37s  C3 médio (velocity 80)
11,60s C3 forte (velocity 120)
13,84s C4 médio (não deve mudar entre os motores)
16,10s A1 médio (grave profundo)
18,48s acorde C2/G2/C3/E3/G3
21,87s pedal sustain ativado
22,04s frase C2/G2/C3/G3/C4/E3/C3/G2/C2
25,98s pedal sustain desativado.

IMPORTANTE
• O mesmo ganho linear foi aplicado a TODOS os áudios. Nenhuma versão foi normalizada individualmente.
• Sem reverberação ou efeitos externos; os motores mantêm seu tampo e ressonância física internos.
• Estas são sínteses digitais; nenhum arquivo AIFF/WAV Steinway/Iowa foi incorporado.
• O novo martelo é experimental: evidência acústica mista, sem comprovação de naturalidade ou certificado de 64 notas em tempo real.
• Para um teste confiável, ouça em fones e compare o ataque, corpo e cauda nas notas graves, sem mudar volume.
`;
writeFileSync(join(outDir,'LEIA-ME.txt'),info,'utf8');
if(result.comparison.differentStereoSamples<1000)throw Error('identical engines: invalid A/B');
if(outputs.some(o=>o.bytes<1000))throw Error('truncated WAV');
console.log(JSON.stringify({files:outputs,peakOld:oldPeak,peakNew:newPeak,gain:linearGain,diff:result.comparison,
  combinedSeconds:outputs[2].durationSeconds},null,2));
