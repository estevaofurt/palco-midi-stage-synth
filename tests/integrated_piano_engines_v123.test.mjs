import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {engines,loadState,fromPreset} from '../patches.js';
const read=(p)=>readFileSync(new URL(p,import.meta.url),'utf8');
const modes=engines.piano.groups.flatMap(g=>g.controls).find(c=>c.id==='soundEngine');
test('A Claude e B Novo Stage estão no mesmo Piano Acústico, sem novo módulo',()=>{
 assert.deepEqual(Object.keys(modes.options),['modal','physical','classic']);
 assert.match(modes.options.modal,/Claude/);
 assert.match(modes.options.physical,/Novo Stage/);
 assert.equal(Object.keys(engines).length,5);
 assert.equal(fromPreset('piano','japanese').values.soundEngine,'physical');
});
test('preserva escolha salva do motor',()=>{
 const saved={patches:{piano:{preset:'japanese',values:{soundEngine:'modal',physicalQuality:'studio'}}}};
 const fake={getItem:k=>k==='palco-stage-panel-v1'?JSON.stringify(saved):null};
 const x=loadState(fake);
 assert.equal(x.patches.piano.values.soundEngine,'modal');
 assert.equal(x.patches.piano.values.physicalQuality,'studio');
});
test('app principal não tem banners, novas categorias ou atalhos externos',()=>{
 const h=read('../index.html');
 assert.doesNotMatch(h,/stage-mechanics-link|acesso-motor-v1\.12\.2|enable-mechanical-piano/);
 const a=read('../app.js');
 assert.doesNotMatch(a,/enable-mechanical-piano|state\.patches\.piano\.values\.soundEngine='physical';/);
 assert.match(a,/preparePhysical/);
 assert.match(a,/prepareModal/);
});
test('motor B inclui acoplamento mecânico integrado e versão correta',()=>{
 const p=read('../physical-piano.js');
 const a=read('../acoustic.js');
 assert.match(p,/PianoResonanceBody/);
 assert.match(a,/setMechanicalModel/);
 assert.match(a,/physical-piano\.js\?build=1\.12\.3/);
});
