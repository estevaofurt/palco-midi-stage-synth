#!/usr/bin/env node
/**
 * E3.2 failure-mode diagnostics: compare old programmed impact with reciprocal
 * nonlinear felt-string interaction using *only* mechanically generated data.
 * Not a perceptual test; contact and modal parameters remain illustrative.
 */
import {writeFile} from 'node:fs/promises';
import {SharedPassiveModalPiano} from '../research/shared-passive-modal-piano.mjs';
import {CoupledNonlinearHammerPiano} from '../research/coupled-nonlinear-hammers-e32.mjs';
import {harmonicLevelsDb} from '../research/diagnose-piano-source-e31.mjs';

const rate=48000,frames=Math.round(.42*rate),rows=[];
for(const key of [36,48,60,72]){
 const old=new SharedPassiveModalPiano({sampleRate:rate});
 const nonlinear=new CoupledNonlinearHammerPiano({sampleRate:rate});
 old.setSustain(127);nonlinear.setSustain(127);
 old.noteOn(key,{velocity:95,peakForce:105,contactMs:3});
 nonlinear.noteOn(key,{velocity:95});
 const oldPanel=new Float64Array(frames),newPanel=new Float64Array(frames);
 for(let i=0;i<frames;i++){
  old.step();nonlinear.step();
  oldPanel[i]=old.boardPanelVelocity;
  newPanel[i]=nonlinear.boardPanelVelocity;
 }
 const f0=440*2**((key-69)/12);
 // Each is normalized to its own fundamental: does not compare SPL or velocity.
 const oldH=harmonicLevelsDb(oldPanel,rate,f0,{count:8,startSeconds:.03,endSeconds:.27});
 const newH=harmonicLevelsDb(newPanel,rate,f0,{count:8,startSeconds:.03,endSeconds:.27});
 rows.push({
  key,fundamentalHz:f0,
  obsoletePrescribedHammer:{harmonicsDb:oldH},
  nonlinearReciprocalHammer:{
   harmonicsDb:newH,contactSamples:nonlinear.contactSampleCount,
   maxForceModelUnits:nonlinear.peakForce,
   relativeEnergyBalance:nonlinear.energyBalanceRelativeError()
  },
  conclusion:'This test DOES NOT establish piano timbre, correct radiation or an acoustic improvement.'
 });
}
const audit={
 model:'Stage Synth E3.2 strictly mechanical attack diagnostic',
 source:'no external audio/no prerecorded PCM',
 usingSharedPassive88KeyNetwork:true,
 physicalCalibration:false,
 humanApproval:false,
 results:rows
};
await writeFile('e32-hammer-harmonic-audit.json',
 JSON.stringify(audit,null,2)+'\n');
console.log(JSON.stringify(audit,null,2));
