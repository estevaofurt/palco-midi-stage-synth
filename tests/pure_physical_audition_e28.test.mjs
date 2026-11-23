import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {makePurePhysicalScore,renderPurePhysicalMechanical,
        encodeNormalizedMechanicalWav16}
 from '../research/pure-physical-audition-e28.mjs';

test('physical score has arpeggios, chords and mechanical pedal events',()=>{
 const events=makePurePhysicalScore();
 const on=events.filter(e=>e.type==='on');
 assert.ok(on.length>=30);
 assert.ok(on.some(x=>x.key===48));
 assert.ok(on.some(x=>x.key===72));
 assert.ok(events.some(e=>e.type==='pedal'&&e.cc===127));
 assert.ok(events.some(e=>e.type==='pedal'&&e.cc===0));
});
test('E2.8 auditions import only passive mechanical DSP, no piano recordings',()=>{
 const impl=readFileSync(new URL('../research/pure-physical-audition-e28.mjs',import.meta.url),'utf8');
 const renderer=readFileSync(new URL('../scripts/render_pure_physical_e28.mjs',import.meta.url),'utf8');
 assert.match(impl,/from '\.\/shared-passive-modal-piano\.mjs'/);
 assert.doesNotMatch(impl,/^import .*sample-library|^import .*\.wav|^import .*sf2-reader|^import .*measured-radiation-adapter/gm);
 assert.doesNotMatch(renderer,/^import .*sample-library|^import .*\.wav|^import .*sf2-reader/gm);
});
test('single-note and full mechanical score have finite, non-silent, passive response',()=>{
 const score=[
  {seconds:.02,type:'on',key:36,velocity:95},
  {seconds:.32,type:'off',key:36}
 ];
 const out=renderPurePhysicalMechanical({sampleRate:24000,seconds:.8,score});
 assert.ok(out.peakMechanical>0);
 assert.equal(out.diagnostics.connectedKeys,88);
 assert.equal(out.diagnostics.sharedBoardCoordinates,2);
 assert.ok(out.diagnostics.mechanicalStringCoordinates>176);
 assert.ok(out.diagnostics.balanceRelativeError<1e-7);
 assert.equal(out.diagnostics.acousticRealismVerified,false);
 assert.equal(out.diagnostics.source.includes('zero PCM samples'),true);
});
test('physical-only mechanical audition deterministic bit-for-bit given score',()=>{
 const score=[
  {seconds:.04,type:'pedal',cc:127},
  {seconds:.06,type:'on',key:48,velocity:70},
  {seconds:.16,type:'on',key:55,velocity:80},
  {seconds:.32,type:'off',key:48},
  {seconds:.36,type:'off',key:55},
  {seconds:.4,type:'pedal',cc:0}
 ];
 const opts={sampleRate:24000,seconds:.7,score,partialsBass:3,partialsTreble:2};
 const a=renderPurePhysicalMechanical(opts),b=renderPurePhysicalMechanical(opts);
 assert.deepEqual(a.signal,b.signal);
});
test('physical preview WAV PCM16 mono follows global scale, remains below clip',()=>{
 const score=[{seconds:.05,type:'on',key:48,velocity:90}];
 const {signal}=renderPurePhysicalMechanical({sampleRate:24000,seconds:.5,score});
 const {wav,gain}=encodeNormalizedMechanicalWav16(signal,24000);
 assert.equal(wav.toString('ascii',0,4),'RIFF');
 assert.equal(wav.toString('ascii',8,12),'WAVE');
 assert.equal(wav.readUInt16LE(20),1);
 assert.equal(wav.readUInt16LE(22),1);
 assert.equal(wav.readUInt16LE(34),16);
 assert.equal(wav.readUInt32LE(24),24000);
 assert.equal(wav.readUInt32LE(40),signal.length*2);
 assert.ok(gain>0);
 let max=0;
 for(let i=44;i<wav.length;i+=2)max=Math.max(max,Math.abs(wav.readInt16LE(i)));
 assert.ok(max>0&&max<=28508,'0.87 peak cap');
});
test('invalid source, event, time and waveform fail closed',()=>{
 assert.throws(()=>renderPurePhysicalMechanical({seconds:0}),RangeError);
 assert.throws(()=>renderPurePhysicalMechanical({score:[{seconds:.2,type:'on',key:200}]}),RangeError);
 assert.throws(()=>renderPurePhysicalMechanical({seconds:.6,score:[{seconds:.7,type:'pedal',cc:127}]}),RangeError);
 assert.throws(()=>encodeNormalizedMechanicalWav16(new Float64Array(16)),RangeError);
 assert.throws(()=>encodeNormalizedMechanicalWav16(new Float64Array([1,NaN])),TypeError);
});
