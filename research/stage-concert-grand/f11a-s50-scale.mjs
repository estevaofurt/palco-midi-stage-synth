import {renderHybridRattle} from './f9-rattle-hybrid.mjs';
import {renderD4LossPilot,trialLoss} from './f10g-d4-loss-pilot.mjs';
import {EXTENDED_NOTES,extendedGeometry,extendedWire} from './f10e-d4-extension.mjs';
import {BOARD_VARIANT} from './f10d-d4-board.mjs';
import {applyLocalLoss} from './f10c-d-local.mjs';
import {MODEL_D} from './f10-model-d-register.mjs';
// F11a: fill gaps within the already explored bare-steel trichord range.
export const SCALE_NOTES=Object.freeze(Array.from({length:20},(_,i)=>53+i));
export const NEW_NOTES=Object.freeze(SCALE_NOTES.filter(m=>!EXTENDED_NOTES.includes(m)));
export const S50_REFERENCE=Object.freeze({factor:.5,gain:MODEL_D.gain*.75,diagnosticGain:MODEL_D.gain});
export function scaleGeometry(midi){
 if(!SCALE_NOTES.includes(midi))throw RangeError('chromatic pilot range');
 if(EXTENDED_NOTES.includes(midi))return extendedGeometry(midi);
 const ratio=2**((midi-60)/12);
 return {midi,f1Hz:440*2**((midi-69)/12),lengthM:.65/ratio,diameterM:.00096,youngPa:200e9,densityKgM3:7850};
}
export function scaleWire(hp,midi,cents=0){
 const g=scaleGeometry(midi);
 if(EXTENDED_NOTES.includes(midi))return extendedWire(hp,midi,cents);
 if(!Number.isFinite(cents)||Math.abs(cents)>.5)throw RangeError('unison cents');
 return hp.makeDesign(hp.solidWire,{lengthM:g.lengthM,diameterM:g.diameterM,youngPa:g.youngPa,densityKgM3:g.densityKgM3,f1Hz:440*2**(-9/12+cents/1200)*2**((midi-60)/12)});
}
export function renderS50Scale(hp,{midi=60,midiVelocity=76,seconds=.5,prior=null}={}){
 const geometry=scaleGeometry(midi);
 if(prior&&(prior.s50Scale!==true||prior.midi!==midi||prior.sustainFactor!==.5||prior.boardVariant!==BOARD_VARIANT))throw Error('S50 scale checkpoint mismatch');
 if(EXTENDED_NOTES.includes(midi)){
  const q=renderD4LossPilot(hp,{midi,midiVelocity,seconds,prior,factor:.5});
  return {...q,checkpoint:{...q.checkpoint,s50Scale:true}};
 }
 let local=null,signature=null,losses=null;
 class ScaleJoint extends hp.BoardCoupledBridge{
  constructor(bridge,board,options){
   local=applyLocalLoss(board,BOARD_VARIANT);
   signature=board.modes.map(m=>[m.frequencyHz,m.coeff.dampingNsM]);
   super(bridge,board,options);
  }
 }
 class ScaleBridge extends hp.PolarizedBridge{
  constructor(wires,options,helpers){
   const adjusted=trialLoss(options,.5);
   super(wires,adjusted,helpers);
   losses={verticalLoss:adjusted.verticalLoss,horizontalLoss:adjusted.horizontalLoss};
  }
 }
 const base=hp.makeDesign,center=440*2**(-9/12),ratio=2**((midi-60)/12);
 const makeDesign=(solidWire,options)=>{
  if(!Number.isFinite(options?.f1Hz)||Math.abs(1200*Math.log2(options.f1Hz/center))>.50000001)throw Error('unexpected wire request');
  return base(solidWire,{...options,lengthM:geometry.lengthM,diameterM:geometry.diameterM,f1Hz:options.f1Hz*ratio});
 };
 const q=renderHybridRattle({...hp,makeDesign,BoardCoupledBridge:ScaleJoint,PolarizedBridge:ScaleBridge},{midiVelocity,seconds,prior,multiplier:MODEL_D.multiplier});
 if(!local||!signature||!losses)throw Error('S50 scale scope');
 return {...q,checkpoint:{...q.checkpoint,midi,boardVariant:BOARD_VARIANT,sustainFactor:.5,s50Scale:true},meta:{...q.meta,model:'D',midi,geometry,centralWire:scaleWire(hp,midi),boardVariant:BOARD_VARIANT,local,boardSignature:signature,sustainFactor:.5,actualStringLoss:losses,selection:{...q.meta.selection,modes:q.meta.selection.modes.map(m=>({...m,damping:local.modes.find(x=>x.index===m.index)?.after??m.damping}))}}};
}
