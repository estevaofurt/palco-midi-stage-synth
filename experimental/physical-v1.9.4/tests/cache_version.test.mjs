import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync, readdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
const dir=resolve(dirname(fileURLToPath(import.meta.url)),'..');
for(const [file,version] of [['index.html','1.9.4'],['v1.9.4.html','1.9.4'],['v1.9.3.html','1.9.3'],['v1.9.2.html','1.9.2'],['v1.9.1.html','1.9.1']]) {
  test(`${file} identifica e carrega v${version}`,()=>{
    const html=readFileSync(resolve(dir,file),'utf8');
    assert.ok(html.includes(`Stage Synth · Palco MIDI v${version}`));
    assert.ok(html.includes(`app.js?build=${version}`));
    assert.ok(html.includes(`panel.css?build=${version}`));
    assert.match(html, /class="build-tag"/);
    const map=JSON.parse(html.match(/<script type="importmap">(.*?)<\/script>/s)[1]);
    for(const path of readdirSync(dir).filter(x=>x.endsWith('.js')&&x!=='app.js')) {
      assert.equal(map.imports[`./${path}`],`./${path}?build=${version}`);
    }
  });
}
