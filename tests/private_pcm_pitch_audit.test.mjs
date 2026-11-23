import test from 'node:test';
import assert from 'node:assert/strict';
import {auditPrivatePcmPitch} from '../research/private-pcm-pitch-audit.mjs';
function synthetic({key=36,rate=44000,channels=2,bits=24,
  frequencies=[3,4,6],level=.12,seconds=.9}={}){
 const frames=Math.round(rate*seconds),width=bits/8,align=channels*width;
 const buf=Buffer.alloc(44+frames*align);
 buf.write('RIFF',0);buf.writeUInt32LE(buf.length-8,4);buf.write('WAVE',8);
 buf.write('fmt ',12);buf.writeUInt32LE(16,16);buf.writeUInt16LE(1,20);
 buf.writeUInt16LE(channels,22);buf.writeUInt32LE(rate,24);
 buf.writeUInt32LE(rate*align,28);buf.writeUInt16LE(align,32);
 buf.writeUInt16LE(bits,34);buf.write('data',36);
 buf.writeUInt32LE(frames*align,40);
 const f0=440*2**((key-69)/12);
 for(let i=0;i<frames;i++){
  const x=frequencies.reduce((sum,n,index)=>
   sum+(1/(index+1))*Math.sin(2*Math.PI*n*f0*i/rate),0)*level;
  const sample=Math.max(-.98,Math.min(.98,x));
  const pcm=Math.round(sample*(2**(bits-1)-1));
  for(let ch=0;ch<channels;ch++)
   buf.writeIntLE(pcm,44+i*align+ch*width,width);
 }
 return buf;
}
test('C2 remains recognizable without the fundamental or second harmonic',()=>{
 const src=synthetic({key:36,frequencies:[3,4,6],bits:24});
 const audit=auditPrivatePcmPitch(src,{midiRoot:36});
 assert.ok(audit.supportsLabeledSemitone,JSON.stringify(audit));
 assert.ok(audit.semitoneContrastDb>5);
 assert.equal(audit.verifiedAbsolutePitch,false);
 assert.equal(audit.commercialRightsVerified,false);
});
test('neighboring semitone mislabeled as C2 is flagged',()=>{
 const src=synthetic({key:37,frequencies:[1,2,3,4]});
 const audit=auditPrivatePcmPitch(src,{midiRoot:36});
 assert.equal(audit.supportsLabeledSemitone,false);
 assert.ok(audit.semitoneContrastDb<0);
});
test('recognizes C4 mono PCM16 and rejects zero signal as evidence',()=>{
 const good=auditPrivatePcmPitch(synthetic({key:60,channels:1,bits:16,
  frequencies:[1,2,4]}),{midiRoot:60});
 assert.ok(good.supportsLabeledSemitone,JSON.stringify(good));
 const zero=auditPrivatePcmPitch(synthetic({key:60,level:0}),{midiRoot:60});
 assert.equal(zero.supportsLabeledSemitone,false);
 assert.equal(zero.verifiedAbsolutePitch,false);
});
test('rejects out-of-range roots, truncated windows, and invalid WAV',()=>{
 const source=synthetic({});
 assert.throws(()=>auditPrivatePcmPitch(source,{midiRoot:250}),RangeError);
 assert.throws(()=>auditPrivatePcmPitch(source,{midiRoot:36,
  offsetSeconds:.8,analysisSeconds:.3}),RangeError);
 assert.throws(()=>auditPrivatePcmPitch(Buffer.from('bad'),{midiRoot:36}),RangeError);
});
