import {chordProgram,validateChordProgram} from './f11p-chord-program.mjs';
let n=0;const check=(m,b)=>{if(!b)throw Error(m);n++},rejects=f=>{try{f();return false}catch{return true}};
const p=chordProgram(),r=validateChordProgram(p);
check('seven original cases',r.cases===7);
check('all three dynamics',new Set(p.map(c=>c.velocity)).size===3);
check('six-note arpeggio',p.some(c=>c.notes.length===6&&c.events[1].ms>0));
check('pedal release',p.some(c=>c.requiresPedal&&c.events.some(e=>e.type==='pedal'&&e.value===0)));
check('shared board required',r.requiresSharedBoard);
check('deterministic',JSON.stringify(p)===JSON.stringify(chordProgram()));
for(const [name,edit] of [['missing off',q=>q[0].events.pop()],['unavailable note',q=>q[0].events[0].midi=21],['unreleased pedal',q=>q[6].events.pop()],['duplicate id',q=>q.push(q[0])],['wrong timing',q=>q[0].events[1].ms=-1]]){
 const q=chordProgram();edit(q);check(name,rejects(()=>validateChordProgram(q)));
}
console.log('F11P_CHORD_PROGRAM_TESTS '+n);
