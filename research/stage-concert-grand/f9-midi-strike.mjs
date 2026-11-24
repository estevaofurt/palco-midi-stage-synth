import {hammerSpeed} from './f9-midi-velocity.mjs';
import {renderFeltSensitivity} from './f9-felt-sensitivity.mjs';
// Offline isolated strike only. Note-off must be handled by the future action/damper layer.
export function renderMidiStrike(hp,{midiVelocity,seconds=.1,prior=null}={}){
 const velocity=hammerSpeed(midiVelocity);
 if(velocity===null)throw RangeError('velocity zero is note-off, not a strike');
 if(prior&&prior.midiVelocity!==midiVelocity)throw Error('MIDI checkpoint mismatch');
 const q=renderFeltSensitivity(hp,{seconds,velocity,feltFactor:1.5,prior});
 return {...q,checkpoint:{...q.checkpoint,midiVelocity},meta:{...q.meta,midiVelocity}};
}
