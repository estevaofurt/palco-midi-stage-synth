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
import {renderFastChunk as renderChunk} from './f9-fast-chunk.mjs';
const hp={fft,solidWire,makeDesign,stringMode,spatialWeight,plateDesign,plateModes,patchWeight,ribDesign,generalizedEigen,mindlinModes,PolarizedBridge,PolarizedHammer,BoardCoupledBridge,radiationGrid,surfaceShape,radiationKernel,ResistiveBoard,relaxMemory};

function joinChunks(chunks,hp,rate=48000){
 const lengths=chunks.map(q=>Math.round(q.meta.seconds*rate)),n=lengths.reduce((a,b)=>a+b,0),tail=chunks[0].channels[0].length-lengths[0];
 const y=[new Float64Array(n+tail),new Float64Array(n+tail)];let offset=0;
 for(let k=0;k<chunks.length;k++){const q=chunks[k];if(q.channels.some(c=>c.length!==lengths[k]+tail))throw Error("chunk length");for(let ch=0;ch<2;ch++)for(let i=0;i<q.channels[ch].length;i++)y[ch][offset+i]+=q.channels[ch][i];offset+=lengths[k];}
 let N=1;while(N<y[0].length)N*=2;
 return y.map(x=>{const re=new Float64Array(N),im=new Float64Array(N);re.set(x);hp.fft(re,im);for(let i=0;i<N;i++){const f=Math.min(i,N-i)*rate/N,w=f<=8000?1:f>=12000?0:.5*(1+Math.cos(Math.PI*(f-8000)/4000));re[i]*=w;im[i]*=w;}hp.fft(re,im,true);return re.slice(0,x.length);});
}
const chunks=[];let prior=null;for(let i=0;i<10;i++){const q=renderChunk(hp,{seconds:1,prior});chunks.push({...q,channels:q.channels.map(c=>Float32Array.from(c))});prior=q.checkpoint;console.log(q.meta);}
const y=joinChunks(chunks,hp),w=waveBytes(y,48000,.36767023440034063);if(w.clipped)throw Error('clipping');const dir=process.argv[2]??'f9-output';mkdirSync(dir,{recursive:true});writeFileSync(dir+'/C4_medio_R_10s.wav',w.bytes);
