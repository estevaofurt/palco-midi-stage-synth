// Original short audition program requested by owner; no audio generated here.
// All keys are present in the research anchors or chromatic midrange.
export const AVAILABLE_NOTES=Object.freeze([36,43,48,...Array.from({length:20},(_,i)=>53+i)]);
const chord=(id,notes,velocity,{arpeggioMs=0,holdMs=2400,tailMs=3000,pedal=false}={})=>{
 const end=arpeggioMs*(notes.length-1)+holdMs;
 const events=notes.map((midi,i)=>({ms:i*arpeggioMs,type:'on',midi,velocity}));
 if(pedal)events.push({ms:0,type:'pedal',value:127});
 for(const midi of notes)events.push({ms:end,type:'off',midi});
 if(pedal)events.push({ms:end+1200,type:'pedal',value:0});
 events.sort((a,b)=>a.ms-b.ms||Number(b.type==='pedal')-Number(a.type==='pedal'));
 return {id,notes,velocity,events,durationMs:end+(pedal?1200:0)+tailMs,requiresSharedBoard:true,requiresPedal:pedal};
};
export function chordProgram(){
 return [
  chord('C-major-open-mf',[48,64,67,72],76),
  chord('A-minor-mf',[57,60,64,69],76),
  chord('G7-open-mf',[43,59,62,65,67],76),
  chord('F-major-pp',[53,57,60,65],24),
  chord('C-major-bass-ff',[36,48,64,67,72],127),
  chord('C-major-arpeggio-mf',[36,43,48,64,67,72],76,{arpeggioMs:150}),
  chord('G7-pedal-mf',[43,59,62,65,67],76,{holdMs:1500,pedal:true}),
 ];
}
export function validateChordProgram(program){
 const ids=new Set;
 for(const c of program){
  if(ids.has(c.id)||!Number.isSafeInteger(c.durationMs)||c.durationMs<=0||c.requiresSharedBoard!==true)throw Error('case');
  ids.add(c.id);let active=new Set,last=-1,pedal=0;const heard=new Set;
  for(const e of c.events){
   if(!Number.isSafeInteger(e.ms)||e.ms<last||e.ms<0||e.ms>=c.durationMs)throw Error('time');last=e.ms;
   if(e.type==='pedal'){if(!c.requiresPedal||![0,127].includes(e.value)||e.value===pedal)throw Error('pedal');pedal=e.value;continue;}
   if(!AVAILABLE_NOTES.includes(e.midi))throw Error('key unavailable');
   if(e.type==='on'){if(active.has(e.midi)||![24,76,127].includes(e.velocity)||e.velocity!==c.velocity)throw Error('note on');active.add(e.midi);heard.add(e.midi);}
   else if(e.type==='off'){if(!active.delete(e.midi))throw Error('orphan off');}
   else throw Error('event');
  }
  if(active.size||pedal||heard.size!==c.notes.length||c.notes.some(m=>!heard.has(m))||c.durationMs-last<1000)throw Error('incomplete sequence');
 }
 return {cases:ids.size,notes:program.reduce((s,c)=>s+c.notes.length,0),requiresSharedBoard:true};
}
