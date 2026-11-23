import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {engines,loadState} from '../patches.js';
import {PhysicalPianoEngine as LegacyPhysical} from '../physical-piano-legacy.js';
import {PhysicalPianoEngine as MechanicalPhysical} from '../physical-piano.js';
import {PianoEngine as ClaudeModal} from '../piano-worklet.js';
const read=p=>readFileSync(new URL(p,import.meta.url),'utf8');
test('três motores selecionados no mesmo módulo, sem novos links',()=>{
 const c=engines.piano.groups.flatMap(x=>x.controls).find(x=>x.id==='soundEngine');
 assert.deepEqual(Object.keys(c.options),['modal','physicalLegacy','physical','hybrid','classic']);
 assert.match(c.options.modal,/Claude/);
 assert.match(c.options.physicalLegacy,/Stage físico anterior/);
 assert.match(c.options.physical,/Novo Stage mecânico/);
 assert.equal(Object.keys(engines).length,5);
 assert.doesNotMatch(read('../index.html'),/stage-mechanics-link|enable-mechanical-piano/);
});
test('o B usa worklet físico v1.9.5 independente do C',()=>{
 const legacy=read('../physical-piano-legacy.js');
 const current=read('../physical-piano.js');
 const acoustic=read('../acoustic.js');
 assert.match(legacy,/registerProcessor\('palco-physical-piano-legacy'/);
 assert.match(current,/registerProcessor\('palco-physical-piano'/);
 assert.doesNotMatch(legacy,/PianoResonanceBody/);
 assert.match(current,/PianoResonanceBody/);
 assert.match(acoustic,/prepareLegacyPhysical/);
 assert.match(acoustic,/playPhysical\(part,key,velocity,p,expression,true\)/);
 assert.match(acoustic,/physical-piano-legacy\.js\?build=1\.12\.7/);
});
test('B e C produzem saídas diferentes com parâmetros iguais',()=>{
 const older=new LegacyPhysical(48000,'eco');
 const newer=new MechanicalPhysical(48000,'eco');
 newer.setMechanicalModel({enabled:true,amount:.8,sympathy:true});
 for(const engine of [older,newer])engine.noteOn({id:1,key:60,speed:.7,hardness:.5,character:'japanese',brightness:.5,send:.16});
 const a=new Float32Array(128),b=new Float32Array(128),c=new Float32Array(128),d=new Float32Array(128);
 let error=0,energy=0;
 for(let frame=0;frame<170;frame++){
   older.render(a,b,null,128);newer.render(c,d,null,128);
   for(let k=0;k<128;k++){error+=(a[k]-c[k])**2;energy+=a[k]**2;assert.ok(Number.isFinite(c[k]));}
 }
 assert.ok(energy>1e-7);
 assert.ok(error>energy*1e-8,'Mecânico e motor histórico não podem renderizar a mesma saída');
});
test('32 e 64 vozes disponíveis nos dois Stage e motor Claude independente',()=>{
 for(const Engine of [LegacyPhysical,MechanicalPhysical]){
   for(const mode of ['eco','studio']){
     const e=new Engine(48000,mode);
     const count=mode==='eco'?32:64;
     for(let i=0;i<count;i++)e.noteOn({id:i+1,key:36+i,speed:.65,hardness:.5,character:'american'});
     assert.equal(e.voices.filter(v=>v.active).length,count);
     const l=new Float32Array(128),r=new Float32Array(128);e.render(l,r,null,128);
     assert.ok(l.every(Number.isFinite));
   }
 }
 assert.equal(typeof ClaudeModal,'function');
});
test('sessões antigas preservam physical como C e modal como A',()=>{
 for(const engine of ['physical','modal','classic']){
   const saved={patches:{piano:{preset:'japanese',values:{soundEngine:engine}}}};
   const storage={getItem:key=>key==='palco-stage-panel-v1'?JSON.stringify(saved):null};
   assert.equal(loadState(storage).patches.piano.values.soundEngine,engine);
 }
});
