import {readFileSync} from 'node:fs';
import {solidWire} from '../c3x-physical/c4-wire-consistency.mjs';
import {makeDesign} from './c4-design.mjs';
import {StiffString} from './stiff-string.mjs';
import {modalCoefficients} from './exact-modal.mjs';
import {Trichord,beatPredictions,acousticWindowAudit,truncationStudy} from './trichord.mjs';
const report=JSON.parse(readFileSync(new URL('../c3x-physical/C5_C4_verified_numeric_report.json',import.meta.url),'utf8'));
function checks(helpers,report){
  const make=o=>new Trichord(o,helpers),tri=make(),a=(v,m)=>{if(!v)throw Error(m)},near=(x,y,t)=>Math.abs(x-y)<t;
  const zero=()=>Array.from({length:3},()=>({verticalN:0,horizontalN:0}));
  const reject=fn=>{let b=false;try{fn()}catch(e){b=true}a(b,'expected rejection')};
  const beat=beatPredictions(tri),audit=acousticWindowAudit(report,tri),truncation=truncationStudy(helpers);
  const cases=[
    ['three wires and six transverse banks',()=>a(tri.strings.length===3&&tri.strings.every(s=>s.vertical.modes.length===47&&s.horizontal.modes.length===47),'banks')],
    ['detune changes tension not mass or geometry',()=>{const s=tri.strings;a(s[0].wire.tensionN<s[1].wire.tensionN&&s[1].wire.tensionN<s[2].wire.tensionN&&s.every(v=>v.wire.linearDensityKgM===s[1].wire.linearDensityKgM&&v.wire.EI===s[1].wire.EI),'physical detune')}],
    ['each fundamental matches target cents',()=>a(tri.strings.every(s=>near(1200*Math.log2(s.wire.f1Hz/(440*2**(-9/12))),s.cents,1e-10)),'pitch')],
    ['polarizations have same conservative stiffness and different loss',()=>a(tri.strings.every(s=>s.vertical.modes.every((m,i)=>m.stiffnessNPerM===s.horizontal.modes[i].stiffnessNPerM&&m.sigma>s.horizontal.modes[i].sigma)),'polarizations')],
    ['no artificial excitation across wires or polarizations',()=>{const s=make(),f=zero();f[0].verticalN=.1;for(let i=0;i<100;i++)s.step(f);a(s.strings[0].vertical.energy()>0&&s.strings[0].horizontal.energy()===0&&s.strings.slice(1).every(v=>v.vertical.energy()+v.horizontal.energy()===0),'isolation')}],
    ['horizontal force acts independently',()=>{const s=make(),f=zero();f[1].horizontalN=.1;s.step(f);a(s.supportForce().verticalN===0&&s.strings[1].horizontal.energy()>0,'horizontal')}],
    ['sum of projected work and losses balances energy',()=>{const s=make();for(let i=0;i<480;i++){const f=zero();for(let j=0;j<3;j++){f[j].verticalN=.1*Math.sin(i*.1+j);f[j].horizontalN=.02*Math.cos(i*.07+j);}s.step(f);}const l=s.ledger();a(near(s.energy()+l.lossJ,l.workJ,1e-12)&&l.lossJ>0,'work')}],
    ['free trichord energy decreases',()=>{const s=make();for(const q of s.strings){q.vertical.x[0]=1e-5;q.horizontal.x[1]=2e-6;}let e=s.energy();for(let i=0;i<1000;i++){s.step(zero());const n=s.energy();a(n<=e+1e-14,'passivity');e=n;}}],
    ['unison beating separation grows with partial number',()=>a(beat.slice(1).every((p,i)=>p.outerSpanHz>beat[i].outerSpanHz),'beat')],
    ['two-mode beating identity agrees with simulated displacement',()=>{const s=make({stringOptions:{sigma0PerS:0,sigma2M2PerS:0}}),lo=s.strings[0].vertical,hi=s.strings[2].vertical;lo.x[0]=hi.x[0]=1e-5;const w=zero();for(let i=1;i<=4800;i++){s.step(w);if(i%120===0){const t=i*lo.dt,fa=lo.modes[0].frequencyHz,fb=hi.modes[0].frequencyHz,pred=2e-5*Math.cos(Math.PI*(fb-fa)*t)*Math.cos(Math.PI*(fa+fb)*t);a(near(lo.x[0]+hi.x[0],pred,1e-13),'beating')}}}],
    ['equal tuning has no beat separation',()=>a(beatPredictions(make({detuneCents:[0,0,0]})).every(p=>p.outerSpanHz===0&&p.outerBeatPeriodS===null),'unison')],
    ['acoustic audit excludes low contrast and preserves source identity',()=>{a(audit.excluded.some(p=>p.n===1)&&audit.rows.length>0,'quality');reject(()=>acousticWindowAudit({...report,source_instrument:'Yamaha C3X'},tri));}],
    ['modal cutoff study compares finite errors to a larger fixed-rate basis',()=>a(truncation.every(q=>q.modes<q.referenceModes&&Number.isFinite(q.supportForceRmsRelative)&&q.supportForceRmsRelative>=0&&Number.isFinite(q.displacementRmsRelative)&&q.displacementRmsRelative>=0),'truncation')],
    ['invalid force vector or detune rejected',()=>{reject(()=>make({detuneCents:[0,1]}));reject(()=>tri.step([{verticalN:NaN,horizontalN:0}]));}]
  ];
  for(const [name,fn] of cases){try{fn()}catch(e){throw Error(name+': '+e.message)}}
  return {passed:cases.map(c=>c[0]),strings:tri.strings.map(s=>({cents:s.cents,tension:s.wire.tensionN,f1:s.wire.f1Hz,B:s.wire.B})),totalModes:tri.strings.reduce((n,s)=>n+s.vertical.modes.length+s.horizontal.modes.length,0),beat,audit,truncation};
}
const result=checks({solidWire,makeDesign,StiffString,modalCoefficients},report);for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));
