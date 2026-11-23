#!/usr/bin/env node
/**
 * E3.2: inspect physically reactive hammer energy and uncalibrated spectrum.
 * NO recording is loaded; harmonic measurements use only the simulated
 * second panel DOF, not bridge motion disguised as distributed plate velocity.
 * Do not call this a calibrated piano or release candidate.
 */
import {writeFile} from 'node:fs/promises';
import {ReactiveFeltModalPiano} from '../research/reactive-felt-modal-piano-e32.mjs';
import {harmonicLevelsDb} from '../research/diagnose-piano-source-e31.mjs';

const rate=48000,key=48,seconds=.38;
function inspect({velocityMps=2,partialsBass=5,partialsTreble=2,stringGeometry=null}={}){
 const model=new ReactiveFeltModalPiano({
  sampleRate:rate,key,velocityMps,partialsBass,partialsTreble,stringGeometry
 });
 const samples=Math.round(rate*seconds);
 const panel=new Float64Array(samples);
 let bridgeSum=0,panelSum=0;
 for(let i=0;i<samples;i++){
  panel[i]=model.step();
  if(i>=.03*rate&&i<.27*rate){
   bridgeSum+=model.piano.bridgeVelocity**2;
   panelSum+=panel[i]**2;
  }
 }
 const fundamentalHz=440*2**((key-69)/12);
 const harmonics=harmonicLevelsDb(panel,rate,fundamentalHz,{
  startSeconds:.03,endSeconds:.27,count:8
 });
 return {
  key,velocityMps,partialsBass,partialsTreble,
  localModalMassKg:model.localModalMassKg,
  localStringGeometryIsIllustrative:stringGeometry!==null,
  initialHammerEnergy:model.initialEnergy,
  fractionOfInitialEnergyInStringAndLoss:
   (model.piano.energy()+model.piano.dissipated)/Math.max(model.initialEnergy,1e-12),
  connectedKeys:88,mechanicalCoordinates:model.piano.n+2,
  peakGeneralizedContactForce:model.maxForce,
  summedContactDurationMs:model.contactSamples/rate*1000,
  finalHammerVelocity:model.hammerV,
  stringBoardEnergy:model.piano.energy(),
  accumulatedPassiveDissipation:model.piano.dissipated,
  energyErrorRelative:model.balanceRelativeError(),
  panelToBridgeRmsRatio:Math.sqrt(panelSum/bridgeSum),
  panelOnlyHarmonicsDb: harmonics.map(x=>+x.toFixed(2)),
  physicallyCalibrated:false,
  perceivedPianoTimbreApproved:false
 };
}
const report={
 stage:'E3.2 single reactive nonlinear hammer + 88 coupled modal strings',
 source:'analytic dynamics only; no sample playback, no measured response',
 sampleRate:rate,seconds,key,
 metrics:[
  inspect({velocityMps:1}),
  inspect({velocityMps:2}),
  inspect({velocityMps:3}),
  inspect({velocityMps:2,partialsBass:8,partialsTreble:8}),
  inspect({velocityMps:2,stringGeometry:{lengthM:.85,radiusM:.0006,densityKgM3:7850}}),
  inspect({velocityMps:2,partialsBass:8,partialsTreble:8,
   stringGeometry:{lengthM:.85,radiusM:.0006,densityKgM3:7850}})
 ],
 limitations:[
  'ONE hammer only; 32–64 simultaneously reacting hammer contacts NOT tested',
  'C3 nominal steel-wire length/radius are illustrative and NOT measured',
  'The string/hammer generalized coordinates and all 88 string geometries are not calibrated to SI',
  'Panel has only two generalized modes; panel output is NOT acoustic pressure',
  'Partial amplitude ratios are diagnostic, NOT proof of musical improvement',
  'No recordings entered the physical synthesis'
 ]
};
await writeFile('e32-reactive-hammer-diagnostic.json',
 JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
