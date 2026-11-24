import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {scheduleContinuousV10,DEFAULT_ACTION_V10,validateActionV10,hammerSpeedV10} from './continuous-action-v10.mjs';
const adapter=fileURLToPath(new URL('./reference_action_v10.py',import.meta.url));
function python(payload){
 return JSON.parse(execFileSync('python3',[adapter],{
  input:JSON.stringify(payload),encoding:'utf8',timeout:15000
 }));
}
function parity(payload){
 const input={events:[],length:1,...payload};
 const original=python(input);
 const js=scheduleContinuousV10(input.events,input.length,{
  keyframes:input.keyframes??null,config:input.config??{},
  mode:input.mode??'double',includeTrajectories:input.includeTrajectories??false
 });
 function compare(actual,expected,path='root'){
  if(typeof expected==='number'){
   assert.ok(Math.abs(actual-expected)<1e-8,path+' : '+actual+' != '+expected);
  }else if(Array.isArray(expected)){
   assert.ok(Array.isArray(actual),path+' expected array');
   assert.equal(actual.length,expected.length,path+' length');
   expected.forEach((v,i)=>compare(actual[i],v,path+'['+i+']'));
  }else if(expected&&typeof expected==='object'){
   assert.deepEqual(Object.keys(actual).sort(),Object.keys(expected).sort(),path+' keys');
   for(const key of Object.keys(expected))compare(actual[key],expected[key],path+'.'+key);
  }else assert.equal(actual,expected,path);
 }
 compare(js,original);
 return js;
}
test('original C3X V10 Python scheduling model is accessible',()=>{
 assert.equal(DEFAULT_ACTION_V10.simulation_hz,2000);
 assert.equal(DEFAULT_ACTION_V10.escapement_key_fraction,.82);
 assert.ok(hammerSpeedV10(100)>hammerSpeedV10(30));
 assert.throws(()=>validateActionV10({simulation_hz:10}),RangeError);
});
test('V10 Python to JS parity: individual and multiple MIDI strikes',()=>{
 for(const input of [
  {events:[[.05,69,.2,85]],length:.7},
  {events:[[.04,60,.22,80],[.26,60,.21,100]],length:1},
  {events:[[.02,60,.3,25],[.02,64,.31,75],[.02,67,.37,120]],length:.8},
  {events:[[.1,69,.3,20],[.1,69,.3,127]],length:.8},
  {events:[[.02,21,.23,45],[.08,108,.32,125]],length:.9}
 ])parity(input);
});
test('V10 Python to JS parity: half-release and double vs single repetition',()=>{
 const keys=[
  [.02,69,1,90],[.12,69,.45,0],[.16,69,1,99],
  [.26,69,.45,0],[.30,69,1,105],[.40,69,0,0]
 ];
 const d=parity({keyframes:keys,length:1,mode:'double',includeTrajectories:true});
 const s=parity({keyframes:keys,length:1,mode:'single'});
 assert.equal(d.diagnostics.strike_count,3);
 assert.equal(s.diagnostics.strike_count,1);
 assert.ok(d.diagnostics.key_trajectories[69].length>40);
});
test('V10 Python to JS parity: shallow, blocked and released actions',()=>{
 const shallow=parity({keyframes:[[.1,69,.5,90],[.3,69,0,0]],length:1});
 assert.equal(shallow.diagnostics.strike_count,0);
 const blocked=parity({
  keyframes:[[.02,69,1,93],[.15,69,.70,0],[.19,69,1,110],[.3,69,0,0]],
  length:1
 });
 assert.equal(blocked.diagnostics.strike_count,1);
 assert.ok(blocked.diagnostics.blocked_count>=1);
});
test('V10 Python to JS parity: action timebase and experimental parameters',()=>{
 for(const hz of [500,1000,2000,4000]){
  parity({events:[[.03,65,.3,85]],length:.7,config:{simulation_hz:hz}});
 }
 parity({keyframes:[
  [.014,57,1,95],[.104,57,0,0],[.24,57,1,116],[.39,57,.2,0]
 ],length:.85,config:{escapement_key_fraction:.79,damper_release_fraction:.2}});
});
