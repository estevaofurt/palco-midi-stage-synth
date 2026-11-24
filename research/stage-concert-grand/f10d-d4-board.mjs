import {renderModelDRegister,MODEL_D} from './f10-model-d-register.mjs';
import {applyLocalLoss} from './f10c-d-local.mjs';
import {PILOT_NOTES} from './f10-pilot-geometry.mjs';
// F10d: one fixed structural coefficient set for all pilot notes.
// Independent single-note simulations; NOT a polyphonic shared-state board.
export const BOARD_VARIANT='local8';
export function renderD4Board(hp,{midi=60,midiVelocity=76,seconds=.5,prior=null}={}){
 if(!PILOT_NOTES.includes(midi))throw RangeError('pilot note');
 if(prior&&(prior.boardVariant!==BOARD_VARIANT||prior.midi!==midi))throw Error('D4 board checkpoint mismatch');
 let local=null,signature=null;
 class FixedBoardJoint extends hp.BoardCoupledBridge{
  constructor(bridge,board,options){
   local=applyLocalLoss(board,BOARD_VARIANT);
   signature=board.modes.map(m=>[m.frequencyHz,m.coeff.dampingNsM]);
   super(bridge,board,options);
  }
 }
 const q=renderModelDRegister({...hp,BoardCoupledBridge:FixedBoardJoint},{midi,midiVelocity,seconds,prior});
 if(!local||!signature||q.meta.multiplier!==MODEL_D.multiplier)throw Error('D4 board scope');
 return {...q,checkpoint:{...q.checkpoint,boardVariant:BOARD_VARIANT},meta:{...q.meta,boardVariant:BOARD_VARIANT,local,boardSignature:signature,selection:{...q.meta.selection,modes:q.meta.selection.modes.map(m=>({...m,damping:local.modes.find(x=>x.index===m.index)?.after??m.damping}))}}};
}
