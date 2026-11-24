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
import {renderRegisterPilot as renderChunk} from './f10-register-pilot.mjs';
import {pilotWire,PILOT_NOTES} from './f10-pilot-geometry.mjs';
const hp={fft,solidWire,makeDesign,stringMode,spatialWeight,plateDesign,plateModes,patchWeight,ribDesign,generalizedEigen,mindlinModes,PolarizedBridge,PolarizedHammer,BoardCoupledBridge,radiationGrid,surfaceShape,radiationKernel,ResistiveBoard,relaxMemory};

function joinChunks(chunks,hp,rate=48000){
 const lengths=chunks.map(q=>Math.round(q.meta.seconds*rate)),n=lengths.reduce((a,b)=>a+b,0),tail=chunks[0].channels[0].length-lengths[0];
 const y=[new Float64Array(n+tail),new Float64Array(n+tail)];let offset=0;
 for(let k=0;k<chunks.length;k++){const q=chunks[k];if(q.channels.some(c=>c.length!==lengths[k]+tail))throw Error("chunk length");for(let ch=0;ch<2;ch++)for(let i=0;i<q.channels[ch].length;i++)y[ch][offset+i]+=q.channels[ch][i];offset+=lengths[k];}
 let N=1;while(N<y[0].length)N*=2;
 return y.map(x=>{const re=new Float64Array(N),im=new Float64Array(N);re.set(x);hp.fft(re,im);for(let i=0;i<N;i++){const f=Math.min(i,N-i)*rate/N,w=f<=8000?1:f>=12000?0:.5*(1+Math.cos(Math.PI*(f-8000)/4000));re[i]*=w;im[i]*=w;}hp.fft(re,im,true);return re.slice(0,x.length);});
}

const [dir='f10-pilot-output',midiArg='60',durationArg='3']=process.argv.slice(2);
const midi=Number(midiArg),duration=Number(durationArg),velocity=1;
if(!PILOT_NOTES.includes(midi)||duration!==3)throw RangeError('pilot note and three-second render');
const wire=pilotWire(hp,midi),chunks=[];let prior=null;
for(let i=0;i<duration;i++){const q=renderChunk(hp,{seconds:1,velocity,midi,prior});chunks.push({...q,channels:q.channels.map(c=>Float32Array.from(c))});prior=q.checkpoint;console.log(JSON.stringify(q.meta));}
const y=joinChunks(chunks,hp),w=waveBytes(y,48000,.36767023440034063);if(w.clipped)throw Error('clipping');
mkdirSync(dir,{recursive:true});const stem='MIDI'+midi+'_v1_felt1.5_3s';
writeFileSync(dir+'/'+stem+'.wav',w.bytes,{flag:'wx'});
writeFileSync(dir+'/'+stem+'.json',JSON.stringify({duration,velocity,midi,wire,feltFactor:1.5,gain:.36767023440034063,peak:w.peak,clipped:w.clipped,chunks:chunks.map(q=>q.meta)},null,2),{flag:'wx'});

const pcm=decodePcmChannels(w.bytes,parsePcm16),audit=compareQuantization(y,pcm.channels,48000);
const prePcm=analyzeSustain(y.map(c=>Float64Array.from(c,v=>v*.36767023440034063)),48000,fft,{excludeEndS:.04,f1:wire.f1Hz,B:wire.B});
writeFileSync(dir+'/'+stem+'_precision.json',JSON.stringify(audit,null,2),{flag:'wx'});
writeFileSync(dir+'/'+stem+'_float_analysis.json',JSON.stringify(prePcm,null,2),{flag:'wx'});
console.log('F10_PILOT_WINDOWS '+JSON.stringify(prePcm.windows));

const hi=wave24(y,48000,.36767023440034063);if(hi.clipped||hi.peak!==w.peak)throw Error('24-bit export mismatch');
writeFileSync(dir+'/'+stem+'_24bit.wav',hi.bytes,{flag:'wx'});
console.log('F10_PILOT_EXPORT '+JSON.stringify({frames:y[0].length,peak:hi.peak,clipped:hi.clipped,pcm16Bytes:w.bytes.length,pcm24Bytes:hi.bytes.length}));
