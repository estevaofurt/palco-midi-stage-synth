import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read=(p)=>readFileSync(new URL(p, import.meta.url),'utf8');
test('HTML principal carrega arquivos da mesma versão',()=>{
 const html=read('../index.html');
 const imports=JSON.parse(html.match(/<script type="importmap">(.*?)<\/script>/s)[1]).imports;
 for(const path of ['./acoustic.js','./physical-piano.js','./piano-resonance.js','./patches.js'])
  assert.equal(imports[path],path+'?build=1.12.6');
 assert.match(html,/app\.js\?build=1\.12\.5/);
});
