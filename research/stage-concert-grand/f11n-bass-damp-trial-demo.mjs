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
import {MODEL_D} from './f10-model-d-register.mjs';
import {BOARD_VARIANT} from './f10d-d4-board.mjs';
import {S50_REFERENCE} from './f11a-s50-scale.mjs';
import {bassCandidate} from './f11c-bass-candidates.mjs';
import {BASS_NOTES} from './f11d-bass-render.mjs';
import {renderBassDampTrial as renderChunk,DAMP_VARIANTS as PITCH_VARIANTS} from './f11n-bass-damp-trial.mjs';
import {pitchSpectrum} from './f11f-bass-pitch.mjs';
import {hammerSpeed} from './f9-midi-velocity.mjs';
import {inspectPair} from './f9-soft-pcm-audit.mjs';
import {inspectRattleWindow} from './f9-rattle-spectrum.mjs';

const hp={fft,solidWire,makeDesign,stringMode,spatialWeight,plateDesign,plateModes,patchWeight,ribDesign,generalizedEigen,mindlinModes,PolarizedBridge,PolarizedHammer,BoardCoupledBridge,radiationGrid,surfaceShape,radiationKernel,ResistiveBoard,relaxMemory};

function joinChunks(chunks,hp,rate=48000){
 const lengths=chunks.map(q=>Math.round(q.meta.seconds*rate)),n=lengths.reduce((a,b)=>a+b,0),tail=chunks[0].channels[0].length-lengths[0];
 const y=[new Float64Array(n+tail),new Float64Array(n+tail)];let offset=0;
 for(let k=0;k<chunks.length;k++){const q=chunks[k];if(q.channels.some(c=>c.length!==lengths[k]+tail))throw Error("chunk length");for(let ch=0;ch<2;ch++)for(let i=0;i<q.channels[ch].length;i++)y[ch][offset+i]+=q.channels[ch][i];offset+=lengths[k];}
 let N=1;while(N<y[0].length)N*=2;
 return y.map(x=>{const re=new Float64Array(N),im=new Float64Array(N);re.set(x);hp.fft(re,im);for(let i=0;i<N;i++){const f=Math.min(i,N-i)*rate/N,w=f<=8000?1:f>=12000?0:.5*(1+Math.cos(Math.PI*(f-8000)/4000));re[i]*=w;im[i]*=w;}hp.fft(re,im,true);return re.slice(0,x.length);});
}

const [dir='f11n-bass',midiArg='60',touchArg='76',variantArg='A']=process.argv.slice(2);
const count=2,midi=Number(midiArg),variant=variantArg,duration=8,midiVelocity=Number(touchArg),velocity=hammerSpeed(midiVelocity);
if(![36,43,48].includes(midi)||!Object.hasOwn(PITCH_VARIANTS,variant)||![24,76,127].includes(midiVelocity))throw RangeError('pilot note or touch');
const gain=S50_REFERENCE.gain;
const wire=bassCandidate(midi),chunks=[];let prior=null;
for(let i=0;i<duration;i++){const q=renderChunk(hp,{seconds:1,midiVelocity,midi,variant,prior});chunks.push({...q,channels:q.channels.map(c=>Float32Array.from(c))});prior=q.checkpoint;console.log(JSON.stringify(q.meta));}
const y=joinChunks(chunks,hp),original=wave24(y,48000,MODEL_D.gain),w=waveBytes(y,48000,gain);
if(!Number.isFinite(original.peak)||Math.abs(w.peak-original.peak*.75)>1e-12)throw Error('gain-only audit');if(w.clipped){console.log('F11N_DAMP_REJECT '+JSON.stringify({variant,midi,midiVelocity,peak:w.peak,clipped:w.clipped}));throw Error('clipping');}
mkdirSync(dir,{recursive:true});const stem='S50_BASS_' + count + '_MIDI'+midi+'_touch'+midiVelocity+'_'+variant+'_8s';
writeFileSync(dir+'/'+stem+'.wav',w.bytes,{flag:'wx'});
writeFileSync(dir+'/'+stem+'.json',JSON.stringify({model:'D',variant,local:chunks[0].meta.local,actualStringLoss:chunks[0].meta.actualStringLoss,boardSignature:chunks[0].meta.boardSignature,duration,velocity,midi,midiVelocity,wire,feltFactor:1.5,gain,peak:w.peak,clipped:w.clipped,chunks:chunks.map(q=>q.meta)},null,2),{flag:'wx'});

