import {renderBassPilot,BASS_NOTES} from './f11d-bass-render.mjs';
import {woundWire} from './f11c-wound-wire.mjs';
export const PITCH_VARIANTS=Object.freeze({
 A:Object.freeze({exact:false,massFactor:1}),
 B:Object.freeze({exact:true,massFactor:1}),
 C:Object.freeze({exact:false,massFactor:2}),
 D:Object.freeze({exact:true,massFactor:2})
});
// Only the bass bridge inertial mass and unison spread are varied.
// Two strings remain physical, with the same winding, losses, felt and soundboard.
export function renderBassPitchTrial(hp,{midi=48,midiVelocity=127,seconds=.5,prior=null,variant='A'}={}){
 if(!Object.hasOwn(PITCH_VARIANTS,variant)||!BASS_NOTES.includes(midi))throw RangeError('pitch trial scope');
 if(prior&&prior.pitchVariant!==variant)throw Error('pitch trial checkpoint mismatch');
 const p=PITCH_VARIANTS[variant];let actual=null;
 class TrialBridge extends hp.PolarizedBridge{
  constructor(wires,options,helpers){
   if(wires.length!==2||options.massKg!==undefined)throw Error('unexpected bass bridge');
   const f1Hz=440*2**((midi-69)/12);
   const adjusted=p.exact?wires.map(w=>woundWire({...w,f1Hz})):wires;
   super(adjusted,p.massFactor===1?options:{...options,massKg:.025*p.massFactor},helpers);
   actual={wires:adjusted,bridgeMassKg:.025*p.massFactor};
  }
 }
 const q=renderBassPilot({...hp,PolarizedBridge:TrialBridge},{midi,count:2,midiVelocity,seconds,prior});
 if(!actual)throw Error('trial bridge missing');
 return {...q,checkpoint:{...q.checkpoint,pitchVariant:variant},meta:{...q.meta,wires:actual.wires,pitchVariant:variant,bridgeMassKg:actual.bridgeMassKg,unisonSpreadCents:p.exact?0:.5}};
}
