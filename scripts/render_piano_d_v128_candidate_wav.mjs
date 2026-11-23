/**
 * Original Stage D v1.12.7 vs. isolated D bass-unison v1.12.8 candidate.
 * The PCM is rendered by THE PROJECT'S ENGINES (no sampled pianos).
 *
 * node scripts/render_piano_d_v128_candidate_wav.mjs <output-dir>
 * WAV PCM24 stereo 48000Hz; common linear gain, identical note events,
 * no EQ/reverb/mastering and no separate per-note normalization.
 */
import {writeFileSync,mkdirSync} from 'node:fs';
import {join} from 'node:path';
import {HybridPianoEngine as V127} from '../physical-piano-hybrid-v127.mjs';
import {HybridPianoEngine as Candidate} from '../physical-piano-hybrid-v128-candidate.mjs';
const RATE=48000,BLOCK=128,SECONDS=2.35;
const GROUP_FRAMES=Math.ceil(SECONDS*RATE/BLOCK)*BLOCK;
const GAP_FRAMES=Math.round(.28*RATE);
const PAIR_GAP_FRAMES=Math.round(.30*RATE);
const EVENTS=[
  {label:'C2 pianissimo',notes:[[36,32]]},
  {label:'C2 mezzo forte',notes:[[36,80]]},
  {label:'C2 fortissimo',notes:[[36,120]]},
  {label:'F1 mezzo forte',notes:[[29,80]]},
  {label:'A1 mezzo forte',notes:[[33,80]]},
  {label:'C3 mezzo forte - unchanged guard',notes:[[48,80]]},
  {label:'C4 mezzo forte - unchanged guard',notes:[[60,80]]},
  {label:'C2 G2 C3 E3 G3 bass chord',notes:[[36,79],[43,78],[48,80],[52,81],[55,76]]}
];
const midiHz=k=>440*2**((k-69)/12);
function renderGroup(Model,event){
 const e=new Model(RATE,'studio'),l=new Float32Array(BLOCK),r=new Float32Array(BLOCK);
 const left=new Float32Array(GROUP_FRAMES),right=new Float32Array(GROUP_FRAMES);
 const onBlock=Math.round(.22*RATE/BLOCK),offBlock=Math.round(1.55*RATE/BLOCK);
 let peak=0;
 for(let pos=0;pos<GROUP_FRAMES;pos+=BLOCK){
  const block=pos/BLOCK;
  if(block===onBlock){
   let id=1;
   for(const [key,v] of event.notes){
    e.noteOn({id:id++,key,speed:v/127,hardness:.55,brightness:.5,
      character:'american',send:0,decayScale:1});
   }
  }
  if(block===offBlock){
   for(let id=1;id<=event.notes.length;id++)e.noteOff(id,false,.4);
  }
  e.render(l,r,null,BLOCK);
  for(let i=0;i<BLOCK;i++){
   left[pos+i]=l[i];right[pos+i]=r[i];
   if(!Number.isFinite(l[i])||!Number.isFinite(r[i]))throw Error('nonfinite PCM');
   peak=Math.max(peak,Math.abs(l[i]),Math.abs(r[i]));
  }
 }
 return {left,right,peak};
}
const old=EVENTS.map(x=>renderGroup(V127,x));
const fresh=EVENTS.map(x=>renderGroup(Candidate,x));
const peak=Math.max(...[...old,...fresh].map(x=>x.peak));
if(!(peak>.0001&&peak<1))throw Error('unexpected original-synth peak '+peak);
const gain=.84/peak;
function concatTrack(groups){
 const len=groups.length*GROUP_FRAMES+(groups.length-1)*GAP_FRAMES;
 const l=new Float32Array(len),r=new Float32Array(len);
 let offset=0;
 for(let g=0;g<groups.length;g++){
  l.set(groups[g].left,offset);r.set(groups[g].right,offset);
  offset+=GROUP_FRAMES+GAP_FRAMES;
 }
 return {l,r,length:len};
}
const a=concatTrack(old),b=concatTrack(fresh);
function composeAB(a,b){
 const l=new Float32Array(a.length+PAIR_GAP_FRAMES+b.length),
   r=new Float32Array(l.length);
 l.set(a.l);r.set(a.r);
 l.set(b.l,a.length+PAIR_GAP_FRAMES);r.set(b.r,a.length+PAIR_GAP_FRAMES);
 return {l,r,length:l.length};
}
function encode(path,pcm){
 const n=pcm.length,len=n*6,buf=Buffer.allocUnsafe(44+len);
 buf.write('RIFF',0,'ascii');buf.writeUInt32LE(36+len,4);
 buf.write('WAVE',8,'ascii');buf.write('fmt ',12,'ascii');
 buf.writeUInt32LE(16,16);buf.writeUInt16LE(1,20);buf.writeUInt16LE(2,22);
 buf.writeUInt32LE(RATE,24);buf.writeUInt32LE(RATE*6,28);
 buf.writeUInt16LE(6,32);buf.writeUInt16LE(24,34);
 buf.write('data',36,'ascii');buf.writeUInt32LE(len,40);
 let peakOut=0;
 for(let i=0;i<n;i++){
  const x=Math.max(-1,Math.min(1,pcm.l[i]*gain));
  const y=Math.max(-1,Math.min(1,pcm.r[i]*gain));
  peakOut=Math.max(peakOut,Math.abs(x),Math.abs(y));
  buf.writeIntLE(Math.round(x*8388607),44+6*i,3);
  buf.writeIntLE(Math.round(y*8388607),47+6*i,3);
 }
 writeFileSync(path,buf);
 return {name:path.split('/').at(-1),bytes:buf.length,frames:n,seconds:Number((n/RATE).toFixed(4)),peakOut};
}
function rms(pcm,start,finish){
 let sum=0,count=0;
 for(let i=Math.round(start*RATE);i<Math.round(finish*RATE);i++){
  sum+=.5*(pcm.left[i]*pcm.left[i]+pcm.right[i]*pcm.right[i]);
  count++;
 }
 return Math.sqrt(sum/Math.max(1,count));
}
const round=x=>Number(x.toFixed(3));
const logDelta=(old,newV,start,finish)=>
 round(20*Math.log10(Math.max(1e-10,rms(newV,start,finish))/
                         Math.max(1e-10,rms(old,start,finish))));
