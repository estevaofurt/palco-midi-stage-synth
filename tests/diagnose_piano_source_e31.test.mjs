import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {harmonicLevelsDb,diagnoseBridgeVsPanel}
 from '../research/diagnose-piano-source-e31.mjs';

test('harmonic analyzer recovers deterministic ratio of synthetic sine partials',()=>{
 const sr=24000,n=12000,signal=new Float64Array(n);
 for(let i=0;i<n;i++){
  const t=i/sr;
  signal[i]=Math.sin(2*Math.PI*200*t)+.5*Math.sin(2*Math.PI*400*t)+
   .25*Math.sin(2*Math.PI*600*t);
 }
 const db=harmonicLevelsDb(signal,sr,200,{count:3});
 assert.ok(Math.abs(db[0])<.001);
 assert.ok(Math.abs(db[1]+6.0206)<.4,'second partial '+db[1]);
 assert.ok(Math.abs(db[2]+12.0412)<.4,'third partial '+db[2]);
});

test('E3.0 radiated large bridge instead of weak panel and lacks upper harmonics',()=>{
 const result=diagnoseBridgeVsPanel({sampleRate:24000,seconds:.36,key:48});
 assert.equal(result.connectedKeys,88);
 assert.equal(result.stringCoordinates,592);
 assert.ok(result.panelToBridgeRmsRatio>.001);
 assert.ok(result.panelToBridgeRmsRatio<.15,
  'panel carries much less velocity than localized bridge');
 assert.equal(result.originalHigherPartialsMissing,true,
  'E3.0 has no convincing fifth harmonic at C3');
 assert.equal(result.surfaceOnlyHigherPartialsMissing,true,
  'fixing source label alone does not produce piano timbre');
 assert.equal(result.truePianoTimbreVerified,false);
 assert.equal(result.proposedPromotion,false);
});

test('source-coherent radiation remains deterministic, does not change passive mechanical state',()=>{
 const options={sampleRate:24000,seconds:.36,key:48};
 const a=diagnoseBridgeVsPanel(options),b=diagnoseBridgeVsPanel(options);
 assert.deepEqual(a,b);
 assert.ok(Math.abs(a.mechanicalRelativeEnergyBalance)<1e-7);
});

test('fail closed on bad audio, piano key and empty fundamental',()=>{
 assert.throws(()=>harmonicLevelsDb(new Float64Array(12000),24000,200),RangeError);
 assert.throws(()=>harmonicLevelsDb(new Float64Array([1,2,3]),24000,200),RangeError);
 assert.throws(()=>diagnoseBridgeVsPanel({key:190}),RangeError);
 assert.throws(()=>diagnoseBridgeVsPanel({seconds:.1}),RangeError);
});

test('diagnostics cannot import prerecorded piano content or a sampler',()=>{
 const src=readFileSync(new URL('../research/diagnose-piano-source-e31.mjs',import.meta.url),'utf8');
 assert.doesNotMatch(src,/^import .*(sample-library|piano-bank|sf2-reader|\.wav)/gm);
});
