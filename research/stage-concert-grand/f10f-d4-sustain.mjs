import {renderD4Board} from './f10d-d4-board.mjs';
// Hypothesis: reduce only frequency-independent string losses, not board damping.
export const LOSS_FACTORS=Object.freeze([1,.5]);
export function lossOptions(options,factor){
 if(!LOSS_FACTORS.includes(factor))throw RangeError('loss factor');
 if(JSON.stringify(options.verticalLoss)!=='[0.2,0.0002]'||JSON.stringify(options.horizontalLoss)!=='[0.1,0.00012]')throw Error('unexpected baseline string losses');
 return {...options,verticalLoss:[.2*factor,.0002],horizontalLoss:[.1*factor,.00012]};
}
export function renderD4Sustain(hp,{midi=60,midiVelocity=76,seconds=.5,prior=null,factor=.5}={}){
 if(![60,67].includes(midi)||!LOSS_FACTORS.includes(factor))throw RangeError('sustain trial scope');
 if(prior&&prior.sustainFactor!==factor)throw Error('sustain checkpoint mismatch');
 let losses=null;
 class SustainBridge extends hp.PolarizedBridge{
  constructor(wires,options,helpers){
   const adjusted=lossOptions(options,factor);
   super(wires,adjusted,helpers);
   losses={verticalLoss:adjusted.verticalLoss,horizontalLoss:adjusted.horizontalLoss};
  }
 }
 const q=renderD4Board({...hp,PolarizedBridge:SustainBridge},{midi,midiVelocity,seconds,prior});
 if(!losses)throw Error('loss trial not applied');
 return {...q,checkpoint:{...q.checkpoint,sustainFactor:factor},meta:{...q.meta,sustainFactor:factor,actualStringLoss:losses}};
}
