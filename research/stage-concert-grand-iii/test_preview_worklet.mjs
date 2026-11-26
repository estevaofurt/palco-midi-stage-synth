import {test} from 'node:test';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
const root=process.env.G3_PREVIEW_SITE;
if(!root)throw Error('G3_PREVIEW_SITE required');
const {PianoEngine,MAX_VOICES}=await import(pathToFileURL(resolve(root,'piano-worklet.js')));
test('actual preallocated pool, defaults and invalid input',()=>{
  assert.equal(new PianoEngine(48000).voices.length,MAX_VOICES);
  for(const invalid of [null,0,NaN,256,'128'])assert.equal(new PianoEngine(48000,invalid).voices.length,32);
  for(const n of [32,64,88,96,128,192]){
    const a=new PianoEngine(48000,n);
    assert.equal(a.voices.length,n);
    const strike=i=>a.noteOn({id:i,key:36+i%36,speed:.8,hardness:.5});
    for(let i=1;i<=n;i++)strike(i);
    assert.equal(a.voices.filter(v=>v.active).length,n);
    const L=new Float32Array(128),R=new Float32Array(128),S=new Float32Array(128);
    a.render(L,R,S,128);
    assert.ok(L.some(v=>v!==0));assert.ok([...L,...R,...S].every(Number.isFinite));
    strike(n+1);
    assert.ok(a.find(n+1));assert.equal(a.voices.filter(v=>v.active).length,n);
    assert.equal(a.done.length,1);
    const id=a.done[0];assert.equal(a.find(id),null);
  }
});

test('physical preview pools and quality changes',async()=>{
  for(const [file,name] of [['physical-piano.js','PhysicalPianoEngine'],['physical-piano-legacy.js','PhysicalPianoEngine'],['physical-piano-hybrid.js','HybridPianoEngine']]){
    const E=(await import(pathToFileURL(resolve(root,file))))[name];
    assert.equal(new E(48000,'studio').maxVoices,64);
    const a=new E(48000,'studio',128);assert.equal(a.maxVoices,128);
    for(let i=1;i<=128;i++)a.noteOn({id:i,key:36+i%36,speed:.7,hardness:.5});
    assert.equal(a.voices.filter(v=>v.active).length,128);
    a.setQuality('eco');assert.equal(a.maxVoices,32);assert.equal(a.voices.filter(v=>v.active).length,32);
    a.setQuality('balanced');assert.equal(a.maxVoices,128);
    const L=new Float32Array(128),R=new Float32Array(128),S=new Float32Array(128);
    a.render(L,R,S,128);assert.ok(L.every(Number.isFinite)&&R.every(Number.isFinite));
  }
});
