import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {HybridPianoEngine as PublicD} from '../physical-piano-hybrid.js';
import {HybridPianoEngine as HistoricD} from '../physical-piano-hybrid-v127.mjs';
import {HybridPianoEngine as TestedCandidate} from '../physical-piano-hybrid-v128-candidate.mjs';
import {engines,loadState} from '../patches.js';

const read=path=>readFileSync(new URL(path,import.meta.url),'utf8');
const render=(Engine,key,velocity=80,quality='studio')=>{
 const e=new Engine(48000,quality);
 e.noteOn({id:7,key,speed:velocity/127,hardness:.55,brightness:.5,
  character:'american',send:0});
 const L=new Float32Array(128),R=new Float32Array(128),out=new Float32Array(2*128*48);
 for(let block=0;block<48;block++){
  e.render(L,R,null,128);
  for(let i=0;i<128;i++){
   out[block*256+i*2]=L[i];out[block*256+i*2+1]=R[i];
  }
 }
 return out;
};
test('motor D preserva PCM do candidato v1.12.8 auditado',()=>{
 for(const key of [21,28,29,33,36,37,48,49,60,72,84,108])
  for(const quality of ['eco','balanced','studio'])
   assert.deepEqual(render(PublicD,key,80,quality),render(TestedCandidate,key,80,quality),
    'candidate/live divergence key='+key+' quality='+quality);
});
test('historical v1.12.7 D is preserved and only F1–C2 differs',()=>{
 for(const key of [21,28,37,48,49,60,72,84,108]){
  assert.deepEqual(render(HistoricD,key),render(PublicD,key),
   'unmodified key changed '+key);
 }
 for(const key of [29,33,36]){
  assert.notDeepEqual(render(HistoricD,key),render(PublicD,key),
   'updated upper bass should differ '+key);
 }
});
test('v1.12.7 historical HTML loads actual 127 acoustics and immutable original worklet',()=>{
 const html=read('../v1.12.7.html');
 const map=JSON.parse(html.match(/<script type="importmap">(.*?)<\/script>/s)[1]).imports;
 assert.equal(map['./acoustic.js'],'./acoustic-v127.mjs?build=1.12.7-archive');
 assert.match(read('../acoustic-v127.mjs'),/physical-piano-hybrid-v127\.mjs\?build=1\.12\.7-archive/);
 assert.match(read('../physical-piano-hybrid-v127.mjs'),/const single=key<37/);
 assert.match(read('../physical-piano-hybrid.js'),/const single=key<29/);
});
test('current D uses original Piano Acoustic selector and historical defaults remain unchanged',()=>{
 const controls=engines.piano.groups.flatMap(x=>x.controls);
 const c=controls.find(x=>x.id==='soundEngine');
 assert.deepEqual(Object.keys(c.options),['modal','physicalLegacy','physical','hybrid','sampled','classic']);
 assert.equal(loadState(null).patches.piano.values.soundEngine,'physical');
 assert.equal(JSON.parse(read('../package.json')).version,'1.12.10');
 const html=read('../index.html');
 assert.match(html,/Stage Synth · Palco MIDI v1\.12\.10/);
 assert.match(read('../acoustic.js'),/physical-piano-hybrid\.js\?build=1\.12\.9/);
});
