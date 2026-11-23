import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {ReactiveFeltModalPiano,idealStringModalMassKg}
 from '../research/reactive-felt-modal-piano-e32.mjs';
import {SharedPassiveModalPiano} from '../research/shared-passive-modal-piano.mjs';

function integrate(velocityMps,{sampleRate=48000,seconds=.06,...options}={}){
 const m=new ReactiveFeltModalPiano({
  sampleRate,key:48,velocityMps,...options
 });
 const count=Math.round(sampleRate*seconds);
 for(let i=0;i<count;i++)m.step();
 return m;
}

test('reactive hammer transfers finite energy to the existing 88 connected keys',()=>{
 const m=integrate(2);
 assert.equal(m.piano.n,592);
 assert.equal(m.piano.externalForceMode,true);
 assert.ok(m.maxForce>0,'no positive hammer compression');
 assert.ok(m.contactSamples>0,'never contacted string');
 assert.ok(m.piano.energy()>0,'string+bridge should receive hammer work');
 assert.ok(m.piano.externalWork>0,'positive reciprocal physical contact work');
 assert.ok(m.piano.dissipated>=0,'cannot create negative dissipation');
 assert.ok(Math.abs(m.balanceRelativeError())<1e-6,
  'total hammer+felt+strings energy not balanced: '+m.balanceRelativeError());
});

test('larger initial hammer velocity raises peak felt force',()=>{
 const slow=integrate(1),hard=integrate(3);
 assert.ok(slow.maxForce>0);
 assert.ok(hard.maxForce>slow.maxForce*1.5,
  'nonlinear impact should respond to velocity: '+slow.maxForce+' → '+hard.maxForce);
 assert.ok(Math.abs(slow.balanceRelativeError())<1e-6);
 assert.ok(Math.abs(hard.balanceRelativeError())<1e-6);
});

test('resting hammer with a gap cannot create acoustic or mechanical energy',()=>{
 const m=integrate(0,{seconds:.015});
 assert.equal(m.force,0);
 assert.equal(m.maxForce,0);
 assert.equal(m.contactSamples,0);
 assert.equal(m.piano.energy(),0);
 assert.equal(m.totalMechanicalEnergy(),0);
});

test('two sample rates preserve energy and reactive force dynamics',()=>{
 for(const sampleRate of [44100,96000]){
  const m=integrate(2,{sampleRate,seconds:.04});
  assert.ok(m.maxForce>0);
  assert.ok(m.piano.energy()>0);
  assert.ok(Math.abs(m.balanceRelativeError())<2e-6,
   'energy @ '+sampleRate+' = '+m.balanceRelativeError());
 }
});

test('pedal release and noteOff dissipate rather than inject energy',()=>{
 const m=new ReactiveFeltModalPiano({
  sampleRate:48000,key:48,velocityMps:2,sustain:127
 });
 for(let i=0;i<3600;i++){
  if(i===900)m.noteOff();
  if(i===1300)m.setSustain(0);
  m.step();
 }
 assert.ok(m.maxForce>0);
 assert.ok(m.piano.dissipated>0);
 assert.ok(Math.abs(m.balanceRelativeError())<1e-6);
});

test('reactive contact is deterministic and old prescribed pulse stays isolated',()=>{
 const a=integrate(2,{seconds:.012});
 const b=integrate(2,{seconds:.012});
 assert.equal(a.maxForce,b.maxForce);
 assert.equal(a.piano.energy(),b.piano.energy());
 assert.equal(a.balanceRelativeError(),b.balanceRelativeError());
 const legacy=new SharedPassiveModalPiano();
 legacy.noteOn(48,{velocity:100,peakForce:105,contactMs:3});
 assert.equal(legacy.externalForceMode,false);
 legacy.step();
 assert.ok(legacy.externalWork>0,'legacy sine pulse remains supported');
 const forced=new SharedPassiveModalPiano({externalForceMode:true});
 assert.throws(()=>forced.noteOn(48),RangeError,
  'external-force mode may not combine fixed pulses with reactive impacts');
});

