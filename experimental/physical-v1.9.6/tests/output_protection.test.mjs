import test from 'node:test';
import assert from 'node:assert/strict';
import {softClipCurve,HEADROOM,CEILING} from '../antclip.js';
import {MAX_VOICES,PianoEngine} from '../piano-worklet.js';
test('limitador: saída limitada, contínua, simétrica e sem reforço ao zero',()=>{
  const a=softClipCurve();
  assert.equal(a.length,4097);
  assert.ok(HEADROOM<.8&&HEADROOM>.5);
  assert.ok(CEILING<1);
  assert.equal(a[(a.length-1)/2],0);
  for(let i=1;i<a.length;i++)assert.ok(a[i]>=a[i-1]);
  for(let i=0;i<a.length;i++){
    assert.ok(Math.abs(a[i])<=CEILING+1e-7);
    assert.ok(Math.abs(a[i]+a[a.length-1-i])<2e-7);
  }
  // Para sinais baixos o transfer é quase linear.
  assert.ok(Math.abs(a[2253]-.1)<.01);
});
test('motor modal: limites de processamento compatíveis com 32 notas',()=>{
  assert.equal(MAX_VOICES,32);
  const m=new PianoEngine(48000);
  assert.ok(m.maxPartials<=28);
});
