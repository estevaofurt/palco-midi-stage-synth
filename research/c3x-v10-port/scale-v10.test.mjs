import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {c3xV10NoteParams,c3xV10TuneNote,c3xV10Partials,v10StretchAnchors,
 v10TuningCents,pianoMidiHz} from './scale-v10.mjs';

const ref=fileURLToPath(new URL('./reference_scale_v10.py',import.meta.url));
const src=JSON.parse(execFileSync('python3',[ref],{
 input:JSON.stringify({notes:Array.from({length:88},(_,i)=>i+21)}),
 encoding:'utf8',timeout:15000
}));
function equivalent(actual,expected,path){
 if(typeof expected==='number'){
  const tol=2e-11*Math.max(1,Math.abs(expected));
  assert.ok(Number.isFinite(actual)&&Math.abs(actual-expected)<tol,
   path+' JS '+actual+' vs V10 Python '+expected+' tolerance '+tol);
 }else if(Array.isArray(expected)){
  assert.equal(actual.length,expected.length,path+' length');
  expected.forEach((v,i)=>equivalent(actual[i],v,path+'['+i+']'));
 }else if(expected&&typeof expected==='object'){
  assert.deepEqual(Object.keys(actual).sort(),Object.keys(expected).sort(),path+' keys');
  for(const [key,value] of Object.entries(expected))
   equivalent(actual[key],value,path+'.'+key);
 }else assert.equal(actual,expected,path);
}
test('Yamaha C3X V10 scale and tuning all 88 keys match ORIGINAL Python',()=>{
 assert.equal(src.notes.length,88);
 for(let i=0;i<88;i++){
  const midi=i+21,record=src.notes[i];
  equivalent(c3xV10NoteParams(midi),record.params,'note '+midi);
  for(const [profile,data] of Object.entries(record.profiles)){
   equivalent(c3xV10TuneNote(midi,profile),data.tuning,'tuning '+midi+' '+profile);
   equivalent(c3xV10Partials(midi,profile,12),data.partials,'partials '+midi+' '+profile);
   equivalent(v10TuningCents(midi,profile),data.cents,'cents '+midi+' '+profile);
  }
 }
 equivalent(v10StretchAnchors(),src.anchors,'stretch anchors');
});
test('88-key range, A4 440Hz and tuning safety',()=>{
 assert.equal(pianoMidiHz(69),440);
 assert.throws(()=>c3xV10NoteParams(20),RangeError);
 assert.throws(()=>c3xV10NoteParams(109),RangeError);
 assert.throws(()=>c3xV10TuneNote(69,'unknown'),RangeError);
 assert.equal(c3xV10Partials(69,'equal',12).length,12);
 assert.ok(c3xV10NoteParams(21).inarmonicidade_b>0);
});
test('estimated wound / unison / discontinuous bridge model is retained',()=>{
 const a=c3xV10NoteParams(46),b=c3xV10NoteParams(47);
 assert.ok(b.comprimento_vibrante_m>a.comprimento_vibrante_m);
 assert.equal(c3xV10NoteParams(21).cordas_por_nota,1);
 assert.equal(c3xV10NoteParams(40).cordas_por_nota,2);
 assert.equal(c3xV10NoteParams(60).cordas_por_nota,3);
 assert.equal(c3xV10NoteParams(50).corda_enrolada,false);
});
