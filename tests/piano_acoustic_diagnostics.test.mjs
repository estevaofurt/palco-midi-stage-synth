import test from 'node:test';
import assert from 'node:assert/strict';
import {PianoEngine as Modal} from '../piano-worklet.js';
import {PhysicalPianoEngine as Legacy} from '../physical-piano-legacy.js';
import {PhysicalPianoEngine as Mechanical} from '../physical-piano.js';
import {measurePianoNote} from './piano_acoustic_metrics.mjs';

test('A/B/C each yield measurable C4 without changing the DSP',()=>{
 for(const [kind,Engine] of [['modal',Modal],['legacy',Legacy],['mechanical',Mechanical]]){
  const engine=kind==='modal'?new Engine(48000):new Engine(48000,'eco');
  if(kind==='mechanical')engine.setMechanicalModel({enabled:true,amount:.65,sympathy:true});
  engine.noteOn({id:1,key:60,speed:80/127,hardness:.5,character:'japanese',brightness:.5,send:0});
  const samples=new Float32Array(48000*1.7);
  const l=new Float32Array(128),r=new Float32Array(128),s=new Float32Array(128);
  for(let i=0;i<samples.length;i+=128){
   const n=Math.min(128,samples.length-i);
   engine.render(l,r,s,n);
   for(let j=0;j<n;j++)samples[i+j]=(l[j]+r[j])*.5;
  }
  const m=measurePianoNote(samples,{sampleRate:48000,key:60});
  assert.ok(m.rms>0,kind+' must produce a signal');
  assert.equal(m.nonFinite,0,kind+' must yield finite samples');
  assert.ok(m.peak<2,kind+' unbounded peak='+m.peak);
  assert.ok(m.harmonics.length>=4,kind+' must yield harmonics');
 }
});
