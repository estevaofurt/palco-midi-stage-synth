import {renderFeltSensitivity} from './f9-felt-sensitivity.mjs';
import {hammerSpeed} from './f9-midi-velocity.mjs';
import {modalCoefficients} from './exact-modal.mjs';
import {cholesky} from './radiation-loading.mjs';
// Diagnostic modal damping, not measured material loss or a frequency-domain audio filter.
export const SUSPECT_MODES=Object.freeze([222.731275232231,227.68107250086456,241.08558547455706,280.42521078052135,372.5984818599289]);
export function locateSuspectModes(modes){
 const ids=SUSPECT_MODES.map(f=>{
  const hits=modes.map((m,i)=>({i,delta:Math.abs(m.frequencyHz-f)})).filter(q=>q.delta<.001);
  if(hits.length!==1)throw Error('suspect mode identity changed '+f);
  return hits[0].i;
 });
 if(new Set(ids).size!==ids.length)throw Error('duplicate suspect mode');
 return ids;
}
export function selectStructuralLoss(board,multiplier){
 if(![1,4,8].includes(multiplier))throw RangeError('selective multiplier');
 const ids=locateSuspectModes(board.modes),chosen=new Set(ids);
 const before=board.modes.map(m=>m.coeff);
 if(multiplier!==1){
  for(const i of ids){const q=before[i];board.modes[i].coeff=modalCoefficients({massKg:q.massKg,frequencyHz:q.frequencyHz,dampingNsM:q.dampingNsM*multiplier,dt:q.dt});}
  // The radiative resistance matrix stays fixed; compliance-dependent factorization must change.
  board.blocks=board.blocks.map(b=>{
   if(!b.indices.some(i=>chosen.has(i)))return b;
   const g=b.indices.map(i=>Math.sqrt(board.modes[i].coeff.G));
   const L=cholesky(b.R.map((row,i)=>row.map((v,j)=>+(i===j)+g[i]*v*g[j]/board.h)));
   return {...b,g,L};
  });
  const response=board.increment(1,true);board.G=board.modes.reduce((s,m,i)=>s+m.w*response[i],0);
 }
 if(!(board.G>0)||board.modes.some((m,i)=>!chosen.has(i)&&m.coeff!==before[i]))throw Error('board scope or compliance');
 return {ids,modeCount:board.modes.length,modifiedCount:multiplier===1?0:ids.length,compliance:board.G,modes:ids.map(i=>({index:i,frequencyHz:board.modes[i].frequencyHz,originalDamping:before[i].dampingNsM,damping:board.modes[i].coeff.dampingNsM}))};
}
export function renderSelectiveRattle(hp,{midiVelocity=76,multiplier=1,seconds=.1,prior=null}={}){
 if(![1,4,8].includes(multiplier))throw RangeError('selective multiplier');
 const velocity=hammerSpeed(midiVelocity);if(velocity===null)throw RangeError('note-off');
 if(prior&&(prior.selectiveMultiplier!==multiplier||prior.midiVelocity!==midiVelocity))throw Error('selective checkpoint mismatch');
 let selection=null;
 class SelectiveBoard extends hp.ResistiveBoard{
  constructor(p,modes,patch,h,options,helpers){
   if(options.loss0!==1||options.lossSlope!==.00025)throw Error('baseline loss changed');
   super(p,modes,patch,h,options,helpers);
   selection=selectStructuralLoss(this,multiplier);
  }
 }
 const q=renderFeltSensitivity({...hp,ResistiveBoard:SelectiveBoard},{seconds,velocity,prior,feltFactor:1.5});
 return {...q,checkpoint:{...q.checkpoint,selectiveMultiplier:multiplier,midiVelocity},meta:{...q.meta,multiplier,midiVelocity,selection}};
}
