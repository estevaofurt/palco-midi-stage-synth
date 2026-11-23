import test from 'node:test';
import assert from 'node:assert/strict';
import {passiveModalMobilityAt,fitPassiveBridgeMobility}
 from '../research/passive-bridge-mobility-fit.mjs';
const modes=[
 {frequencyHz:120,damping:.09,weight:.45},
 {frequencyHz:320,damping:.06,weight:.2},
 {frequencyHz:760,damping:.08,weight:.15}
];
function syntheticH1({corruptHoldout=false}={}){
 const spectrum=[];
 for(let k=1;k<=100;k++){
  const f=k*30;const y=passiveModalMobilityAt(f,modes);
  spectrum.push({frequencyHz:f,real:y.real,imag:y.imag,
   coherence:.999,valid:true});
 }
 if(corruptHoldout)for(const p of spectrum)
  if(p.frequencyHz>=1500){p.real+=.003;p.imag-=.002;}
 return {inputUnit:'N',outputUnit:'m/s',transferUnit:'(m/s)/N',
  spectrum,provenance:{sourceId:'SYNTHETIC-MATH-ONLY'}};
}
const grid=modes.map(({frequencyHz,damping})=>({frequencyHz,damping}));
test('positive-real mechanical mobility never has negative dissipative real part',()=>{
 for(const f of [30,70,120,220,320,700,760,1500,2900]){
  const y=passiveModalMobilityAt(f,modes);
  assert.ok(y.real>=0&&Number.isFinite(y.imag));
 }
 assert.throws(()=>passiveModalMobilityAt(120,[{frequencyHz:120,damping:.04,weight:-1}]),RangeError);
});
test('training identifies known positive modal weights from synthetic complex Y',()=>{
 const fit=fitPassiveBridgeMobility({
  measuredSpectrum:syntheticH1(),modalGrid:grid,
  trainBand:[60,1200],validationBand:[1500,2700],iterations:500
 });
 assert.ok(fit.trainBins>=30&&fit.holdoutBins>=30);
 for(let j=0;j<grid.length;j++){
  assert.ok(fit.modes[j].weight>=0);
  assert.ok(Math.abs(fit.modes[j].weight-modes[j].weight)<.001,
   'weight j='+j+' '+fit.modes[j].weight);
 }
 assert.ok(fit.trainComplexRms<1e-6);
 assert.ok(fit.holdoutComplexRms<1e-6);
 assert.equal(fit.provenanceExternallyAudited,false);
});
test('held-out band reveals model failure even when training band is unchanged',()=>{
 const good=fitPassiveBridgeMobility({
  measuredSpectrum:syntheticH1(),modalGrid:grid,
  trainBand:[60,1200],validationBand:[1500,2700],iterations:400
 });
 const corrupted=fitPassiveBridgeMobility({
  measuredSpectrum:syntheticH1({corruptHoldout:true}),modalGrid:grid,
  trainBand:[60,1200],validationBand:[1500,2700],iterations:400
 });
 assert.ok(Math.abs(good.trainComplexRms-corrupted.trainComplexRms)<1e-15);
 assert.ok(corrupted.holdoutComplexRms>good.holdoutComplexRms+.002);
});
test('wrong modes stay nonnegative even with bad frequency targets',()=>{
 const fit=fitPassiveBridgeMobility({
  measuredSpectrum:syntheticH1(),
  modalGrid:[{frequencyHz:100,damping:.3},{frequencyHz:550,damping:.1}],
  trainBand:[60,1200],validationBand:[1500,2700]
 });
 assert.ok(fit.modes.every(m=>m.weight>=0));
 assert.ok(fit.holdoutComplexRms>1e-6);
});
test('reject overlapping training/validation, weak data and false units',()=>{
 const x=syntheticH1();
 assert.throws(()=>fitPassiveBridgeMobility({
  measuredSpectrum:x,modalGrid:grid,trainBand:[100,1700],validationBand:[1600,2500]
 }),RangeError);
 assert.throws(()=>fitPassiveBridgeMobility({
  measuredSpectrum:x,modalGrid:[{frequencyHz:120,damping:-1}]
 }),RangeError);
 assert.throws(()=>fitPassiveBridgeMobility({
  measuredSpectrum:{...x,inputUnit:'key-bed-force'},modalGrid:grid
 }),TypeError);
 assert.throws(()=>fitPassiveBridgeMobility({
  measuredSpectrum:{...x,spectrum:x.spectrum.map(p=>({...p,valid:false}))},
  modalGrid:grid
 }),RangeError);
});
