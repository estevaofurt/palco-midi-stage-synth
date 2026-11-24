// F10 preparation: isolated bare-steel trichord pitch/length sensitivity, not a piano scale.
// Keep the C4 arithmetic path identical for exact regression.
export const PILOT_NOTES=Object.freeze([55,60,67]);
export function pilotGeometry(midi){
 if(!PILOT_NOTES.includes(midi))throw RangeError('pilot note');
 const ratio=2**((midi-60)/12);
 return {midi,f1Hz:440*2**((midi-69)/12),lengthM:.65/ratio,diameterM:.00096,youngPa:200e9,densityKgM3:7850};
}
export function pilotWire(hp,midi,cents=0){
 const g=pilotGeometry(midi);
 if(!Number.isFinite(cents)||Math.abs(cents)>.5)throw RangeError('unison cents');
 const f1Hz=440*2**(-9/12+cents/1200);
 return hp.makeDesign(hp.solidWire,{lengthM:g.lengthM,diameterM:g.diameterM,youngPa:g.youngPa,densityKgM3:g.densityKgM3,f1Hz:f1Hz*2**((midi-60)/12)});
}
