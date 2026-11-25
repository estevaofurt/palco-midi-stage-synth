import {woundWire} from './f11c-wound-wire.mjs';
// Independent hypothetical bass scale: solve winding mass at a diagnostic tension,
// not a real piano scale, not fabrication parameters, not a sound-producing model.
export const BASS_ANCHORS=Object.freeze([
 Object.freeze({midi:36,lengthM:1.5,coreDiameterM:.0012}),
 Object.freeze({midi:43,lengthM:1.15,coreDiameterM:.0011}),
 Object.freeze({midi:48,lengthM:.90,coreDiameterM:.0010})
]);
export const DIAGNOSTIC_TENSION_N=650;
export function bassCandidate(midi,{tensionN=DIAGNOSTIC_TENSION_N}={}){
 const g=BASS_ANCHORS.find(x=>x.midi===midi);
 if(!g||!Number.isFinite(tensionN)||tensionN<=0)throw RangeError('bass pilot scope');
 const f1Hz=440*2**((midi-69)/12),make=d=>woundWire({...g,wrapDiameterM:d,f1Hz});
 let lo=.00005,hi=.0015;
 if(make(lo).tensionN>tensionN||make(hi).tensionN<tensionN)throw RangeError('target outside winding bracket');
 for(let i=0;i<60;i++){const mid=(lo+hi)/2;if(make(mid).tensionN<tensionN)lo=mid;else hi=mid;}
 const wire=make((lo+hi)/2);
 if(Math.abs(wire.tensionN-tensionN)>1e-8)throw Error('tension residual');
 return {...wire,midi,scope:'single layer homogenized winding, axial load and EI core only, diagnostic target not measured',impedanceNsM:Math.sqrt(wire.tensionN*wire.linearDensityKgM)};
}
