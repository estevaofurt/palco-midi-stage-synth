// G2.06c: provisional isolated-string hammer profile, not production voicing.
import {HAMMER,HammerPilot} from './g2_hammer_pilot.mjs';
import {pilotCutoffHz,PILOT_KEYS} from './g2_string_pilot.mjs';
export const MASS_KG=Object.freeze({48:.012,60:.010,84:.006});
export function profileFor(key){
 if(!PILOT_KEYS.includes(key))throw RangeError('pilot key');
 return {...HAMMER,massKg:MASS_KG[key]};
}
export function makeProfileHammer(key,sr=48000,{speedMps=1,cutoffHz=pilotCutoffHz(key)}={}){
 return new HammerPilot(key,sr,{speedMps,cutoffHz,params:profileFor(key)});
}
