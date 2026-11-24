import {renderExtendedD4,EXTENDED_NOTES} from './f10e-d4-extension.mjs';
import {lossOptions} from './f10f-d4-sustain.mjs';
// Fixed passive string-loss coefficients for the entire seven-note pilot.
export const STRING_FACTORS=Object.freeze([1,.5,.25]);
export function trialLoss(options,factor){
 if(!STRING_FACTORS.includes(factor))throw RangeError('loss factor');
 const baseline=lossOptions(options,1);
 return {...baseline,verticalLoss:[.2*factor,.0002],horizontalLoss:[.1*factor,.00012]};
}
export function renderD4LossPilot(hp,{midi=60,midiVelocity=76,seconds=.5,prior=null,factor=.5}={}){
 if(!EXTENDED_NOTES.includes(midi)||!STRING_FACTORS.includes(factor))throw RangeError('loss pilot scope');
 if(prior&&(prior.lossPilot!==true||prior.sustainFactor!==factor||prior.midi!==midi))throw Error('loss pilot checkpoint mismatch');
 let losses=null;
 class LossBridge extends hp.PolarizedBridge{
  constructor(wires,options,helpers){
   const adjusted=trialLoss(options,factor);
   super(wires,adjusted,helpers);
   losses={verticalLoss:adjusted.verticalLoss,horizontalLoss:adjusted.horizontalLoss};
  }
 }
 const q=renderExtendedD4({...hp,PolarizedBridge:LossBridge},{midi,midiVelocity,seconds,prior});
 if(!losses)throw Error('loss not applied');
 return {...q,checkpoint:{...q.checkpoint,lossPilot:true,sustainFactor:factor},meta:{...q.meta,sustainFactor:factor,actualStringLoss:losses}};
}
