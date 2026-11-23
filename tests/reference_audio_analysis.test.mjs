import test from 'node:test';
import assert from 'node:assert/strict';
import {decodeF32le,locateAttack,compareSpectralShape,measureEarlyPartials} from '../scripts/analyze_reference_audio.mjs';

test('E0 decodes little-endian mono PCM without modifying velocity',()=>{
 const buf=Buffer.alloc(48000*2*4);
 for(let i=0;i<96000;i++)buf.writeFloatLE(i<48000?.15:0,i*4);
 const pcm=decodeF32le(buf);
 assert.equal(pcm.length,96000);
 assert.ok(Math.abs(pcm[200]-.15)<1e-7);
});
test('E0 locates deliberate attack after a silent pre-roll',()=>{
 const pcm=new Float32Array(48000*3);
 for(let i=24000;i<pcm.length;i++)pcm[i]=.2*Math.sin(2*Math.PI*261.6*(i-24000)/48000);
 const onset=locateAttack(pcm);
 assert.ok(onset>=.49&&onset<=.51,'attack '+onset);
});
test('E0 rejects a silent recording and malformed float stream',()=>{
 assert.throws(()=>decodeF32le(Buffer.alloc(7)),/aligned/);
 assert.throws(()=>locateAttack(new Float32Array(48000)),/too quiet/);
});
test('E0 reports relative spectral differences and excludes a weak partial',()=>{
 const measured={harmonics:[
  {n:1,measuredHz:261.6,relativeDb:0},
  {n:2,measuredHz:523.5,relativeDb:-3},
  {n:3,measuredHz:790,relativeDb:-35},
  {n:4,measuredHz:1050,relativeDb:-20}
 ]};
 const reference={harmonics:[{n:1,relativeDb:0},{n:2,relativeDb:-6},{n:3,relativeDb:-10},{n:4,relativeDb:-17}]};
 const c=compareSpectralShape(measured,reference);
 assert.equal(c.comparablePartials,2);
 assert.equal(c.meanAbsDb,null,'two partials are insufficient to rank a spectrum');
 assert.equal(c.insufficientPartials,true);
 assert.ok(Math.abs(c.exploratoryMeanAbsDb-3)<1e-9);
});

test('E0 short attack window identifies fast-decaying C6 harmonics without inventing a B coefficient',()=>{
 const RATE=48000,f0=440*2**((84-69)/12),pcm=new Float32Array(Math.round(1.7*RATE));
 for(let i=0;i<pcm.length;i++){
  const t=i/RATE;
  let x=0;
  for(let n=1;n<=6;n++)x+=.12*Math.exp(-t*3*n)/n*Math.sin(2*Math.PI*f0*n*t);
  pcm[i]=x;
 }
 const early=measureEarlyPartials(pcm,84);
 assert.equal(early.fftSize,8192);
 assert.ok(early.visibleUpperPartials>=3,'detected='+early.visibleUpperPartials);
 assert.equal('bMedian' in early,false,'attack is not a stationary B measurement');
});
