import {renderHybridRattle} from './f9-rattle-hybrid.mjs';
export const MODEL_D=Object.freeze({multiplier:3,suspectMultiplier:4,feltFactor:1.5,gain:.36767023440034063});
import {pilotGeometry,pilotWire} from './f10-pilot-geometry.mjs';
export function renderModelDRegister(hp,{midi=60,prior=null,seconds=.5,midiVelocity=76}={}){
 const geometry=pilotGeometry(midi);
 if(prior&&prior.midi!==midi)throw Error('note checkpoint mismatch');
 // Original integrator passes the C4 unison targets; transpose those targets and scale length.
 const base=hp.makeDesign,center=440*2**(-9/12),ratio=2**((midi-60)/12);
 const makeDesign=(solidWire,options)=>{
  if(!Number.isFinite(options?.f1Hz)||Math.abs(1200*Math.log2(options.f1Hz/center))>.50000001)throw Error('unexpected pilot wire request');
  return midi===60?base(solidWire,options):base(solidWire,{...options,lengthM:geometry.lengthM,diameterM:geometry.diameterM,f1Hz:options.f1Hz*ratio});
 };
 const q=renderHybridRattle({...hp,makeDesign},{prior,seconds,midiVelocity,multiplier:MODEL_D.multiplier});
 return {...q,checkpoint:{...q.checkpoint,midi},meta:{...q.meta,model:'D',midi,geometry,centralWire:pilotWire(hp,midi)}};
}
