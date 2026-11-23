import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {engines,loadState,fromPreset} from '../patches.js';
const read=(p)=>readFileSync(new URL(p, import.meta.url),'utf8');
const controls=engines.piano.groups.flatMap(g=>g.controls);
const choice=controls.find(c=>c.id==='soundEngine');
test('A Claude e B Novo Stage estão dentro do Piano Acústico, sem novo módulo',()=>{
 assert.deepEqual(Object.keys(choice.options),['modal','physicalLegacy','physical','hybrid','classic']);
 assert.match(choice.options.modal,/Claude/);
 assert.match(choice.options.physicalLegacy,/Stage físico anterior/);
 assert.match(choice.options.physical,/Novo Stage mecânico/);
 assert.equal(Object.keys(engines).length,5);
 assert.equal(fromPreset('piano','japanese').values.soundEngine,'physical');
});
test('v1.12.3 mantém seleção salva do motor entre sessões',()=>{
 const saved={patches:{piano:{preset:'japanese',values:{soundEngine:'modal',physicalQuality:'studio'}}}};
 const fake={getItem:(k)=>k==='palco-stage-panel-v1'?JSON.stringify(saved):null};
 const state=loadState(fake);
 assert.equal(state.patches.piano.values.soundEngine,'modal');
 assert.equal(state.patches.piano.values.physicalQuality,'studio');
});
test('UI não cria banners, páginas de atalhos ou outras categorias',()=>{
 const html=read('../index.html');
 assert.doesNotMatch(html,/stage-mechanics-link|acesso-motor-v1\.12\.2|enable-mechanical-piano/);
 assert.match(html,/id="modules"/);
 const app=read('../app.js');
 assert.doesNotMatch(app,/enable-mechanical-piano|state\.patches\.piano\.values\.soundEngine='physical';/);
 assert.match(app,/preparePhysical/);
 assert.match(app,/prepareModal/);
});
test('Novo Stage inclui motor físico e tampo mecânico no AudioWorklet',()=>{
 const engine=read('../physical-piano.js');
 const acoustic=read('../acoustic.js');
 assert.match(engine,/PianoResonanceBody/);
 assert.match(acoustic,/setMechanicalModel/);
 assert.match(acoustic,/physical-piano\.js\?build=1\.12\.7/);
});
