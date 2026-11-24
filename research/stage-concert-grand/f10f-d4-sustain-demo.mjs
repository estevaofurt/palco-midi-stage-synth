import {writeFileSync,mkdirSync} from 'node:fs';
import {solidWire} from '../c3x-physical/c4-wire-consistency.mjs';
import {makeDesign} from './c4-design.mjs';
import {stringMode,spatialWeight} from './stiff-string.mjs';
import {plateDesign,plateModes,patchWeight} from './orthotropic-plate.mjs';
import {ribDesign,generalizedEigen} from './ribbed-plate.mjs';
import {mindlinModes} from './mindlin-plate.mjs';
import {PolarizedBridge,PolarizedHammer} from './polarized-bridge.mjs';
import {BoardCoupledBridge} from './board-coupling.mjs';
import {radiationGrid,surfaceShape,radiationKernel} from './surface-radiation.mjs';
import {ResistiveBoard} from './radiation-loading.mjs';
import {relaxMemory} from './felt-memory.mjs';
import {fft,waveBytes} from './f8-render.mjs';
import {wave24} from './f9-wave24.mjs';
import {compareQuantization,decodePcmChannels} from './f9-precision-audit.mjs';
import {parsePcm16} from './f9-decay-analysis.mjs';
import {analyzeSustain} from './f9-long-analysis.mjs';
import {renderD4Sustain as renderChunk} from './f10f-d4-sustain.mjs';
import {MODEL_D} from './f10-model-d-register.mjs';
import {pilotWire} from './f10-pilot-geometry.mjs';
import {inspectPair} from './f9-soft-pcm-audit.mjs';
import {contextualCrossing} from './f9-acceptance-analysis.mjs';
import {inspectRattleWindow} from './f9-rattle-spectrum.mjs';
import {hammerSpeed} from './f9-midi-velocity.mjs';
const hp={fft,solidWire,makeDesign,stringMode,spatialWeight,plateDesign,plateModes,patchWeight,ribDesign,generalizedEigen,mindlinModes,PolarizedBridge,PolarizedHammer,BoardCoupledBridge,radiationGrid,surfaceShape,radiationKernel,ResistiveBoard,relaxMemory};

function joinChunks(chunks,hp,rate=48000){
 const lengths=chunks.map(q=>Math.round(q.meta.seconds*rate)),n=lengths.reduce((a,b)=>a+b,0),tail=chunks[0].channels[0].length-lengths[0];
 const y=[new Float64Array(n+tail),new Float64Array(n+tail)];let offset=0;
 for(let k=0;k<chunks.length;k++){const q=chunks[k];if(q.channels.some(c=>c.length!==lengths[k]+tail))throw Error("chunk length");for(let ch=0;ch<2;ch++)for(let i=0;i<q.channels[ch].length;i++)y[ch][offset+i]+=q.channels[ch][i];offset+=lengths[k];}
 let N=1;while(N<y[0].length)N*=2;
 return y.map(x=>{const re=new Float64Array(N),im=new Float64Array(N);re.set(x);hp.fft(re,im);for(let i=0;i<N;i++){const f=Math.min(i,N-i)*rate/N,w=f<=8000?1:f>=12000?0:.5*(1+Math.cos(Math.PI*(f-8000)/4000));re[i]*=w;im[i]*=w;}hp.fft(re,im,true);return re.slice(0,x.length);});
}

