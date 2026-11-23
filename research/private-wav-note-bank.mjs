/**
 * E2.6 — LOCAL ONLY: extract manually verified note windows from user WAVs.
 * No model DSP, no redistribution and no cloud loading. Metadata is NOT proof
 * of the user's commercial licensing rights. Do not commit input/outputs.
 * Supports little-endian PCM16/24 WAV with arbitrary RIFF metadata chunks.
 */
import {createHash} from 'node:crypto';

const safeInt=(v,lo,hi,label)=>{
  if(!Number.isInteger(v)||v<lo||v>hi)throw new RangeError(label);
  return v;
};
export function parseLocalPcmWav(source){
  if(!Buffer.isBuffer(source)||source.length<44||
     source.toString('ascii',0,4)!=='RIFF'||
     source.toString('ascii',8,12)!=='WAVE')
    throw new RangeError('expected ordinary RIFF/WAVE PCM');
  const end=8+source.readUInt32LE(4);
  if(end>source.length||end<44)throw new RangeError('truncated RIFF');
  let fmt=null,data=null;
  for(let at=12;at+8<=end;){
    const id=source.toString('ascii',at,at+4),length=source.readUInt32LE(at+4);
    const start=at+8,stop=start+length;
    if(stop>end)throw new RangeError('malformed WAV chunk');
    if(id==='fmt '){
      if(length<16)throw new RangeError('invalid fmt');
      fmt={format:source.readUInt16LE(start),channels:source.readUInt16LE(start+2),
        sampleRate:source.readUInt32LE(start+4),
        byteRate:source.readUInt32LE(start+8),blockAlign:source.readUInt16LE(start+12),
        bitsPerSample:source.readUInt16LE(start+14)};
    }else if(id==='data'&&!data)data={offset:start,length};
    at=stop+(length&1);
  }
  if(!fmt||!data||fmt.format!==1||
     ![16,24].includes(fmt.bitsPerSample)||
     !Number.isInteger(fmt.channels)||fmt.channels<1||fmt.channels>2||
     !Number.isInteger(fmt.sampleRate)||fmt.sampleRate<22050||fmt.sampleRate>96000||
     fmt.blockAlign!==fmt.channels*fmt.bitsPerSample/8||
     fmt.byteRate!==fmt.sampleRate*fmt.blockAlign||
     data.length%fmt.blockAlign)
    throw new RangeError('requires PCM16/24 mono/stereo 22.05–96k WAV');
  return {...fmt,offset:data.offset,dataBytes:data.length,
    frames:data.length/fmt.blockAlign,
    durationSeconds:data.length/fmt.blockAlign/fmt.sampleRate};
}
export function extractLocalNote(source,window,{fadeInMs=2,fadeOutMs=45}={}){
  const fmt=parseLocalPcmWav(source);
  if(!window||!Number.isFinite(window.startSeconds)||window.startSeconds<0||
     !Number.isFinite(window.durationSeconds)||window.durationSeconds<.10||
     !Number.isFinite(fadeInMs)||fadeInMs<0||fadeInMs>50||
     !Number.isFinite(fadeOutMs)||fadeOutMs<0||fadeOutMs>250)
    throw new RangeError('invalid private note extraction window');
  const frameStart=Math.round(window.startSeconds*fmt.sampleRate);
  const frames=Math.round(window.durationSeconds*fmt.sampleRate);
  if(frameStart+frames>fmt.frames||frames<=1)throw new RangeError('note window out of bounds');
  const bytes=frames*fmt.blockAlign;
  const output=Buffer.alloc(44+bytes);
  output.write('RIFF',0);output.writeUInt32LE(36+bytes,4);output.write('WAVE',8);
  output.write('fmt ',12);output.writeUInt32LE(16,16);
  output.writeUInt16LE(1,20);output.writeUInt16LE(fmt.channels,22);
  output.writeUInt32LE(fmt.sampleRate,24);
  output.writeUInt32LE(fmt.byteRate,28);
  output.writeUInt16LE(fmt.blockAlign,32);
  output.writeUInt16LE(fmt.bitsPerSample,34);
  output.write('data',36);output.writeUInt32LE(bytes,40);
  source.copy(output,44,fmt.offset+frameStart*fmt.blockAlign,
    fmt.offset+(frameStart+frames)*fmt.blockAlign);
  const startFade=Math.round(fadeInMs/1000*fmt.sampleRate);
  const endFade=Math.round(fadeOutMs/1000*fmt.sampleRate);
  const width=fmt.bitsPerSample/8;
  for(let i=0;i<frames;i++){
    const gain=Math.min(1,startFade>0?(i+1)/startFade:1,
      endFade>0?(frames-i)/endFade:1);
    if(gain>=1)continue;
    for(let channel=0;channel<fmt.channels;channel++){
      const at=44+i*fmt.blockAlign+channel*width;
      const sample=output.readIntLE(at,width);
      output.writeIntLE(Math.round(sample*gain),at,width);
    }
  }
  return output;
}
export function validatePrivateBankManifest(manifest,source){
  const fmt=parseLocalPcmWav(source);
  if(!manifest||manifest.use!=='private-listening-only'||
    manifest.redistributionAuthorized!==false||
    typeof manifest.sourceSha256!=='string'||
    !/^[a-f0-9]{64}$/.test(manifest.sourceSha256))
    throw new RangeError('private-only source provenance and SHA256 required');
  const sha=createHash('sha256').update(source).digest('hex');
  if(sha!==manifest.sourceSha256)throw new RangeError('source SHA256 does not match manifest');
  if(!Array.isArray(manifest.notes)||!manifest.notes.length||manifest.notes.length>128)
    throw new RangeError('expected 1..128 verified notes');
  const seen=new Set();
  for(const note of manifest.notes){
    safeInt(note.midiRoot,21,108,'MIDI root');
    safeInt(note.nominalVelocity,1,127,'nominal velocity');
    if(note.verifiedPitch!==true)
      throw new RangeError('note key must have been verified separately');
    const filename=`MIDI${note.midiRoot}_v${note.nominalVelocity}.wav`;
    if(seen.has(filename))throw new RangeError('duplicate sample key and velocity');
    seen.add(filename);
    if(!Number.isFinite(note.startSeconds)||note.startSeconds<0||
      !Number.isFinite(note.durationSeconds)||note.durationSeconds<.10||
      note.startSeconds+note.durationSeconds>fmt.durationSeconds+.000001)
      throw new RangeError('invalid note bounds');
  }
  return {sampleRate:fmt.sampleRate,channels:fmt.channels,bitDepth:fmt.bitsPerSample,
    fileCount:seen.size,sourceSha256:sha,names:[...seen]};
}
