import {renderModelDRegister,MODEL_D} from './f10-model-d-register.mjs';
import {modalCoefficients} from './exact-modal.mjs';
import {cholesky} from './radiation-loading.mjs';
// F10c: isolated G4 sensitivity of four nearby plate modes, not calibrated damping.
export const FACTORS=Object.freeze({reference:0,local6:6,local8:8});
export const TARGETS=Object.freeze([372.5984818599289,376.10992819640126,380.62893452755657,384.3371342573889]);
export function applyLocalLoss(board,variant){
 if(!Object.hasOwn(FACTORS,variant))throw RangeError('local variant');
 const factor=FACTORS[variant],before=board.modes.map(m=>m.coeff);
 const ids=TARGETS.map(f=>{
  const matches=board.modes.map((m,i)=>({i,f:m.frequencyHz})).filter(q=>Math.abs(q.f-f)<.001);
  if(matches.length!==1)throw Error('local mode identity changed');
  return matches[0].i;
 });
 const chosen=new Set(ids);
 if(chosen.size!==TARGETS.length)throw Error('duplicate local modes');
 for(const [j,i] of ids.entries()){
  const q=before[i],base=2*(1+.00025*2*Math.PI*q.frequencyHz),expected=(j===0?4:3)*base;
  if(Math.abs(q.dampingNsM-expected)>1e-10)throw Error('unexpected D baseline damping');
  if(factor)board.modes[i].coeff=modalCoefficients({massKg:q.massKg,frequencyHz:q.frequencyHz,dampingNsM:base*factor,dt:q.dt});
 }
 if(factor){
  board.blocks=board.blocks.map(b=>{
   if(!b.indices.some(i=>chosen.has(i)))return b;
   const g=b.indices.map(i=>Math.sqrt(board.modes[i].coeff.G));
   return {...b,g,L:cholesky(b.R.map((row,i)=>row.map((v,j)=>+(i===j)+g[i]*v*g[j]/board.h)))};
  });
  const response=board.increment(1,true);
  board.G=board.modes.reduce((s,m,i)=>s+m.w*response[i],0);
 }
 if(!(board.G>0)||board.modes.some((m,i)=>!chosen.has(i)&&m.coeff!==before[i]))throw Error('local loss scope');
 return {variant,factor,modeCount:board.modes.length,modifiedCount:factor?ids.length:0,compliance:board.G,modes:ids.map(i=>({index:i,frequencyHz:board.modes[i].frequencyHz,before:before[i].dampingNsM,after:board.modes[i].coeff.dampingNsM}))};
}
export function renderDLocal(hp,{midi=67,midiVelocity=76,seconds=.5,prior=null,variant='reference'}={}){
 if(midi!==67||!Object.hasOwn(FACTORS,variant))throw RangeError('G4 local damping only');
 if(prior&&prior.localVariant!==variant)throw Error('local checkpoint mismatch');
 let local=null;
 // The original D constructs its HybridBoard first. Update it BEFORE the
 // joint compliance and the fastBoard solver cache are built.
 class LocalJoint extends hp.BoardCoupledBridge{
  constructor(bridge,board,options){
   local=applyLocalLoss(board,variant);
   super(bridge,board,options);
  }
 }
 const q=renderModelDRegister({...hp,BoardCoupledBridge:LocalJoint},{midi,midiVelocity,seconds,prior});
 if(!local||q.meta.multiplier!==MODEL_D.multiplier)throw Error('local scope');
 // Original selection describes D before local trial; report final coefficients explicitly.
 return {...q,checkpoint:{...q.checkpoint,localVariant:variant},meta:{...q.meta,localVariant:variant,local,selection:{...q.meta.selection,modes:q.meta.selection.modes.map(m=>({...m,damping:local.modes.find(x=>x.index===m.index)?.after??m.damping}))}}};
}
