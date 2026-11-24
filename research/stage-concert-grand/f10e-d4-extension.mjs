import {renderHybridRattle} from './f9-rattle-hybrid.mjs';
import {renderD4Board,BOARD_VARIANT} from './f10d-d4-board.mjs';
import {applyLocalLoss} from './f10c-d-local.mjs';
import {MODEL_D} from './f10-model-d-register.mjs';
import {PILOT_NOTES,pilotGeometry,pilotWire} from './f10-pilot-geometry.mjs';
// Hypothetical bare-steel trichord scale only; not a full piano geometry.
export const EXTENDED_NOTES=Object.freeze([53,55,57,60,64,67,72]);
export function extendedGeometry(midi){
 if(!EXTENDED_NOTES.includes(midi))throw RangeError('extended pilot note');
 if(PILOT_NOTES.includes(midi))return pilotGeometry(midi);
 const ratio=2**((midi-60)/12);
 return {midi,f1Hz:440*2**((midi-69)/12),lengthM:.65/ratio,diameterM:.00096,youngPa:200e9,densityKgM3:7850};
}
export function extendedWire(hp,midi,cents=0){
 if(PILOT_NOTES.includes(midi))return pilotWire(hp,midi,cents);
 const g=extendedGeometry(midi);
 if(!Number.isFinite(cents)||Math.abs(cents)>.5)throw RangeError('unison cents');
 return hp.makeDesign(hp.solidWire,{lengthM:g.lengthM,diameterM:g.diameterM,youngPa:g.youngPa,densityKgM3:g.densityKgM3,f1Hz:440*2**(-9/12+cents/1200)*2**((midi-60)/12)});
}
export function renderExtendedD4(hp,{midi=60,midiVelocity=76,seconds=.5,prior=null}={}){
 const geometry=extendedGeometry(midi);
 if(prior&&(prior.extendedD4!==true||prior.midi!==midi||prior.boardVariant!==BOARD_VARIANT))throw Error('extended checkpoint mismatch');
 if(PILOT_NOTES.includes(midi)){
  const q=renderD4Board(hp,{midi,midiVelocity,seconds,prior});
  return {...q,checkpoint:{...q.checkpoint,extendedD4:true}};
 }
 let local=null,signature=null;
 class FixedBoardJoint extends hp.BoardCoupledBridge{
  constructor(bridge,board,options){
   local=applyLocalLoss(board,BOARD_VARIANT);
   signature=board.modes.map(m=>[m.frequencyHz,m.coeff.dampingNsM]);
   super(bridge,board,options);
  }
 }
 const base=hp.makeDesign,center=440*2**(-9/12),ratio=2**((midi-60)/12);
 const makeDesign=(solidWire,options)=>{
  if(!Number.isFinite(options?.f1Hz)||Math.abs(1200*Math.log2(options.f1Hz/center))>.50000001)throw Error('unexpected wire request');
  return base(solidWire,{...options,lengthM:geometry.lengthM,diameterM:geometry.diameterM,f1Hz:options.f1Hz*ratio});
 };
 const q=renderHybridRattle({...hp,makeDesign,BoardCoupledBridge:FixedBoardJoint},{midiVelocity,seconds,prior,multiplier:MODEL_D.multiplier});
 if(!local||!signature)throw Error('board scope');
 return {...q,checkpoint:{...q.checkpoint,midi,boardVariant:BOARD_VARIANT,extendedD4:true},meta:{...q.meta,model:'D',midi,geometry,centralWire:extendedWire(hp,midi),boardVariant:BOARD_VARIANT,local,boardSignature:signature,selection:{...q.meta.selection,modes:q.meta.selection.modes.map(m=>({...m,damping:local.modes.find(x=>x.index===m.index)?.after??m.damping}))}}};
}
