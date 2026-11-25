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
const hp={fft,solidWire,makeDesign,stringMode,spatialWeight,plateDesign,plateModes,patchWeight,ribDesign,generalizedEigen,mindlinModes,PolarizedBridge,PolarizedHammer,BoardCoupledBridge,radiationGrid,surfaceShape,radiationKernel,ResistiveBoard,relaxMemory};

import {renderImpactTrial} from './f11u-r7-impact-render.mjs';
import {phraseNotes,phrase} from './f11u-phrase-program.mjs';
import {chordProgram,validateChordProgram} from './f11p-chord-program.mjs';
import {S50_REFERENCE} from './f11a-s50-scale.mjs';
import {wave24} from './f9-wave24.mjs';
import {inspectPair} from './f9-soft-pcm-audit.mjs';
import {writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
const [out='r7',mode='pedal',speedArg='1',feltArg='1.5',velocityArg='76']=process.argv.slice(2);
if(!['pedal','dry','C3','C4'].includes(mode))throw RangeError('program');
const isolated=['C3','C4'].includes(mode),variant='K750',layout='wide',velocity=Number(velocityArg);
if(![24,76,127].includes(velocity))throw RangeError('velocity');
const id=isolated?mode+'-v'+velocity:'original-phrase-'+mode;
const seconds=isolated?3:10;
const notes=isolated?[mode==='C3'?48:60]:phraseNotes;
const events=isolated?[{ms:0,type:'on',midi:notes[0],velocity},{ms:2200,type:'off',midi:notes[0]}]:phrase().filter(e=>mode==='pedal'||e.type!=='pedal');
const q=renderImpactTrial(hp,{notes,events,variant,seconds,releaseRate:25,distance:.3,lossFactor:1,layout,speedFactor:Number(speedArg),feltFactor:Number(feltArg)});
// Fixed shared listening headroom across all candidates, not per-chord normalization.
const gain=S50_REFERENCE.gain*.20;
const y=q.channels.map(x=>{let N=1;while(N<x.length)N*=2;const re=new Float64Array(N),im=new Float64Array(N);re.set(x);hp.fft(re,im);for(let i=0;i<N;i++){const f=Math.min(i,N-i)*48000/N,w=f<=8000?1:f>=12000?0:.5*(1+Math.cos(Math.PI*(f-8000)/4000));re[i]*=w;im[i]*=w;}hp.fft(re,im,true);return re.slice(0,x.length);});
const hi=wave24(y,48000,gain),lo=waveBytes(y,48000,gain),pair=inspectPair(lo.bytes,hi.bytes);
if(hi.clipped||lo.clipped||hi.peak>.85||pair.frames!==Math.round(seconds*48000)+q.meta.maxDelay)throw Error('chord export gate');
const rms=(a,b)=>{let s=0,n=0;for(const ch of y)for(let i=Math.round(a*48000);i<Math.round(b*48000);i++){s+=(ch[i]*gain)**2;n++;}return 10*Math.log10(Math.max(s/n,1e-30));};
const metrics=isolated?{attack:rms(0,.05),held:rms(1,1.5),release:rms(2.5,2.7)}:{attack:rms(0,.05),initial:rms(0,.5),arpeggio:rms(1,1.5),chord:rms(3.5,3.6),held:rms(4.2,4.4),pedalTail:rms(5.1,5.3),afterPedal:rms(5.6,5.8),end:rms(9,9.5)};
const spectrum=(a,b)=>{
 const N=4096,bands=[0,250,1000,3000,6000,24000.001],sums=[0,0,0,0,0];
 for(const ch of y)for(let off=Math.round(a*48000);off+N<=Math.round(b*48000);off+=N/2){
  const re=new Float64Array(N),im=new Float64Array(N);
  for(let i=0;i<N;i++)re[i]=ch[off+i]*(.5-.5*Math.cos(2*Math.PI*i/(N-1)));
  hp.fft(re,im);
  for(let i=0;i<=N/2;i++){const f=i*48000/N,k=bands.findIndex((v,j)=>j>0&&f<v)-1;if(k>=0)sums[k]+=(re[i]**2+im[i]**2)*(i===0||i===N/2?1:2);}
 }
 const total=sums.reduce((s,x)=>s+x,0);return sums.map(v=>100*v/total);
};
const spectral={bandsHz:[0,250,1000,3000,6000,24000],initial:spectrum(0,.5),active:spectrum(0,isolated?2.2:8.2)};
const activeRms=rms(0,seconds),listenGain=Math.min(gain*10**((-30-activeRms)/20),gain*.8/Math.max(hi.peak,1e-12));
const listen=wave24(y,48000,listenGain);
if(listen.clipped)throw Error('listening gain clipping');
const sha=createHash('sha256').update(hi.bytes).digest('hex'),result={...q.meta,metrics,spectral,activeRms,listenGain,listenRms:activeRms+20*Math.log10(listenGain/gain),caseId:id,gain,peak:hi.peak,clipped:hi.clipped,pair,sha256:sha,scope:'continuous shared board, staggered/repeated hammer strikes and R2 two-axis release; fixed .20 S50 gain; fixed .3m height, wide bridge layout; isolated hammer speed/felt sensitivity'};
mkdirSync(out,{recursive:true});const stem=out+'/'+id+'_'+variant+'_S'+speedArg+'_F'+feltArg+'_impact';
writeFileSync(stem+'_24bit.wav',hi.bytes,{flag:'wx'});writeFileSync(stem+'.wav',lo.bytes,{flag:'wx'});writeFileSync(stem+'.json',JSON.stringify(result,null,2),{flag:'wx'});
writeFileSync(stem+'_matched_24bit.wav',listen.bytes,{flag:'wx'});
const small=result;console.log('F11U_R7_RESULT '+JSON.stringify(small));
