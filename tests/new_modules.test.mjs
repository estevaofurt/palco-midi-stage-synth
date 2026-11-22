import test from 'node:test';
import assert from 'node:assert/strict';
import {engines,effectsDefinition,fromPreset,loadState} from '../patches.js';
import {Performance,chordIntervals,stepDuration} from '../performance.js';
import {SF2Reader} from '../sf2-reader.js';

const fixture=()=>{
 const le16=n=>{const b=Buffer.alloc(2);b.writeUInt16LE(n&65535);return b};
 const le32=n=>{const b=Buffer.alloc(4);b.writeUInt32LE(n>>>0);return b};
 const name=(s,n)=>{const b=Buffer.alloc(n);b.write(s);return b};
 const chunk=(id,b)=>Buffer.concat([name(id,4),le32(b.length),b,b.length%2?Buffer.alloc(1):Buffer.alloc(0)]);
 const list=(id,children)=>chunk('LIST',Buffer.concat([name(id,4),...children]));
 const gen=(op,val)=>Buffer.concat([le16(op),le16(val)]);
 const phdr=(s,p,b,bag)=>Buffer.concat([name(s,20),le16(p),le16(b),le16(bag),Buffer.alloc(12)]);
 const inst=(s,bag)=>Buffer.concat([name(s,20),le16(bag)]);
 const shdr=(s,start,end,ls,le,pitch=60)=>Buffer.concat([name(s,20),le32(start),le32(end),le32(ls),le32(le),le32(22050),Buffer.from([pitch,0]),le16(0),le16(1)]);
 const count=2048;const audio=Buffer.alloc(count*2);
 for(let i=0;i<count;i++)audio.writeInt16LE(Math.round(10000*Math.sin(i*2*Math.PI*220/22050)),i*2);
 const hydra=[
   chunk('phdr',Buffer.concat([phdr('Fixture Preset',0,0,0),phdr('EOP',0,0,1)])),
   chunk('pbag',Buffer.concat([gen(0,0),gen(1,0)])),
   chunk('pmod',Buffer.alloc(10)),chunk('pgen',gen(41,0)),
   chunk('inst',Buffer.concat([inst('Sine Fixture',0),inst('EOI',1)])),
   chunk('ibag',Buffer.concat([gen(0,0),gen(1,0)])),
   chunk('imod',Buffer.alloc(10)),chunk('igen',gen(53,0)),
   chunk('shdr',Buffer.concat([shdr('SINE',0,count,100,count-100),shdr('EOS',0,0,0,0)]))
 ];
 const body=Buffer.concat([name('sfbk',4),list('INFO',[chunk('ifil',Buffer.from([2,0,1,0]))]),list('sdta',[chunk('smpl',audio)]),list('pdta',hydra)]);
 const result=Buffer.concat([name('RIFF',4),le32(body.length),body]);
 return result.buffer.slice(result.byteOffset,result.byteOffset+result.byteLength);
};
test('catálogo contém timbres e oito sessões de efeitos',()=>{
 assert.equal(Object.keys(engines).length,5);assert.equal(effectsDefinition.length,8);
 assert.deepEqual(engines.piano.presets.map(x=>x.id),['japanese','american','felt','upright']);
 assert.equal(engines.electric.presets.length,9);
 assert.deepEqual(engines.organ.presets.map(x=>x.id),['jazz','gospel','church']);
 const state=loadState({getItem:()=>null});assert.equal(Object.keys(state.fx.slots).length,8);
 for(const id of Object.keys(engines))assert.equal(state.fx.enabled[id],false);
});
test('presets de instrumentos são independentes',()=>{
 assert.notDeepEqual(fromPreset('piano','felt').values,fromPreset('piano','japanese').values);
 assert.equal(fromPreset('electric','wurly200').values.model,'wurly200');
 assert.equal(fromPreset('synth','bass').values.voiceMode,'mono');
});
test('gerador de acordes e divisão de tempo',()=>{
 assert.deepEqual(chordIntervals('minor'),[0,3,7]);
 assert.deepEqual(chordIntervals('major'),[0,4,7]);
 assert.equal(stepDuration(120,'1/8'),250);
 assert.equal(stepDuration(120,'1/16'),125);
});
test('performance distribui múltiplas notas e libera todas',()=>{
 let seq=0;const active=new Map();
 const st={startNote(source,ch,key,vel){const id=++seq;active.set(id,{source,ch,key,vel});return id},releaseId(id){active.delete(id)},message(){}};
 const p=new Performance(()=>st,{chord:'major',arp:false,bpm:120,rate:'1/8',loopBars:'1'});
 const id=p.noteOn('midi1',0,60,90);
 assert.deepEqual([...active.values()].map(v=>v.key),[60,64,67]);
 p.noteOffId(id);assert.equal(active.size,0);
 p.message('midi1',[0x90,67,100]);assert.equal(active.size,3);
 p.message('midi1',[0x80,67,0]);assert.equal(active.size,0);
 p.panic();
});
test('leitor SF2 interpreta uma amostra PCM de teste',()=>{
 const bank=new SF2Reader(fixture());
 assert.equal(bank.programs.length,1);
 assert.equal(bank.getZones(0,60,100).length,1);
 assert.equal(bank.getZones(0,60,100)[0].sampleIndex,0);
 assert.equal(bank.getZones(0,60,100)[0].sample.rate,22050);
 assert.deepEqual(bank.getZones(0,50,100).length,1);
 assert.throws(()=>new SF2Reader(new ArrayBuffer(8)),/SF2/);
});
export const sf2Fixture=fixture;
