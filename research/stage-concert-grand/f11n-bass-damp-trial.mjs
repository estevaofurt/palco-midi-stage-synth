import {renderBassPilot} from './f11d-bass-render.mjs';
import {modalCoefficients} from './exact-modal.mjs';
import {cholesky} from './radiation-loading.mjs';
// Global fixed set, no per-note damping or output EQ. Factors relative to S50.
export const TARGETS=Object.freeze([102.00990901829908,128.73539039969043,129.01313417136907,197.15936784432006]);
export const DAMP_VARIANTS=Object.freeze({A:1,M2:2,M4:4});
export function applyBassModeLoss(board,variant){
 if(!Object.hasOwn(DAMP_VARIANTS,variant))throw RangeError('bass damping variant');
 const factor=DAMP_VARIANTS[variant],before=board.modes.map(m=>m.coeff);
 const ids=TARGETS.map(f=>{
  const matches=board.modes.map((m,i)=>({i,f:m.frequencyHz})).filter(q=>Math.abs(q.f-f)<.001);
  if(matches.length!==1)throw Error('mode identity');
  return matches[0].i;
 });
 const chosen=new Set(ids);
 if(chosen.size!==TARGETS.length)throw Error('duplicate targets');
 for(const i of ids){
  const q=before[i],expected=6*(1+.00025*2*Math.PI*q.frequencyHz);
  if(Math.abs(q.dampingNsM-expected)>1e-10)throw Error('unexpected S50 baseline');
  if(factor!==1)board.modes[i].coeff=modalCoefficients({massKg:q.massKg,frequencyHz:q.frequencyHz,dampingNsM:q.dampingNsM*factor,dt:q.dt});
 }
 if(factor!==1){
  board.blocks=board.blocks.map(b=>{
   if(!b.indices.some(i=>chosen.has(i)))return b;
   const g=b.indices.map(i=>Math.sqrt(board.modes[i].coeff.G));
   return {...b,g,L:cholesky(b.R.map((row,i)=>row.map((v,j)=>+(i===j)+g[i]*v*g[j]/board.h)))};
  });
  const response=board.increment(1,true);board.G=board.modes.reduce((s,m,i)=>s+m.w*response[i],0);
 }
 if(!(board.G>0)||board.modes.some((m,i)=>!chosen.has(i)&&m.coeff!==before[i]))throw Error('damping scope');
 return {variant,factor,modeCount:board.modes.length,modes:ids.map(i=>({i,hz:board.modes[i].frequencyHz,before:before[i].dampingNsM,after:board.modes[i].coeff.dampingNsM}))};
}
export function renderBassDampTrial(hp,{midi=48,midiVelocity=127,seconds=.5,prior=null,variant='A'}={}){
 if(![36,43,48].includes(midi)||!Object.hasOwn(DAMP_VARIANTS,variant))throw RangeError('trial scope');
 if(prior&&prior.dampVariant!==variant)throw Error('damping checkpoint mismatch');
 let loss=null;
 class Joint extends hp.BoardCoupledBridge{
  constructor(bridge,board,options){loss=applyBassModeLoss(board,variant);super(bridge,board,options);}
 }
 const q=renderBassPilot({...hp,BoardCoupledBridge:Joint},{midi,count:2,midiVelocity,seconds,prior});
 if(!loss)throw Error('missing damping metadata');
 return {...q,checkpoint:{...q.checkpoint,dampVariant:variant},meta:{...q.meta,dampVariant:variant,bassModeLoss:loss}};
}
