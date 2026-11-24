/**
 * Direct port of V10 Python note_params and tuning.py (offline research).
 * References:
 *  research/c3x-python/v10/stage_synth_c3x/parameters.py
 *  research/c3x-python/v10/stage_synth_c3x/tuning.py
 * All string/hammer geometry, lengths and tensions are ESTIMATES:
 * these are not manufacturer-measured Yamaha C3X specifications.
 * No sample audio. Frequencies remain calibrated to A4=440 (equal mode).
 */
const E=200e9;
const NOTE_NAMES=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
const interpolation=(note,table)=>{
 const anchors=Object.keys(table).map(Number).sort((a,b)=>a-b);
 if(note<=anchors[0])return table[anchors[0]];
 if(note>=anchors[anchors.length-1])return table[anchors[anchors.length-1]];
 for(let i=1;i<anchors.length;i++){
  const hi=anchors[i],lo=anchors[i-1];
  if(note<=hi)return table[lo]+(note-lo)/(hi-lo)*(table[hi]-table[lo]);
 }
 throw RangeError('no anchors');
};
const logInterp=(note,table)=>Math.exp(
 interpolation(note,Object.fromEntries(Object.entries(table).map(([k,v])=>[k,Math.log(v)]))));
export const pianoMidiHz=midi=>440*2**((midi-69)/12);
export function c3xV10NoteParams(midi){
 if(!Number.isInteger(midi)||midi<21||midi>108)
  throw RangeError('C3X 88 keys only: MIDI21–108');
 const f=pianoMidiHz(midi);
 let L;
 if(midi<=46)L=logInterp(midi,{21:1.36,33:1.10,45:.86,46:.83});
 else if(midi<=49)L=logInterp(midi,{47:1.03,49:.985});
 else L=logInterp(midi,{50:.963,57:.620,60:.545,69:.399,81:.208,93:.105,108:.05});
 const T=interpolation(midi,{21:1300,32:1050,46:675,47:790,49:760,50:720,69:687,81:672,108:650});
 const d=interpolation(midi,{21:1.5,33:1.18,46:.95,47:.98,49:.97,50:1.125,69:.95,81:.9,108:.78});
 const mu=T/(4*L*L*f*f);
 const B=Math.PI**3*E*(d/1000)**4/(64*T*L*L);
 return {
  midi,nota:NOTE_NAMES[midi%12]+(Math.floor(midi/12)-1),
  frequencia_hz:f,cordas_por_nota:midi<=32?1:midi<=49?2:3,
  corda_enrolada:midi<=49,comprimento_vibrante_m:L,
  tensao_por_corda_n:T,diametro_nucleo_aco_mm:d,
  densidade_linear_kg_m:mu,inarmonicidade_b:B,
  massa_martelo_kg:interpolation(midi,{21:.014,45:.012,69:.009,108:.005}),
  rigidez_feltro_k:logInterp(midi,{21:7e8,49:1.5e10,69:2e10,108:3e11}),
  expoente_feltro_p:interpolation(midi,{21:2.2,69:2.8,108:3.5}),
  posicao_impacto_fracao:interpolation(midi,{21:.14,69:.125,108:.105})
 };
}
export function v10OctaveMatchCents(lower,lowerPartial,upperPartial){
 if(lowerPartial!==2*upperPartial)throw RangeError('2k:k octave relation required');
 const b0=c3xV10NoteParams(lower).inarmonicidade_b;
 const b1=c3xV10NoteParams(lower+12).inarmonicidade_b;
 const r=Math.sqrt((1+b0*lowerPartial**2)/(1+b0))/
         Math.sqrt((1+b1*upperPartial**2)/(1+b1));
 return 1200*Math.log2(r);
}
export function v10StretchAnchors(){
 const a={69:0};
 for(const lo of [57,45,33,21]){
  const pair=lo===57?[4,2]:[6,3];
  a[lo]=a[lo+12]-v10OctaveMatchCents(lo,...pair);
 }
 for(const lo of [69,81,93]){
  const pair=lo===69?[4,2]:[2,1];
  a[lo+12]=a[lo]+v10OctaveMatchCents(lo,...pair);
 }
 return a;
}
export function v10TuningCents(midi,profile='equal'){
 if(!Number.isInteger(midi)||midi<21||midi>108)throw RangeError('MIDI range 21–108');
 if(profile==='equal')return 0;
 if(profile!=='stretch_experimental')throw RangeError('Unknown stretch profile');
 const anchors=v10StretchAnchors();
 if(midi>105)return anchors[105]+(midi-105)*(anchors[105]-anchors[93])/12;
 return interpolation(midi,anchors);
}
export function c3xV10TuneNote(midi,profile='equal'){
 const p=c3xV10NoteParams(midi),cents=v10TuningCents(midi,profile);
 const r=2**(cents/1200),ratio=r*r-p.inarmonicidade_b;
 if(ratio<=0)throw RangeError('Tuning incompatible with string stiffness');
 const T=p.tensao_por_corda_n*ratio,B=p.inarmonicidade_b/ratio;
 const ideal=1/(2*p.comprimento_vibrante_m)*Math.sqrt(T/p.densidade_linear_kg_m);
 const fundamental=ideal*Math.sqrt(1+B);
 const target=p.frequencia_hz*r;
 if(Math.abs(fundamental-target)>1e-10*Math.max(1,Math.abs(target)))
  throw Error('C3X physics tuning inconsistency');
 return {
  midi,profile,target_hz:target,cents,tension_newton:T,
  inharmonicity_b:B,ideal_fundamental_hz:ideal
 };
}
export function c3xV10Partials(midi,profile='equal',max=40){
 if(!Number.isInteger(max)||max<1||max>100)throw RangeError('partials count');
 const tuned=c3xV10TuneNote(midi,profile);
 const B=tuned.inharmonicity_b;
 return Array.from({length:max},(_,index)=>{
  const n=index+1;
  return n*tuned.target_hz*Math.sqrt((1+B*n*n)/(1+B));
 });
}
