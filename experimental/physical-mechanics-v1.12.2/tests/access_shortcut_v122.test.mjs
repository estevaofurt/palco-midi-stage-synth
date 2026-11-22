import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read=(p)=>readFileSync(new URL(p,import.meta.url),'utf8');
test('Acesso mecânico tem página própria sem cache antigo',()=>{
 const html=read('../acesso-motor-v1.12.2.html');
 assert.match(html,/id="enable-mechanical-piano"/);
 assert.match(html,/id="mechanical-access-state"/);
 assert.match(html,/app\.js\?build=1\.12\.2-access1/);
 assert.match(html,/\.\/piano-resonance\.js\?build=1\.12\.2/);
});
test('Botão seleciona motor físico e acoplamento ao abrir editor',()=>{
 const app=read('../app.js');
 assert.match(app,/enable-mechanical-piano.*addEventListener\('click'/);
 assert.match(app,/piano\.soundEngine='physical'/);
 assert.match(app,/piano\.mechanicalModel='on'/);
 assert.match(app,/await startAudio\(\)/);
 assert.match(app,/engine\.setMechanicalModel\(piano\)/);
});
