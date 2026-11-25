import {renderBassPilot} from './f11d-bass-render.mjs';
export const JOINT_VARIANTS=Object.freeze({A:1e7,J25:2.5e6,J400:4e7});
// Isolate joint compliance from bridge inertia, port location and unison.
// Positive spring and unchanged nonnegative dashpot retain the passive formulation.
export function renderBassJointTrial(hp,{midi=48,midiVelocity=127,seconds=.5,prior=null,variant='A'}={}){
 if(![43,48].includes(midi)||!Object.hasOwn(JOINT_VARIANTS,variant))throw RangeError('joint trial scope');
 if(prior&&prior.jointVariant!==variant)throw Error('joint checkpoint mismatch');
 let actual=null;
 class TrialJoint extends hp.BoardCoupledBridge{
  constructor(bridge,board,options){
   if(options!==undefined)throw Error('baseline joint options changed');
   super(bridge,board,variant==='A'?options:{jointK:JOINT_VARIANTS[variant],jointC:1});
   actual={jointK:this.k,jointC:this.c,portWeights:board.modes.map(m=>m.w),bridgeMassV:bridge.vAxis.mB,bridgeMassH:bridge.hAxis.mB};
  }
 }
 const q=renderBassPilot({...hp,BoardCoupledBridge:TrialJoint},{midi,count:2,midiVelocity,seconds,prior});
 if(!actual||actual.jointK!==JOINT_VARIANTS[variant]||actual.jointC!==1)throw Error('joint capture');
 return {...q,checkpoint:{...q.checkpoint,jointVariant:variant},meta:{...q.meta,jointVariant:variant,...actual}};
}