const metrics=EVENTS.map((e,i)=>{
 const x=old[i],y=fresh[i];
 let sampleDifferences=0;
 for(let j=0;j<GROUP_FRAMES;j++)
  if(x.left[j]!==y.left[j]||x.right[j]!==y.right[j])sampleDifferences++;
 return {label:e.label,notes:e.notes,first12msDb:logDelta(x,y,.22,.232),
   body100to220msDb:logDelta(x,y,.32,.44),
   late900to1300msDb:logDelta(x,y,1.12,1.52),
   changedFrames:sampleDifferences};
});
for(const record of metrics){
 const keys=record.notes.map(x=>x[0]);
 if(keys.every(k=>k<29||k>=37)&&record.changedFrames!==0)
  throw Error('unmodified notes changed: '+record.label);
 if(keys.some(k=>k>=29&&k<=36)&&record.changedFrames<2000)
  throw Error('experimental notes did not change enough: '+record.label);
}
const dir=process.argv[2]||'artifacts/stage-d-v128';
mkdirSync(dir,{recursive:true});
const files=[
 encode(join(dir,'01_Stage_D_v127_original.wav'),a),
 encode(join(dir,'02_Stage_D_v128_bass_unison_experimental.wav'),b),
 encode(join(dir,'03_AB_D_v127_depois_v128_experimental.wav'),composeAB(a,b))
];
const meta={schema:'stage-original-d-v127-v128-bass-unison-ab-v1',
  source:'actual Stage Synth HybridPianoEngine source files',
  sampleRate:RATE,channels:2,bits:24,quality:'studio',
  sourceVersions:['physical-piano-hybrid-v127.mjs','physical-piano-hybrid-v128-candidate.mjs'],
  masterLinearGain:gain,individuallyNormalized:false,
  soundDesign:'Bass F1 through C2 bichord approximation. No novel additive board modes or external samples.',
  noExternalAudio:true,noFX:true,
  historicalFirst:true,secondBeginsSeconds:Number(((a.length+PAIR_GAP_FRAMES)/RATE).toFixed(4)),
  groupSeconds:Number((GROUP_FRAMES/RATE).toFixed(4)),
  groups:EVENTS,relativeMetricsDb:metrics,files};
writeFileSync(join(dir,'metadata.json'),JSON.stringify(meta,null,2)+'\n');
console.log(JSON.stringify({gain,secondBeginsSeconds:meta.secondBeginsSeconds,
  metrics,files},null,2));