const [dir='f10f-sustain',noteArg='60',touchArg='76']=process.argv.slice(2);
const caseArg='D4-loss50';
const midi=Number(noteArg),midiVelocity=Number(touchArg),duration=midiVelocity===127?40:20,velocity=hammerSpeed(midiVelocity);
if(![60,67].includes(midi)||![24,76,127].includes(midiVelocity))throw RangeError('long case');
const wire=pilotWire(hp,midi);
const chunks=[];let prior=null;
for(let i=0;i<duration;i++){const q=renderChunk(hp,{seconds:1,midiVelocity,midi,prior,factor:.5});chunks.push({...q,channels:q.channels.map(c=>Float32Array.from(c))});prior=q.checkpoint;console.log(JSON.stringify(q.meta));}
const y=joinChunks(chunks,hp),w=waveBytes(y,48000,MODEL_D.gain);if(w.clipped)throw Error('clipping');
mkdirSync(dir,{recursive:true});const stem=caseArg+'_MIDI'+midi+'_touch'+midiVelocity+'_'+duration+'s';
writeFileSync(dir+'/'+stem+'.wav',w.bytes,{flag:'wx'});
writeFileSync(dir+'/'+stem+'.json',JSON.stringify({duration,midiVelocity,velocity,midi,wire,case:caseArg,feltFactor:1.5,gain:MODEL_D.gain,peak:w.peak,clipped:w.clipped,chunks:chunks.map(q=>q.meta)},null,2),{flag:'wx'});

const pcm=decodePcmChannels(w.bytes,parsePcm16),audit=compareQuantization(y,pcm.channels,48000);
const prePcm=analyzeSustain(y.map(c=>Float64Array.from(c,v=>v*MODEL_D.gain)),48000,fft,{excludeEndS:.04,f1:wire.f1Hz,B:wire.B});
writeFileSync(dir+'/'+stem+'_precision.json',JSON.stringify(audit,null,2),{flag:'wx'});
writeFileSync(dir+'/'+stem+'_float_analysis.json',JSON.stringify(prePcm,null,2),{flag:'wx'});
console.log('F9_PRECISION '+JSON.stringify(audit.windows.filter(x=>[0,10,14,19,24,29,34,39].includes(x.startS))));

const hi=wave24(y,48000,MODEL_D.gain);if(hi.clipped||hi.peak!==w.peak)throw Error('24-bit export mismatch');
writeFileSync(dir+'/'+stem+'_24bit.wav',hi.bytes,{flag:'wx'});
console.log('F10F_EXPORT '+JSON.stringify({frames:y[0].length,peak:hi.peak,clipped:hi.clipped,pcm16Bytes:w.bytes.length,pcm24Bytes:hi.bytes.length}));

const pressure=y.map(c=>Float64Array.from(c,v=>v*MODEL_D.gain));
const windows=[[.025,.525],[.525,1.025],[1.025,1.525],[2.025,2.525]].map(([startS,endS])=>inspectRattleWindow(pressure,48000,fft,{startS,endS,f1:wire.f1Hz,B:wire.B}));
const pair=inspectPair(w.bytes,hi.bytes);
if(pair.frames!==y[0].length||Math.abs(pair.rms24-prePcm.windows[0].rms)>.5/8388607+1e-12||chunks.some(q=>q.meta.maxBalance>1e-9||q.meta.maxIncrease>1e-9))throw Error('long render gate');
const threshold=.0006518758466381057;
const result={case:caseArg,midiVelocity,duration,velocity,midi,wire,gain:MODEL_D.gain,windows,rms:prePcm.windows.map(w=>({startS:w.startS,rms:w.rms,partials:w.partials})),relativeDrops:prePcm.broadband.drops,contextualCrossing:contextualCrossing(prePcm.windows,threshold),threshold,actualStringLoss:chunks[0].meta.actualStringLoss,maxBalance:Math.max(...chunks.map(q=>q.meta.maxBalance)),maxIncrease:Math.max(...chunks.map(q=>q.meta.maxIncrease)),peak:hi.peak,clipped:hi.clipped,pair,attack:chunks[0].meta.attack};
writeFileSync(dir+'/'+stem+'_rattle.json',JSON.stringify(result,null,2),{flag:'wx'});
console.log('F10F_LONG '+JSON.stringify({...result,rms:result.rms.filter(w=>[0,.5,1,2,4,9,10,14,19,24,29,34,39].includes(w.startS))}));
