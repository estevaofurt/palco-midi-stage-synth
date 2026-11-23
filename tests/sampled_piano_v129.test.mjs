import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {engines,loadState,fromPreset} from '../patches.js';
import {SampleLibrary} from '../sample-library.js';
const read=p=>readFileSync(new URL(p,import.meta.url),'utf8');

test('E disponível no seletor do piano sem mudar padrão C e sem novo módulo',()=>{
 const c=engines.piano.groups.flatMap(g=>g.controls).find(x=>x.id==='soundEngine');
 assert.deepEqual(Object.keys(c.options),['modal','physicalLegacy','physical','hybrid','sampled','classic']);
 assert.match(c.options.sampled,/sampleado/);
 assert.equal(engines.piano.groups.flatMap(g=>g.controls).filter(x=>x.type==='samplepack').length,1);
 assert.equal(Object.keys(engines).length,5);
 assert.equal(fromPreset('piano','american').values.soundEngine,'physical');
 const s=loadState({getItem:k=>k==='palco-stage-panel-v1'?JSON.stringify({patches:{piano:{preset:'american',values:{soundEngine:'sampled'}}}}):null});
 assert.equal(s.patches.piano.values.soundEngine,'sampled');
});
test('bancos isolados e notas/velocidades selecionadas sem cruzar pianos',async()=>{
 const ctx={decodeAudioData:async()=>({duration:1})};
 const fake=name=>({name,size:10,arrayBuffer:async()=>new ArrayBuffer(100)});
 const lib=new SampleLibrary(ctx);
 await lib.load('american',[fake('MIDI60_v60.wav'),fake('MIDI60_v110.wav'),fake('MIDI72_v110.wav')]);
 await lib.load('felt',[fake('MIDI60_v70.wav')]);
 assert.equal(lib.count('american'),3);
 assert.equal(lib.count('felt'),1);
 assert.equal(lib.count('japanese'),0);
 assert.equal(lib.choose('american',61,55).velocity,60);
 assert.equal(lib.choose('american',61,115).velocity,110);
 assert.equal(lib.choose('felt',61,115).velocity,70);
 assert.equal(lib.choose('american',96,110),null);
 let rate,played=0;
 ctx.createBufferSource=()=>({playbackRate:{set value(v){rate=v},get value(){return rate}},connect(x){return x}});
 ctx.createGain=()=>({gain:{value:0},connect(x){return x}});
 const part={gate:{},own(){},start(){played++}};
 assert.equal(lib.play('american',part,64,110,.8),true);
 assert.ok(Math.abs(rate-2**(4/12))<1e-10);
 assert.equal(played,1);
 assert.equal(lib.play('japanese',part,64,110),false);
 lib.clear('american');assert.equal(lib.count('american'),0);
});
test('motor E é somente WAV, preservando rotas A/B/C/D e sem amostras no site',()=>{
 const a=read('../acoustic.js'),panel=read('../panel.js'),app=read('../app.js');
 assert.match(a,/if\(p\.soundEngine==='sampled'\)/);
 assert.match(a,/this\.samples\.play\(p\.character,part,key,dynamic,\.85\)/);
 assert.match(a,/\(p\.soundEngine==='classic'\|\|p\.soundEngine==='modal'\)/);
 assert.match(panel,/patch\.values\.soundEngine!=='sampled'/);
 assert.match(app,/E · Piano sampleado/);
 assert.doesNotMatch(read('../index.html'),/\.wav\?build=/);
});
