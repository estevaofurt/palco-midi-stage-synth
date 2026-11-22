import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync, readdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
const dir=resolve(dirname(fileURLToPath(import.meta.url)),'..');
for(const file of ['index.html','v1.8.2.html']) {
  test(`${file} identifica e carrega v1.8.2`,()=>{
    const html=readFileSync(resolve(dir,file),'utf8');
    assert.match(html, /Stage Synth \u00b7 Palco MIDI v1\.8\.2/);
    assert.match(html, /app\.js\?build=1\.8\.2/);
    assert.match(html, /panel\.css\?build=1\.8\.2/);
    assert.match(html, /class="build-tag"/);
    const map=JSON.parse(html.match(/<script type="importmap">(.*?)<\/script>/s)[1]);
    for(const path of readdirSync(dir).filter(x=>x.endsWith('.js')&&x!=='app.js')) {
      assert.equal(map.imports[`./${path}`],`./${path}?build=1.8.2`);
    }
  });
}
