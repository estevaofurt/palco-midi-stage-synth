/**
 * Offline Stage Synth v1.12.4 A/B/C diagnostics; not a hardware benchmark.
 * Run: node tests/measure_piano_engines.mjs
 *      node tests/measure_piano_engines.mjs --json
 * DRY 48kHz 128-frame processing; no FX, private WAVs or subjective scores.
 */
import {PianoEngine as Modal} from '../piano-worklet.js';
import {PhysicalPianoEngine as Legacy} from '../physical-piano-legacy.js';
import {PhysicalPianoEngine as Mechanical} from '../physical-piano.js';
import {measurePianoNote} from './piano_acoustic_metrics.mjs';

const SR=48000,BLOCK=128,DURATION=1.7;
const MOTORS=[['A_modal',Modal],['B_v195',Legacy],['C_mechanical',Mechanical]];
const CHARACTERS=['japanese','american','felt','upright'];
const KEYS=[36,60,84],VELOCITIES=[32,80,120];

function renderSingle(Engine,motor,key,velocity,character){
 const engine=motor==='A_modal'?new Engine(SR):new Engine(SR,'eco');
 if(motor==='C_mechanical')engine.setMechanicalModel({enabled:true,amount:.65,sympathy:true});
 engine.noteOn({id:1,key,speed:velocity/127,hardness:.5,brightness:.5,character,send:0});
 const frames=Math.ceil(DURATION*SR),data=new Float32Array(frames);
 const l=new Float32Array(BLOCK),r=new Float32Array(BLOCK),s=new Float32Array(BLOCK);
 let maxOfflineBlockMs=0;
 for(let i=0;i<frames;i+=BLOCK){
  const n=Math.min(BLOCK,frames-i),t0=performance.now();
  engine.render(l,r,s,n);
  maxOfflineBlockMs=Math.max(maxOfflineBlockMs,performance.now()-t0);
  for(let j=0;j<n;j++)data[i+j]=(l[j]+r[j])*.5;
 }
 return {motor,character,key,velocity,maxOfflineBlockMs,...measurePianoNote(data,{sampleRate:SR,key})};
}

const measurements=[];
for(const [motor,Engine] of MOTORS)
 for(const character of CHARACTERS)
  for(const key of KEYS)
   for(const velocity of VELOCITIES)
    measurements.push(renderSingle(Engine,motor,key,velocity,character));
const data={baseline:'v1.12.4',sampleRate:SR,monoAverage:true,fx:false,
 notes:KEYS,velocities:VELOCITIES,measurements};
if(process.argv.includes('--json')){
 console.log(JSON.stringify(data,null,2));
}else{
 console.log('Stage Synth A/B/C acoustic baseline: 3 engines × 4 instruments × C2/C4/C6 × v32/80/120');
 console.log('Motor / Character / Key / Velocity | Peak | B-estimate | B-partials | Early/Late dB | RMS');
 for(const m of measurements){
  const B=m.bMedian==null?'n/d':m.bMedian.toExponential(2);
  console.log(m.motor.padEnd(13)+' '+m.character.padEnd(8)+' '+m.key+' v'+String(m.velocity).padEnd(3)+
  ' | '+m.peak.toFixed(3)+' | '+B.padEnd(9)+' | '+m.bSampleCount+
  ' | '+(m.earlyDecayDb?.toFixed(1)??'n/d')+'/'+(m.lateDecayDb?.toFixed(1)??'n/d')+
  ' | '+m.rms.toFixed(4));
 }
 console.log('WARNING: Finite-window B is only an estimate; this is not a piano realism or device performance certification.');
}
if(measurements.some(x=>x.nonFinite||x.clipped))
 console.error('WARNING: detected clipping or non-finite samples in some dry renders. Inspect JSON.');
