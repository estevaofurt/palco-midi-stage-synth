import {renderFeltSensitivity} from './f9-felt-sensitivity.mjs';
import {hammerSpeed} from './f9-midi-velocity.mjs';
// Isolate structural board loss; no changes to string losses, felt, joint, radiation, or digital gain.
export const BOARD_LOSS_MULTIPLIERS=Object.freeze([1,2,4]);
export function renderRattleBoard(hp,{midiVelocity=76,multiplier=1,seconds=.1,prior=null}={}){
 if(!BOARD_LOSS_MULTIPLIERS.includes(multiplier))throw RangeError('board loss multiplier');
 const velocity=hammerSpeed(midiVelocity);if(velocity===null)throw RangeError('note-off');
 if(prior&&(prior.multiplier!==multiplier||prior.midiVelocity!==midiVelocity))throw Error('board diagnostic checkpoint mismatch');
 let board=null;
 class DiagnosticBoard extends hp.ResistiveBoard{
  constructor(p,modes,patch,h,options,helpers){
   if(options.loss0!==1||options.lossSlope!==.00025)throw Error('unexpected baseline board loss');
   super(p,modes,patch,h,{...options,loss0:options.loss0*multiplier,lossSlope:options.lossSlope*multiplier},helpers);
   board=this;
  }
 }
 const q=renderFeltSensitivity({...hp,ResistiveBoard:DiagnosticBoard},{seconds,velocity,prior,feltFactor:1.5});
 return {...q,checkpoint:{...q.checkpoint,multiplier,midiVelocity},meta:{...q.meta,multiplier,midiVelocity,boardLoss0:multiplier,boardLossSlope:.00025*multiplier,nearestBoardModes:[221.19140625,240.234375,279.78515625,370.60546875].map(f=>({targetHz:f,modes:board.modes.map(m=>({frequencyHz:m.frequencyHz,patchWeight:m.w})).sort((a,b)=>Math.abs(a.frequencyHz-f)-Math.abs(b.frequencyHz-f)).slice(0,3)}))}};
}
