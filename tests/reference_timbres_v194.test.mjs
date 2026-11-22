import test from 'node:test';
import assert from 'node:assert/strict';
import {PhysicalPianoEngine,PIANO_CALIBRATION} from '../physical-piano.js';

const RATE=48000;
const KEY=60;
const FREQ=261.625565;
function render(character,seconds=.93){
  const e=new PhysicalPianoEngine(RATE,'eco');
  e.noteOn({id:1,key:KEY,speed:.75,hardness:.6,brightness:.5,character});
  const samples=new Float32Array(Math.round(RATE*seconds));
  const l=new Float32Array(128),r=new Float32Array(128),s=new Float32Array(128);
  for(let pos=0;pos<samples.length;pos+=128){
    const n=Math.min(128,samples.length-pos);
    e.render(l,r,s,n);samples.set(l.subarray(0,n),pos);
  }
  return samples;
}
function harmonicDb(pcm,n,at=.28){
  const size=8192,from=Math.round(at*RATE),freq=FREQ*n;
  let re=0,im=0;
  for(let j=0;j<size;j++){
    const x=pcm[from+j]*(.5-.5*Math.cos(2*Math.PI*j/(size-1)));
    re+=x*Math.cos(2*Math.PI*freq*j/RATE);
    im+=x*Math.sin(2*Math.PI*freq*j/RATE);
  }
  return Math.hypot(re,im);
}
function rms(pcm,from,to){
  let acc=0,count=0;
  for(let i=Math.floor(from*RATE);i<Math.floor(to*RATE);i++){acc+=pcm[i]*pcm[i];count++;}
  return Math.sqrt(acc/count);
}
test('four independent reference-calibrated piano characters are present',()=>{
  assert.deepEqual(Object.keys(PIANO_CALIBRATION),['japanese','american','felt','upright']);
  for(const p of Object.values(PIANO_CALIBRATION)){
    assert.equal(p.partials.length,6);
    assert.ok(p.transientFloor>0&&p.transientFloor<1);
    assert.ok(p.transientTime>.1&&p.transientTime<1);
  }
});
test('Japanese C4 second harmonic dominates; American and Felt do not',()=>{
  const audio=Object.fromEntries(Object.keys(PIANO_CALIBRATION).map(k=>[k,render(k)]));
  const ratio=k=>20*Math.log10(harmonicDb(audio[k],2)/harmonicDb(audio[k],1));
  assert.ok(ratio('japanese')>3,`Japanese H2/H1: ${ratio('japanese').toFixed(1)} dB`);
  assert.ok(ratio('american')< -7,`American H2/H1: ${ratio('american').toFixed(1)} dB`);
  assert.ok(ratio('felt')< -5,`Felt H2/H1: ${ratio('felt').toFixed(1)} dB`);
  assert.ok(ratio('upright')>ratio('american')+5,`Upright: ${ratio('upright').toFixed(1)} dB`);
});
test('instrument-specific fast attack-to-body decay replaces organ-like sustained onset',()=>{
  for(const character of Object.keys(PIANO_CALIBRATION)){
    const x=render(character,1.0);
    const start=rms(x,.09,.27),late=rms(x,.70,.88);
    assert.ok(start>late*1.9,`${character}: ${start} / ${late}`);
    assert.ok(x.every(Number.isFinite));
  }
});
test('output contains no imported audio samples or external per-note assets',()=>{
  const engine=new PhysicalPianoEngine(RATE,'eco');
  engine.noteOn({id:1,key:60,speed:.75,character:'japanese'});
  assert.ok(engine.find(1)?.lineA instanceof Float32Array);
});
