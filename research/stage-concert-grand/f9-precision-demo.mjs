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
import {compareQuantization,decodePcmChannels} from './f9-precision-audit.mjs';
import {parsePcm16} from './f9-decay-analysis.mjs';
import {analyzeSustain} from './f9-long-analysis.mjs';
import {renderStringLoss as renderChunk} from './f9-string-loss.mjs';
const hp={fft,solidWire,makeDesign,stringMode,spatialWeight,plateDesign,plateModes,patchWeight,ribDesign,generalizedEigen,mindlinModes,PolarizedBridge,PolarizedHammer,BoardCoupledBridge,radiationGrid,surfaceShape,radiationKernel,ResistiveBoard,relaxMemory};

function joinChunks(chunks,hp,rate=48000){
 const lengths=chunks.map(q=>Math.round(q.meta.seconds*rate)),n=lengths.reduce((a,b)=>a+b,0),tail=chunks[0].channels[0].length-lengths[0];
 const y=[new Float64Array(n+tail),new Float64Array(n+tail)];let offset=0;
 for(let k=0;k<chunks.length;k++){const q=chunks[k];if(q.channels.some(c=>c.length!==lengths[k]+tail))throw Error("chunk length");for(let ch=0;ch<2;ch++)for(let i=0;i<q.channels[ch].length;i++)y[ch][offset+i]+=q.channels[ch][i];offset+=lengths[k];}
 let N=1;while(N<y[0].length)N*=2;
 return y.map(x=>{const re=new Float64Array(N),im=new Float64Array(N);re.set(x);hp.fft(re,im);for(let i=0;i<N;i++){const f=Math.min(i,N-i)*rate/N,w=f<=8000?1:f>=12000?0:.5*(1+Math.cos(Math.PI*(f-8000)/4000));re[i]*=w;im[i]*=w;}hp.fft(re,im,true);return re.slice(0,x.length);});
}

const [dir='f9-precision-output',durationArg='20',velocityArg='1',factorArg='.5',angleArg='.5',spreadArg='.5',lossCase='control']=process.argv.slice(2);
const duration=Number(durationArg),velocity=Number(velocityArg),boardFactor=Number(factorArg),angleRad=Number(angleArg),spreadCents=Number(spreadArg);
if(!Number.isInteger(duration)||duration<1||duration>40||![.5,1,2.5].includes(velocity)||![.5,1].includes(boardFactor)||![.25,.5].includes(angleRad)||![.25,.5,1].includes(spreadCents)||!['control','horizontal-half','both-half'].includes(lossCase))throw RangeError('duration 1–40 s, velocity .5/1/2.5, board factor .5/1, angle .25/.5, spread .25/.5/1, loss case control/horizontal-half/both-half');
const chunks=[];let prior=null;
for(let i=0;i<duration;i++){const q=renderChunk(hp,{seconds:1,velocity,boardFactor,angleRad,spreadCents,lossCase,prior});chunks.push({...q,channels:q.channels.map(c=>Float32Array.from(c))});prior=q.checkpoint;console.log(JSON.stringify(q.meta));}
const y=joinChunks(chunks,hp),w=waveBytes(y,48000,.36767023440034063);if(w.clipped)throw Error('clipping');
mkdirSync(dir,{recursive:true});const stem='C4_v'+velocity+'_board'+boardFactor+'_angle'+angleRad+'_spread'+spreadCents+'_'+lossCase+'_'+duration+'s';
writeFileSync(dir+'/'+stem+'.wav',w.bytes,{flag:'wx'});
writeFileSync(dir+'/'+stem+'.json',JSON.stringify({duration,velocity,boardFactor,angleRad,spreadCents,lossCase,gain:.36767023440034063,peak:w.peak,clipped:w.clipped,chunks:chunks.map(q=>q.meta)},null,2),{flag:'wx'});

const pcm=decodePcmChannels(w.bytes,parsePcm16),audit=compareQuantization(y,pcm.channels,48000);
const prePcm=analyzeSustain(y.map(c=>Float64Array.from(c,v=>v*.36767023440034063)),48000,fft,{excludeEndS:.04});
writeFileSync(dir+'/'+stem+'_precision.json',JSON.stringify(audit,null,2),{flag:'wx'});
writeFileSync(dir+'/'+stem+'_float_analysis.json',JSON.stringify(prePcm,null,2),{flag:'wx'});
console.log('F9_PRECISION '+JSON.stringify(audit.windows.filter(x=>[0,10,14,19,24,29,34,39].includes(x.startS))));
