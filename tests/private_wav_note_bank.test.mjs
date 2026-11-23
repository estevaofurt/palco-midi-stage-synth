import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {parseLocalPcmWav,extractLocalNote,validatePrivateBankManifest}
 from '../research/private-wav-note-bank.mjs';
import {sampleDescriptor,SampleLibrary} from '../sample-library.js';
import {engines} from '../patches.js';

function makePcm({rate=24000,channels=2,bits=24,frames=24000,withJunk=false}={}){
 const width=bits/8,align=channels*width,meta=withJunk?12:0;
 const buffer=Buffer.alloc(44+meta+frames*align);
 buffer.write('RIFF',0);buffer.writeUInt32LE(buffer.length-8,4);buffer.write('WAVE',8);
 buffer.write('fmt ',12);buffer.writeUInt32LE(16,16);buffer.writeUInt16LE(1,20);
 buffer.writeUInt16LE(channels,22);buffer.writeUInt32LE(rate,24);
 buffer.writeUInt32LE(rate*align,28);buffer.writeUInt16LE(align,32);
 buffer.writeUInt16LE(bits,34);
 const dataAt=36+meta;
 if(withJunk){
  buffer.write('JUNK',36);buffer.writeUInt32LE(4,40);
 }
 buffer.write('data',dataAt);buffer.writeUInt32LE(frames*align,dataAt+4);
 const dataAtStart=dataAt+8;
 for(let i=0;i<frames;i++){
  const sample=Math.round(Math.sin(2*Math.PI*150*i/rate)*(bits===24?2500000:10000));
  for(let c=0;c<channels;c++)
   buffer.writeIntLE(sample,dataAtStart+i*align+c*width,width);
 }
 return buffer;
}
function manifest(source,notes=[{
 midiRoot:36,nominalVelocity:60,verifiedPitch:true,
 startSeconds:.1,durationSeconds:.3
}]){
 return {use:'private-listening-only',redistributionAuthorized:false,
  sourceSha256:createHash('sha256').update(source).digest('hex'),notes};
}
test('WAV parser recognizes actual PCM24 RIFF with non-audio metadata',()=>{
 const original=makePcm({withJunk:true});
 const x=parseLocalPcmWav(original);
 assert.equal(x.channels,2);assert.equal(x.sampleRate,24000);
 assert.equal(x.bitDepth,24);assert.equal(x.frames,24000);
 assert.equal(x.offset,56);
});
test('extracting WAV windows preserves internal PCM and fades edges',()=>{
 const source=makePcm({frames:24000});
 const crop=extractLocalNote(source,{startSeconds:.2,durationSeconds:.4},
  {fadeInMs:2,fadeOutMs:45});
 const info=parseLocalPcmWav(crop);
 assert.equal(info.frames,9600);
 assert.equal(info.bitDepth,24);assert.equal(info.channels,2);
 const originalAt=parseLocalPcmWav(source).offset;
 const sampleIndex=1000;
 const midSource=source.readIntLE(originalAt+(4800+sampleIndex)*6,3);
 const midCrop=crop.readIntLE(info.offset+sampleIndex*6,3);
 assert.equal(midCrop,midSource,'interior audio must stay bitwise identical');
 assert.ok(Math.abs(crop.readIntLE(info.offset,3))<Math.abs(midSource));
 assert.equal(crop.toString('ascii',0,4),'RIFF');
});
test('strict private SHA256 manifest validates 2 velocity layers per root',()=>{
 const source=makePcm({bits:16,channels:1});
 const m=manifest(source,[
 {midiRoot:36,nominalVelocity:60,verifiedPitch:true,startSeconds:.1,durationSeconds:.3},
 {midiRoot:36,nominalVelocity:110,verifiedPitch:true,startSeconds:.5,durationSeconds:.3}
 ]);
 const info=validatePrivateBankManifest(m,source);
 assert.deepEqual(info.names,['MIDI36_v60.wav','MIDI36_v110.wav']);
 assert.equal(parseLocalPcmWav(source).bitDepth,16);
});
test('fails closed on missing rights warning, source substitution and unverified pitch',()=>{
 const source=makePcm();
 assert.throws(()=>validatePrivateBankManifest({...manifest(source),redistributionAuthorized:true},source),RangeError);
 assert.throws(()=>validatePrivateBankManifest({...manifest(source),sourceSha256:'0'.repeat(64)},source),RangeError);
 assert.throws(()=>validatePrivateBankManifest(manifest(source,[{
  midiRoot:36,nominalVelocity:60,verifiedPitch:false,
  startSeconds:.1,durationSeconds:.3
 }]),source),RangeError);
});
test('rejects out of range, duplicates, malformed WAVE and oversized crop',()=>{
 const source=makePcm(),valid=manifest(source);
 assert.throws(()=>parseLocalPcmWav(Buffer.from('RIFFbad')),RangeError);
 assert.throws(()=>extractLocalNote(source,{startSeconds:.8,durationSeconds:.6}),RangeError);
 assert.throws(()=>validatePrivateBankManifest(manifest(source,[
  valid.notes[0],valid.notes[0]
 ]),source),RangeError);
 assert.throws(()=>validatePrivateBankManifest(manifest(source,[{
  midiRoot:200,nominalVelocity:70,verifiedPitch:true,
  startSeconds:0,durationSeconds:.5
 }]),source),RangeError);
});
test('already-built sample library can select a private MIDI pitch/layer, classic only',()=>{
 assert.deepEqual(sampleDescriptor('MIDI36_v60.wav'),{root:36,velocity:60});
 assert.deepEqual(sampleDescriptor('MIDI60_v110.wav'),{root:60,velocity:110});
 const loader=new SampleLibrary({});
 loader.banks.set('american',[
  {root:36,velocity:60,name:'low'},
  {root:36,velocity:110,name:'high'},
  {root:60,velocity:110,name:'other'}
 ]);
 assert.equal(loader.choose('american',36,65).name,'low');
 assert.equal(loader.choose('american',36,115).name,'high');
 assert.equal(loader.choose('american',80,110),null,'do not transpose more than 12 semitones');
 const controls=engines.piano.groups.flatMap(g=>g.controls);
 assert.equal(controls.filter(x=>x.type==='samplepack').length,1);
 const models=controls.find(x=>x.id==='soundEngine').options;
 assert.equal(models.classic,'Clássico · compatibilidade');
 assert.ok(models.hybrid.startsWith('D · Stage híbrido'));
 assert.equal(controls.find(x=>x.id==='soundEngine').initial,'physical');
});
