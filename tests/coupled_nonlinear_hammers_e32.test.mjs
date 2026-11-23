import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {CoupledNonlinearHammerPiano,contactDiscreteGradient}
 from '../research/coupled-nonlinear-hammers-e32.mjs';
import {SharedPassiveModalPiano} from '../research/shared-passive-modal-piano.mjs';

function run(velocity,rate=48000,samples=2500,options={}){
 const piano=new CoupledNonlinearHammerPiano({sampleRate:rate,...options});
 piano.noteOn(48,{velocity});
 for(let i=0;i<samples;i++)piano.step();
 return piano;
}
test('opt-in external modal forces preserve the prior scheduled research solver',()=>{
 const scheduled=new SharedPassiveModalPiano();
 const external=new SharedPassiveModalPiano({externalForceMode:true});
 assert.equal(scheduled.externalForceMode,false);
 assert.equal(external.externalForceMode,true);
 assert.throws(()=>external.noteOn(48),RangeError);
 assert.equal(external.step(),0);
 assert.equal(external.energy(),0);
 const baseline=new SharedPassiveModalPiano();
 baseline.noteOn(48,{velocity:90});
 let peak=0;for(let i=0;i<750;i++)peak=Math.max(peak,Math.abs(baseline.step()));
 assert.ok(peak>0);
});
test('felt discrete gradient never attracts a separated string',()=>{
 const k=1e10,p=2.3;
 assert.equal(contactDiscreteGradient(-.0001,-.00005,k,p),0);
 assert.ok(contactDiscreteGradient(-.00001,.00002,k,p)>0);
 assert.ok(contactDiscreteGradient(.00002,.00004,k,p)>0);
 assert.throws(()=>contactDiscreteGradient(NaN,0,k,p),RangeError);
});
test('hammer cannot produce sounds from no MIDI input',()=>{
 const instrument=new CoupledNonlinearHammerPiano();
 for(let i=0;i<1000;i++)assert.equal(instrument.step(),0);
 assert.equal(instrument.totalEnergy(),0);
 assert.equal(instrument.energyBalanceError(),0);
 assert.equal(instrument.piano.externalWork,0);
});
test('physical felt hammer and 592 string modes exchange reciprocal energy',()=>{
 const piano=run(95,48000,2500);
 assert.equal(piano.piano.n,592);
 assert.equal(piano.piano.externalForceMode,true);
 assert.ok(piano.peakForce>0,'actual nonlinear contact must occur');
 assert.ok(piano.contactSampleCount>0);
 assert.ok(piano.piano.energy()>0,'hammer has excited the passive string bank');
 assert.ok(piano.piano.dissipated>0);
 assert.ok(Math.abs(piano.energyBalanceRelativeError())<2e-6,
  'complete mechanical hammer + string + felt energy audit '+piano.energyBalanceRelativeError());
});
test('higher strike velocity transfers greater vibrational energy and peak force',()=>{
 const slow=run(55,48000,1800),fast=run(115,48000,1800);
 assert.ok(fast.peakForce>slow.peakForce);
 assert.ok(fast.piano.energy()>slow.piano.energy());
});
test('CC64 damping and noteOff change the coupled mechanical decay',()=>{
 const sustain=new CoupledNonlinearHammerPiano();
 const release=new CoupledNonlinearHammerPiano();
 for(const m of [sustain,release]){
  m.noteOn(48,{velocity:100});
  for(let i=0;i<1800;i++)m.step();
  m.noteOff(48);
 }
 sustain.setSustain(127);
 for(let i=0;i<2200;i++){sustain.step();release.step()}
 assert.ok(sustain.piano.energy()>release.piano.energy(),
  'open string with CC64 should sustain more energy than released damper');
 assert.ok(Math.abs(sustain.energyBalanceRelativeError())<2e-6);
 assert.ok(Math.abs(release.energyBalanceRelativeError())<2e-6);
});
test('simultaneous physical contacts are stable and conserve energy',()=>{
 for(const notes of [2,8,32,48,64]){
  const instrument=new CoupledNonlinearHammerPiano({maxHammers:64});
  for(let k=0;k<notes;k++)instrument.noteOn(k+21,{velocity:80+(k%12)});
  for(let i=0;i<180;i++){
   instrument.step();
   assert.ok(Number.isFinite(instrument.boardPanelVelocity));
  }
  assert.ok(instrument.contactSampleCount>0);
  assert.ok(instrument.peakForce>0);
  assert.ok(Math.abs(instrument.energyBalanceRelativeError())<2e-5,
   'energy leak for '+notes+' hammers: '+instrument.energyBalanceRelativeError());
 }
});
test('re-strike is explicit external kinetic input, never canned piano WAV',()=>{
 const p=run(85,48000,1400);
 const before=p.launchWork;
 p.noteOn(48,{velocity:100});
 assert.ok(p.launchWork>before);
 for(let i=0;i<1400;i++)p.step();
 assert.ok(Math.abs(p.energyBalanceRelativeError())<2e-5);
});
test('invalid hammer settings and notes are rejected',()=>{
 assert.throws(()=>new CoupledNonlinearHammerPiano({feltExponent:0}),RangeError);
 assert.throws(()=>new CoupledNonlinearHammerPiano({hammerMass:0}),RangeError);
 assert.throws(()=>new CoupledNonlinearHammerPiano({maxHammers:0}),RangeError);
 const p=new CoupledNonlinearHammerPiano({maxHammers:1});
 assert.throws(()=>p.noteOn(150),RangeError);
 assert.throws(()=>p.noteOn(36,{velocity:0}),RangeError);
 p.noteOn(36);assert.throws(()=>p.noteOn(37),RangeError);
});
test('E3.2 does not load recorded samples or pretend audible fidelity',()=>{
 const source=readFileSync(new URL('../research/coupled-nonlinear-hammers-e32.mjs',import.meta.url),'utf8');
 assert.doesNotMatch(source,/^import .*(sample-library|piano-bank|sf2-reader|measured-radiation-adapter|\.wav)/gm);
 assert.match(source,/NOT Stage-D public DSP/);
});
