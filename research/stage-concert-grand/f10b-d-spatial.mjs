import {renderModelDRegister,MODEL_D} from './f10-model-d-register.mjs';
import {ribbedPatchWeight} from './ribbed-plate.mjs';
// F10b isolated G4 sensitivity. Coordinates are hypotheses, not a measured piano bridge.
export const PATCHES=Object.freeze({reference:0,minus8cm:-.08,plus8cm:.08});
export function patchFor(patch,variant){
 if(!Object.hasOwn(PATCHES,variant))throw RangeError('patch variant');
 if(patch.xM!==.83||patch.yM!==.46||patch.dxM!==.04||patch.dyM!==.025)throw Error('unexpected baseline patch');
 return {...patch,xM:patch.xM+PATCHES[variant]};
}
export function renderDSpatial(hp,{midi=67,midiVelocity=76,seconds=.5,prior=null,variant='reference'}={}){
 if(!Object.hasOwn(PATCHES,variant)||midi!==67)throw RangeError('G4 spatial pilot only');
 if(prior&&prior.spatialVariant!==variant)throw Error('spatial checkpoint mismatch');
 let observed=null;
 class SpatialBoard extends hp.ResistiveBoard{
  constructor(p,modes,patch,h,options,helpers){
   const selected=patchFor(patch,variant);
   super(p,modes,selected,h,options,helpers);
   observed={patch:selected,modes:modes.filter(m=>m.frequencyHz>=340&&m.frequencyHz<=440).map(m=>({
    frequencyHz:m.frequencyHz,weight:ribbedPatchWeight(p,m,selected,helpers.patchWeight)
   }))};
  }
 }
 const q=renderModelDRegister({...hp,ResistiveBoard:SpatialBoard},{midi,midiVelocity,seconds,prior});
 if(!observed||q.meta.multiplier!==MODEL_D.multiplier)throw Error('spatial scope');
 return {...q,checkpoint:{...q.checkpoint,spatialVariant:variant},meta:{...q.meta,spatialVariant:variant,spatial:observed}};
}
