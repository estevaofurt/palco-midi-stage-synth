// A/B using one original MIDI-like performance, without commercial audio.
// The supplied user WAVs are for private analysis only; no sample copying.
import {mkdirSync,writeFileSync} from 'node:fs';
import {PhysicalPianoEngine as Old} from '../../Stage_Synth_v1_9_5/physical-piano.js';
import {PhysicalPianoEngine as New} from '../physical-piano.js';
const sr=48000, duration=8.3;
const notes=[
  {key:36,start:0,stop:1.14,velocity:.72},
  {key:60,start:1.35,stop:2.38,velocity:.32},
  {key:60,start:2.65,stop:3.78,velocity:.92},
  {key:84,start:4.0,stop:5.15,velocity:.80},
  ...[48,52,55,60,64].map((key,i)=>({key,start:5.35+i*.08,stop:6.55+i*.04,velocity:.72})),
];
function render(Engine){
  const engine=new Engine(sr,'eco'),n=Math.round(sr*duration);
  const L=new Float32Array(n),R=new Float32Array(n), l=new Float32Array(128),r=new Float32Array(128),s=new Float32Array(128);
  let started=0,ended=new Set();
  for(let pos=0;pos<n;pos+=128){
    const t=pos/sr;
    for(let i=0;i<notes.length;i++){
      const note=notes[i];
      if(note.start<=t&&!(note.id)){note.id=i+1;engine.noteOn({id:i+1,key:note.key,speed:note.velocity,hardness:.52,character:'japanese',brightness:.64});}
      if(note.stop<=t&&note.id&&!ended.has(i)){engine.noteOff(i+1,false,.6);ended.add(i)}
    }
    const size=Math.min(128,n-pos);engine.render(l,r,s,size);L.set(l.subarray(0,size),pos);R.set(r.subarray(0,size),pos);
  }
  return [L,R];
}
function stats(arr){let sq=0,peak=0;for(const ch of arr)for(let i=0;i<ch.length;i++){sq+=ch[i]*ch[i];peak=Math.max(peak,Math.abs(ch[i]));}return {rms:Math.sqrt(sq/(2*arr[0].length)),peak};}
function wav(path,L,R){
  const buffer=Buffer.alloc(44+L.length*4);buffer.write('RIFF',0);buffer.writeUInt32LE(buffer.length-8,4);buffer.write('WAVEfmt ',8);buffer.writeUInt32LE(16,16);
  buffer.writeUInt16LE(1,20);buffer.writeUInt16LE(2,22);buffer.writeUInt32LE(sr,24);buffer.writeUInt32LE(sr*4,28);buffer.writeUInt16LE(4,32);buffer.writeUInt16LE(16,34);
  buffer.write('data',36);buffer.writeUInt32LE(L.length*4,40);
  for(let i=0;i<L.length;i++){
    buffer.writeInt16LE(Math.max(-32768,Math.min(32767,Math.round(L[i]*32767))),44+i*4);
    buffer.writeInt16LE(Math.max(-32768,Math.min(32767,Math.round(R[i]*32767))),46+i*4);
  }
  writeFileSync(path,buffer);
}
const a=render(Old); // render() mutates note ids — clear before B!
for(const note of notes)delete note.id;
const b=render(New);const before=stats(a),after=stats(b);
// RMS-normalized with a shared additional gain ceiling to prevent clipping.
const target=.12,maxPeak=Math.max(before.peak*target/before.rms,after.peak*target/after.rms);
const gain=Math.min(1,.72/maxPeak);
for(const [audio,info] of [[a,before],[b,after]]){
  const scale=gain*target/info.rms;
  for(const ch of audio)for(let i=0;i<ch.length;i++)ch[i]*=scale;
}
const out='/mnt/data/Stage_Synth_v1_9_6/demos';mkdirSync(out,{recursive:true});
wav(out+'/Japanese_v195.wav',...a);wav(out+'/Japanese_v196_martelo.wav',...b);
const pause=Math.round(sr*.8),length=a[0].length+pause+b[0].length;
const combined=[new Float32Array(length),new Float32Array(length)];
for(let c=0;c<2;c++){combined[c].set(a[c],0);combined[c].set(b[c],a[0].length+pause)}
wav(out+'/A_B_Japanese_v195_vs_v196.wav',...combined);
console.log(JSON.stringify({before,after,renderedFiles:3},null,2));
