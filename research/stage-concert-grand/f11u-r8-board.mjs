import {bridgePatches,portSummary} from './f11u-r6-geometry.mjs';
import {SharedBoard} from './f9-shared-board.mjs';
import {fastSharedBoard} from './f9-sympathetic-network.mjs';
import {MultiHammerNetwork,SimultaneousHammers} from './f11r-multi-hammer-network.mjs';
import {locateSuspectModes} from './f9-rattle-selective.mjs';
import {modalCoefficients} from './exact-modal.mjs';
import {cholesky} from './radiation-loading.mjs';
import {applyLocalLoss} from './f10c-d-local.mjs';
import {bassCandidate} from './f11c-bass-candidates.mjs';
import {woundWire} from './f11c-wound-wire.mjs';
import {bassWires,BASS_NOTES} from './f11d-bass-render.mjs';
import {scaleWire,SCALE_NOTES} from './f11a-s50-scale.mjs';
import {feltParameters} from './f9-felt-sensitivity.mjs';
import {hammerSpeed} from './f9-midi-velocity.mjs';
import {SUPPORT_VARIANTS} from './f11q-bass-support-trial.mjs';
import {PolyDamperController,viscousMultiDamperStep} from './f11t-poly-damper.mjs';
// First sustained simultaneous chord, no release/pedal/retrigger yet.
// Identical conjugate patch for every note is a deliberate diagnostic geometry,
// matching isolated S50, not a calibrated spatial layout.
export function buildChord(hp,{notes=[48,64,67,72],midiVelocity=76,variant='K750',lossFactor=1,layout='coincident',spread=.5,angle=.5}={}){
 if(!['A','K750','K1000'].includes(variant)||![24,76,127].includes(midiVelocity)||notes.length<1||notes.length>6||new Set(notes).size!==notes.length||notes.some(m=>!BASS_NOTES.includes(m)&&!SCALE_NOTES.includes(m)))throw RangeError('chord scope');
 if(![0,.2,.5].includes(spread)||![.25,.5].includes(angle))throw RangeError('string trial');
 if(![1,1.5,2].includes(lossFactor))throw RangeError('lossFactor');
 const rate=96000,outRate=48000,p=hp.plateDesign(),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>hp.ribDesign(p,{xM})),patch={xM:.83,yM:.46,dxM:.04,dyM:.025};
 const modes=hp.mindlinModes(p,ribs,{basisHz:4000},hp).modes.filter(m=>m.frequencyHz<3000);
 const bridges=notes.map(midi=>{
  const bass=BASS_NOTES.includes(midi),wires=bass?(spread===.5?bassWires(midi,2):[-spread,spread].map(c=>{const w=bassCandidate(midi);return woundWire({...w,f1Hz:w.f1Hz*2**(c/1200)});})): [-spread,0,spread].map(c=>scaleWire(hp,midi,c));
  return new hp.PolarizedBridge(wires,{sampleRate:rate,stiffness:[bass?SUPPORT_VARIANTS[variant]:0,2e6],damping:[0,5],angleRad:angle,verticalLoss:[.1,.0002],horizontalLoss:[.05,.00012]},hp);
 });
 const patches=bridgePatches(notes,layout,p);
 const board=new SharedBoard(p,modes,patches,1/rate,{loss0:3,lossSlope:.00075,radiation:{scale:1}},hp);
 const ids=locateSuspectModes(board.modes),chosen=new Set(ids);
 for(const i of ids){const q=board.modes[i].coeff;board.modes[i].coeff=modalCoefficients({massKg:q.massKg,frequencyHz:q.frequencyHz,dampingNsM:2*(4+.001*2*Math.PI*q.frequencyHz),dt:q.dt});}
 board.blocks=board.blocks.map(b=>{
  if(!b.indices.some(i=>chosen.has(i)))return b;
  const g=b.indices.map(i=>Math.sqrt(board.modes[i].coeff.G));
  return {...b,g,L:cholesky(b.R.map((row,i)=>row.map((v,j)=>+(i===j)+g[i]*v*g[j]/board.h)))};
 });
 const response=board.increment(1,true);board.G=board.modes.reduce((s,m,i)=>s+m.w*response[i],0);
 const local=applyLocalLoss(board,'local8');
 // R5: limited sensitivity trial on mid-register plate modes.
 // Preserve four previously calibrated local8 modes; no string loss changes.
 const excluded=new Set(local.modes.map(m=>m.index)),changed=[];
 for(let i=0;i<board.modes.length;i++){
  const m=board.modes[i],q=m.coeff;
  if(lossFactor===1||excluded.has(i)||m.frequencyHz<250||m.frequencyHz>1000)continue;
  m.coeff=modalCoefficients({massKg:q.massKg,frequencyHz:q.frequencyHz,dampingNsM:q.dampingNsM*lossFactor,dt:q.dt});
  changed.push({i,hz:m.frequencyHz,before:q.dampingNsM,after:m.coeff.dampingNsM});
 }
 const modified=new Set(changed.map(m=>m.i));
 if(changed.length){
  board.blocks=board.blocks.map(b=>{
   if(!b.indices.some(i=>modified.has(i)))return b;
   const g=b.indices.map(i=>Math.sqrt(board.modes[i].coeff.G));
   return {...b,g,L:cholesky(b.R.map((row,i)=>row.map((v,j)=>+(i===j)+g[i]*v*g[j]/board.h)))};
  });
  const response=board.increment(1,true);board.G=board.modes.reduce((s,m,i)=>s+m.w*response[i],0);
 }
 // Rebuild reciprocal multi-port compliance after all modal loss modifications.
 board.responses=board.weights.map((_,j)=>board.incrementPorts(board.weights.map((_,i)=>+(i===j)),true));
 board.portG=board.weights.map(w=>board.responses.map(dx=>w.reduce((s,x,i)=>s+x*dx[i],0)));
 const portStats=portSummary(board.portG);
 const network=new MultiHammerNetwork(bridges,board,notes.map(()=>({k:1e7,c:1})));
 fastSharedBoard(board);
 const hammers=new SimultaneousHammers(network,notes.map(()=>({velocityMps:hammerSpeed(midiVelocity),felt:feltParameters(1.5)})));
 return {p,modes,board,network,hammers,rate,outRate,notes:notes.slice(),midiVelocity,variant,local,changed,patches,portStats,boardSignature:board.modes.map(m=>[m.frequencyHz,m.coeff.dampingNsM])};
}
