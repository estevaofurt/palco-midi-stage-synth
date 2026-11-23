import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {engines,loadState} from '../patches.js';
const read=p=>readFileSync(new URL(p,import.meta.url),'utf8');
test('E esclarece falta de WAVs e oferece importação na área do teclado',()=>{
 const html=read('../index.html'),app=read('../app.js');
 assert.match(html,/id="sample-notice"/);
 assert.match(html,/id="sample-upload-shortcut"/);
 assert.match(app,/nenhuma nota WAV carregada/);
 assert.match(app,/picker\.click\(\)/);
 assert.match(app,/warnMissingSample\(key,velocity\)/);
 assert.match(app,/lib\.choose\(model,key,velocity\)/);
 assert.match(app,/syncSampleUI\(\)/);
 assert.equal(loadState(null).patches.piano.values.soundEngine,'physical');
 assert.equal(engines.piano.groups.flatMap(g=>g.controls).find(c=>c.id==='soundEngine').options.sampled,'E · Piano sampleado · WAV local');
});
test('Tecla virtual indica pressão mesmo quando Stage não conseguiu criar voz',()=>{
 const app=read('../app.js');
 assert.match(app,/for\(const slot of activePointers\.values\(\)\)held\.add\(slot\.key\)/);
 assert.match(app,/activePointers\.set\(pointer,slot\);paintKeys\(\)/);
 assert.match(app,/activePointers\.delete\(pointer\);performer\.noteOffId\(slot\.id\);paintKeys\(\)/);
 assert.match(app,/keys\.onpointerdown=/);
 assert.match(read('../panel.css'),/\.sample-notice\[hidden\]\{display:none\}/);
});