test('reject impossible contact parameters and forbid recorded piano dependencies',()=>{
 for(const args of [
  {key:200},{velocityMps:-1},{hammerGapM:-1},
  {feltStiffness:0},{feltExponent:0},{sampleRate:8000},
  {partialsBass:9},{coupling:-1}
 ])assert.throws(()=>new ReactiveFeltModalPiano(args),RangeError);
 const code=readFileSync(new URL('../research/reactive-felt-modal-piano-e32.mjs',import.meta.url),'utf8');
 assert.doesNotMatch(code,/^import .*(sample-library|sf2-reader|piano-bank|\.wav)/gm);
 assert.doesNotMatch(code,/readFileSync\s*\(|fetch\s*\(|decodeAudioData\s*\(/);
});


test('discrete-gradient force exactly matches bridge-coupled final contact gap',()=>{
 const m=new ReactiveFeltModalPiano({
  sampleRate:48000,key:48,hammerGapM:0,velocityMps:2
 });
 const before=m.predictor(),oldHammerX=m.hammerX;
 m.step();
 const qActual=m.currentStringX();
 const qPredicted=before.qFree+before.compliance*m.force;
 assert.ok(m.force>0);
 assert.ok(Math.abs(qActual-qPredicted)<1e-14,
  'bridge compliance predictor must match integrated motion');
 const oldGap=oldHammerX-before.q0,newGap=m.hammerX-qActual;
 const energyGradient=m.discreteGradient(oldGap,newGap);
 assert.ok(Math.abs(m.force-energyGradient)<1e-9*Math.max(1,m.force),
  'felt contact must equal its potential discrete gradient');
});

test('reactive contact remains passive with an enriched 8x8 string modal bank',()=>{
 const m=integrate(2,{
  seconds:.05,partialsBass:8,partialsTreble:8
 });
 assert.ok(m.piano.n>592);
 assert.ok(m.maxForce>0);
 assert.ok(m.piano.energy()>0);
 assert.ok(Math.abs(m.balanceRelativeError())<1e-6);
});


test('ideal string modal mass is rho * pi * r² * L / 2 and not a timbral preset',()=>{
 const g={lengthM:.85,radiusM:.0006,densityKgM3:7850};
 const expected=7850*Math.PI*.0006**2*.85/2;
 assert.ok(Math.abs(idealStringModalMassKg(g)-expected)<=1e-12*Math.max(1,expected),
  'identical dimensional mass formula must tolerate floating-point reassociation');
 assert.ok(expected>.002&&expected<.006);
 assert.throws(()=>idealStringModalMassKg({...g,radiusM:0}),RangeError);
 assert.throws(()=>idealStringModalMassKg({...g,densityKgM3:-1}),RangeError);
 const legacy=new SharedPassiveModalPiano();
 assert.equal(legacy.uniformModalMassKg,null);
 const dimensional=new SharedPassiveModalPiano({uniformModalMassKg:expected});
 assert.equal(dimensional.mass[0],expected);
 assert.ok(Math.abs(dimensional.ground[0]/dimensional.mass[0]-
              legacy.ground[0]/legacy.mass[0])<1e-10,
  'mass scaling must preserve modal frequencies within floating-point roundoff');
 assert.throws(()=>new SharedPassiveModalPiano({uniformModalMassKg:-1}),RangeError);
});

test('geometry-derived string mass remains mechanically passive with reactive felt',()=>{
 const g={lengthM:.85,radiusM:.0006,densityKgM3:7850};
 const m=integrate(2,{seconds:.05,stringGeometry:g});
 assert.equal(m.localModalMassKg,idealStringModalMassKg(g));
 assert.ok(m.maxForce>0);
 assert.ok(m.piano.energy()>0);
 assert.ok(Math.abs(m.balanceRelativeError())<1e-6,
  'geometry-matched string mass energy residual = '+m.balanceRelativeError());
});
