import {renderFeltSensitivity} from './f9-felt-sensitivity.mjs';
import {pilotGeometry,pilotWire} from './f10-pilot-geometry.mjs';
export function renderRegisterPilot(hp,{midi=60,prior=null,seconds=.5,velocity=1}={}){
 const geometry=pilotGeometry(midi);
 if(prior&&prior.midi!==midi)throw Error('note checkpoint mismatch');
 // Original integrator passes the C4 unison targets; transpose those targets and scale length.
 const base=hp.makeDesign,center=440*2**(-9/12),ratio=2**((midi-60)/12);
 const makeDesign=(solidWire,options)=>{
  if(!Number.isFinite(options?.f1Hz)||Math.abs(1200*Math.log2(options.f1Hz/center))>.50000001)throw Error('unexpected pilot wire request');
  return midi===60?base(solidWire,options):base(solidWire,{...options,lengthM:geometry.lengthM,diameterM:geometry.diameterM,f1Hz:options.f1Hz*ratio});
 };
 const q=renderFeltSensitivity({...hp,makeDesign},{prior,seconds,velocity,feltFactor:1.5});
 return {...q,checkpoint:{...q.checkpoint,midi},meta:{...q.meta,midi,geometry,centralWire:pilotWire(hp,midi)}};
}
