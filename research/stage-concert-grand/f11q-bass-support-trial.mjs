import {renderBassPilot} from './f11d-bass-render.mjs';
export const SUPPORT_VARIANTS=Object.freeze({A:0,K500:5e5,K750:7.5e5,K1000:1e6});
// Hypothetical passive restoring support along the previously free principal
// bridge direction. No EQ, no tension adjustment, no changes to the board.
export function renderBassSupportTrial(hp,{midi=48,midiVelocity=76,seconds=.05,prior=null,variant='A'}={}){
 if(![36,43,48].includes(midi)||!Object.hasOwn(SUPPORT_VARIANTS,variant))throw RangeError('support trial');
 if(prior&&prior.supportVariant!==variant)throw Error('support checkpoint mismatch');
 let actual=null;
 class SupportBridge extends hp.PolarizedBridge{
  constructor(wires,options,helpers){
   if(options.stiffness[0]!==0||options.stiffness[1]!==2e6)throw Error('support baseline changed');
   const k=SUPPORT_VARIANTS[variant],stiffness=[k,2e6];
   super(wires,variant==='A'?options:{...options,stiffness},helpers);
   actual={stiffness,K:{...this.K},C:{...this.C},massV:this.vAxis.mB,massH:this.hAxis.mB};
  }
 }
 const q=renderBassPilot({...hp,PolarizedBridge:SupportBridge},{midi,count:2,midiVelocity,seconds,prior});
 if(!actual)throw Error('support capture');
 return {...q,checkpoint:{...q.checkpoint,supportVariant:variant},meta:{...q.meta,supportVariant:variant,support:actual}};
}