const pcm=decodePcmChannels(w.bytes,parsePcm16),audit=compareQuantization(y,pcm.channels,48000);
const prePcm=analyzeSustain(y.map(c=>Float64Array.from(c,v=>v*gain)),48000,fft,{excludeEndS:.04,f1:wire.f1Hz,B:wire.B});
writeFileSync(dir+'/'+stem+'_precision.json',JSON.stringify(audit,null,2),{flag:'wx'});
writeFileSync(dir+'/'+stem+'_float_analysis.json',JSON.stringify(prePcm,null,2),{flag:'wx'});
console.log('F11N_DAMP_WINDOWS '+JSON.stringify(prePcm.windows));

const hi=wave24(y,48000,gain);if(hi.clipped||hi.peak!==w.peak)throw Error('24-bit export mismatch');
writeFileSync(dir+'/'+stem+'_24bit.wav',hi.bytes,{flag:'wx'});
console.log('F11N_DAMP_EXPORT '+JSON.stringify({frames:y[0].length,peak:hi.peak,clipped:hi.clipped,pcm16Bytes:w.bytes.length,pcm24Bytes:hi.bytes.length}));

const pressure=y.map(c=>Float64Array.from(c,v=>v*gain));
const windows=[[.025,.525],[.525,1.025],[1.025,1.525],[2.025,2.525]].map(([startS,endS])=>inspectRattleWindow(pressure,48000,fft,{startS,endS,f1:wire.f1Hz,B:wire.B}));
const pair=inspectPair(w.bytes,hi.bytes);
if(pair.frames!==duration*48000+239||Math.abs(pair.rms24-prePcm.windows[0].rms)>.5/8388607+1e-12)throw Error('PCM gate');
const pitch=[[.25,1.25],[1,3],[3,7]].map(([a,b])=>pitchSpectrum(pressure,48000,a,b,wire.f1Hz,wire.B));
const result={pitch,parameters:{factor:PITCH_VARIANTS[variant],modes:chunks[0].meta.bassModeLoss.modes},pair,relativeDrops:prePcm.broadband.drops,partialDrops:prePcm.partialDrops,model:'S50-bass',variant,local:chunks[0].meta.local,midi,midiVelocity,duration,wire,gain,peak:hi.peak,clipped:hi.clipped,originalPeak:original.peak,originalClipped:original.clipped,windows,rms:prePcm.windows.map(w=>({startS:w.startS,rms:w.rms,partials:w.partials})),count,attack:{peakForce:chunks[0].meta.peakForce,reboundMps:chunks[0].meta.reboundMps},maxBalance:Math.max(...chunks.map(q=>q.meta.maxBalance)),maxIncrease:Math.max(...chunks.map(q=>q.meta.maxIncrease))};
if(hi.peak>.85||result.maxBalance>1e-9||result.maxIncrease>1e-9||!result.rms.every(x=>Number.isFinite(x.rms)))throw Error('pilot gate');
writeFileSync(dir+'/'+stem+'_rattle.json',JSON.stringify(result,null,2),{flag:'wx'});
console.log('F11N_DAMP_RESULT '+JSON.stringify({...result,pitch:pitch.map(w=>({startS:w.startS,endS:w.endS,dominant:w.dominant,partials:w.partials.slice(0,4)})),rms:result.rms.filter(w=>[0,.5,1,2,4,6,7].includes(w.startS))}));
