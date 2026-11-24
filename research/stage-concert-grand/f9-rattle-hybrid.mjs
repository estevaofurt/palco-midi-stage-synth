import {renderFeltSensitivity} from './f9-felt-sensitivity.mjs';
import {hammerSpeed} from './f9-midi-velocity.mjs';
import {locateSuspectModes} from './f9-rattle-selective.mjs';
import {modalCoefficients} from './exact-modal.mjs';
import {cholesky} from './radiation-loading.mjs';
// Isolated, passive trial: global structural damping 2/3/4 times baseline,
// five suspect modes fixed at 4 times original damping. No audio filtering.
export function renderHybridRattle(hp,{midiVelocity=76,multiplier=2,seconds=.1,prior=null}={}){
 if(![2,3,4].includes(multiplier))throw RangeError('hybrid global multiplier');
 const velocity=hammerSpeed(midiVelocity);if(velocity===null)throw RangeError('note-off');
 if(prior&&(prior.hybridMultiplier!==multiplier||prior.midiVelocity!==midiVelocity))throw Error('hybrid checkpoint mismatch');
 let selection=null;
 class HybridBoard extends hp.ResistiveBoard{
  constructor(p,modes,patch,h,options,helpers){
   if(options.loss0!==1||options.lossSlope!==.00025)throw Error('baseline loss changed');
   super(p,modes,patch,h,{...options,loss0:options.loss0*multiplier,lossSlope:options.lossSlope*multiplier},helpers);
   const ids=locateSuspectModes(this.modes),chosen=new Set(ids),before=this.modes.map(m=>m.coeff);
   if(multiplier!==4){
    for(const i of ids){
     const q=before[i],d=2*(4+.001*2*Math.PI*q.frequencyHz);
     this.modes[i].coeff=modalCoefficients({massKg:q.massKg,frequencyHz:q.frequencyHz,dampingNsM:d,dt:q.dt});
    }
    this.blocks=this.blocks.map(b=>{
     if(!b.indices.some(i=>chosen.has(i)))return b;
     const g=b.indices.map(i=>Math.sqrt(this.modes[i].coeff.G));
     return {...b,g,L:cholesky(b.R.map((row,i)=>row.map((v,j)=>+(i===j)+g[i]*v*g[j]/h)))};
    });
    const response=this.increment(1,true);this.G=this.modes.reduce((s,m,i)=>s+m.w*response[i],0);
   }
   if(!(this.G>0)||this.modes.some((m,i)=>!chosen.has(i)&&m.coeff!==before[i]))throw Error('hybrid scope');
   selection={modeCount:this.modes.length,globalMultiplier:multiplier,suspectMultiplier:4,modifiedCount:multiplier===4?0:ids.length,modes:ids.map(i=>({index:i,frequencyHz:this.modes[i].frequencyHz,damping:this.modes[i].coeff.dampingNsM}))};
  }
 }
 const q=renderFeltSensitivity({...hp,ResistiveBoard:HybridBoard},{seconds,velocity,prior,feltFactor:1.5});
 return {...q,checkpoint:{...q.checkpoint,hybridMultiplier:multiplier,midiVelocity},meta:{...q.meta,multiplier,midiVelocity,selection}};
}
