import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync, readdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
const dir=resolve(dirname(fileURLToPath(import.meta.url)),'..');
for(const [file,version] of [['index.html','1.12.8'],['v1.12.7.html','1.12.7'],['v1.12.6.html','1.12.6'],['v1.12.5.html','1.12.5'],['v1.12.4.html','1.12.4'],['v1.8.4.html','1.8.4'],['v1.8.3.html','1.8.3'],['v1.8.2.html','1.8.2']]) {
  test(`${file} identifica e carrega v${version}`,()=>{
    const html=readFileSync(resolve(dir,file),'utf8');
    assert.ok(html.includes(`Stage Synth · Palco MIDI v${version}`));
    assert.ok(html.includes(`app.js?build=${version}`));
    assert.ok(html.includes(`panel.css?build=${version}`));
    assert.match(html, /class="build-tag"/);
    const map=JSON.parse(html.match(/<script type="importmap">(.*?)<\/script>/s)[1]);
    for(const [path,url] of Object.entries(map.imports)){
      assert.equal(url,file==='v1.12.6.html'&&path==='./acoustic.js'
        ?'./acoustic-v126.js?build=1.12.6-archive':
        file==='v1.12.7.html'&&path==='./acoustic.js'
        ?'./acoustic-v127.mjs?build=1.12.7-archive':`${path}?build=${version}`);
    }
    if(file==='index.html'||file==='v1.12.7.html'){
      for(const path of readdirSync(dir).filter(x=>x.endsWith('.js')&&x!=='app.js')){
        const expected=file==='v1.12.7.html'&&path==='acoustic.js'
          ?'./acoustic-v127.mjs?build=1.12.7-archive':`./${path}?build=${version}`;
        assert.equal(map.imports[`./${path}`],expected);
      }
    }
  });
}
