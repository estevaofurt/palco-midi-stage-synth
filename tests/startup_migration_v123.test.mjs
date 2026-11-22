import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
test('HTML carrega os módulos da mesma versão',()=>{
 const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
 const match=html.match(/<script type="importmap">(.*?)<\/script>/s);
 const map=JSON.parse(match[1]).imports;
 for(const path of ['./acoustic.js','./physical-piano.js','./piano-resonance.js','./patches.js'])
  assert.equal(map[path],path+'?build=1.12.3');
 assert.match(html,/app\.js\?build=1\.12\.3/);
});
