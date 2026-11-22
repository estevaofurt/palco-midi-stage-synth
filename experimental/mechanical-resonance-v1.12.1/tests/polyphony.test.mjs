import test from 'node:test';
import assert from 'node:assert/strict';
import {PianoResonanceBody} from '../piano-resonance.js';
import {CoupledPianoBus} from '../coupled-piano-bus.js';
import {MultiStringProbe} from './fixtures/surrogate-strings.mjs';

for(const count of [32,64]){
  test(`surrogate ${count} physical string loops stay finite in coupled core`,()=>{
    const source=new MultiStringProbe(count);
    const body=new PianoResonanceBody({bridgeLoad:.4,sympathetic:.22,body:.2});
    const bus=new CoupledPianoBus(source,{body,wetMix:.15,feedbackGain:1});
    for(let i=0;i<count;i++)bus.noteOn(24+i,100);
    const l=new Float32Array(128),r=new Float32Array(128);
    let max=0;
    for(let b=0;b<1250;b++){
      bus.render(l,r);
      for(let i=0;i<l.length;i++){
        assert.ok(Number.isFinite(l[i])&&Number.isFinite(r[i]));
        max=Math.max(max,Math.abs(l[i]),Math.abs(r[i]));
      }
    }
    assert.ok(max<1.0,`peak ${max}`);
    assert.equal(source.count,count);
    assert.ok(source.returns>0,'two-way signal must reach test strings');
  });
}
