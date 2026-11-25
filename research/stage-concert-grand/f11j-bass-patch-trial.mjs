import {renderBassPilot} from './f11d-bass-render.mjs';
export const PATCH_VARIANTS=Object.freeze({A:.83,L:.75,LL:.67,LM:.71});
// Spatial sensitivity only: same passive modal coefficients, joint and wound wires.
// Change the conjugate excitation/observation port before board construction.
export function renderBassPatchTrial(hp,{midi=48,midiVelocity=127,seconds=.5,prior=null,variant='A'}={}){
 if(![43,48].includes(midi)||!Object.hasOwn(PATCH_VARIANTS,variant))throw RangeError('bass patch trial scope');
 if(prior&&prior.patchVariant!==variant)throw Error('patch checkpoint mismatch');
 let patchActual=null,weights=null;
 class SpatialBoard extends hp.ResistiveBoard{
  constructor(p,modes,patch,h,options,helpers){
   if(patch.xM!==.83||patch.yM!==.46||patch.dxM!==.04||patch.dyM!==.025)throw Error('baseline patch changed');
   const next=variant==='A'?patch:{...patch,xM:PATCH_VARIANTS[variant]};
   super(p,modes,next,h,options,helpers);
   patchActual={...next};weights=this.modes.map(m=>m.w);
  }
 }
 const q=renderBassPilot({...hp,ResistiveBoard:SpatialBoard},{midi,count:2,midiVelocity,seconds,prior});
 if(!patchActual||weights.length!==337||weights.some(x=>!Number.isFinite(x)))throw Error('patch capture');
 return {...q,checkpoint:{...q.checkpoint,patchVariant:variant},meta:{...q.meta,patchVariant:variant,patchActual,portWeights:weights}};
}
