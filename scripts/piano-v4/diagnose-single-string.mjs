#!/usr/bin/env node
/** V4 physics-only C4 bench: measurements of mechanics, NOT audio pressure. */
import {writeFile} from 'node:fs/promises';
import {StiffStringHammerV4}
 from '../../research/piano-v4/stiff-string-hammer.mjs';

const results=[];
for(const velocity of [0,.8,1.5,2.5,3.8]){
 const p=new StiffStringHammerV4({hammerInitialVelocityMps:velocity});
 let active=false,firstStart=-1,firstContactMs=0,bridgePeakN=0;
 for(let i=0;i<p.sampleRate*.10;i++){
  bridgePeakN=Math.max(bridgePeakN,Math.abs(p.step()));
  if(p.contactForceN>0&&firstStart<0) {
   firstStart=i;active=true;
  }
  if(active&&p.contactForceN===0){
   firstContactMs=(i-firstStart)*1000/p.sampleRate;
   active=false;
  }
 }
 if(Math.abs(p.relativeEnergyBalance())>1e-8)
  throw new RangeError('nonconservative mechanical model');
 results.push({
  velocityMps:velocity,
  peakFeltContactForceN:p.peakContactForceN,
  firstContactDurationMs:firstContactMs,
  peakFixedBridgeShearN:bridgePeakN,
  initialHammerEnergyJ:p.initialEnergyJ,
  mechanicalEnergyJ:p.totalEnergyJ(),
  cumulativeDissipationJ:p.dissipatedJ,
  energyResidualRelative:p.relativeEnergyBalance()
 });
}
const specimen=new StiffStringHammerV4();
const report={
 project:'Stage Synth piano restart V4.0, independent of E2/E3',
 note:'C4 single steel string; physical geometry illustrative, not measured',
 source:'mechanical equations only, no sample audio or legacy DSP',
 sampleRate:specimen.sampleRate,
 lengthM:specimen.lengthM,radiusM:specimen.radiusM,
 targetFundamentalHz:specimen.targetFundamentalHz,
 tensionN:specimen.tensionN,
 linearDensityKgM:specimen.linearDensityKgM,
 modalMassKg:specimen.modalMassKg,
 inharmonicityB:specimen.inharmonicityB,
 numberOfResolvedModes:specimen.n,
 firstEightModalFrequenciesHz:Array.from(specimen.frequenciesHz.slice(0,8)),
 hammerSpeedTrials:results,
 noBridgeMobilityOrSoundboardYet:true,
 soundRadiationComputed:false,
 validatedAcousticPianoTimbre:false,
 hardwarePolyphonyCertified:false,
 decision:'Mechanical solver passes; NO piano WAV or product integration until auditory gates.'
};
await writeFile('piano-v4-physics-only-c4.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
