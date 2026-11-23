/**
 * E3.1 — REJECTED TIMBRE DIAGNOSTIC (research only).
 *
 * Important distinction: point bridge velocity is NOT distributed surface
 * velocity. E2.9/E3.0 erroneously radiated bridge velocity as a large-area
 * symmetric plate shape, while radiating the actual second mechanical panel
 * coordinate as an antisymmetric shape. Changing spatial integration alone
 * cannot repair that physical source misidentification.
 *
 * This runs the existing passive solver without recordings or user data.
 * Acoustic references may be compared OFFLINE, never mixed into synthesis.
 */
import {SharedPassiveModalPiano} from './shared-passive-modal-piano.mjs';
import {AnalyticSoundboardRadiator} from './analytic-soundboard-radiation.mjs';

export function harmonicLevelsDb(signal,sampleRate,frequency,{
 startSeconds=.03,endSeconds=.27,count=8
}={}){
 if(!(signal instanceof Float64Array||signal instanceof Float32Array)||
    !Number.isInteger(sampleRate)||sampleRate<22050||sampleRate>96000||
    !Number.isFinite(frequency)||frequency<=0||frequency*count>=sampleRate*.48||
    !Number.isInteger(count)||count<1||count>16||
    !Number.isFinite(startSeconds)||startSeconds<0||
    !Number.isFinite(endSeconds)||endSeconds<=startSeconds||
    endSeconds*sampleRate>signal.length)
  throw new RangeError('invalid harmonic diagnostic window or frequency');
 const first=Math.floor(startSeconds*sampleRate),
       last=Math.floor(endSeconds*sampleRate),len=last-first;
 const values=[];
 for(let harmonic=1;harmonic<=count;harmonic++){
  let best=0;
  // Search local +-3Hz to include tiny inharmonicity and unison splitting.
  for(const centsHz of [-3,-1.5,0,1.5,3]){
   const f=frequency*harmonic+centsHz,omega=2*Math.PI*f/sampleRate;
   const cosStep=Math.cos(omega),sinStep=Math.sin(omega);
   let cos=1,sin=0,real=0,imag=0;
   for(let i=0;i<len;i++){
    const value=signal[first+i]*(.5-.5*Math.cos(2*Math.PI*i/(len-1)));
    real+=value*cos;imag+=value*sin;
    const nc=cos*cosStep-sin*sinStep;
    sin=sin*cosStep+cos*sinStep;cos=nc;
   }
   best=Math.max(best,Math.hypot(real,imag));
  }
  values.push(best);
 }
 const reference=values[0];
 if(!(reference>1e-18))throw new RangeError('missing measurable fundamental');
 return values.map(value=>20*Math.log10(Math.max(1e-18,value)/reference));
}

export function diagnoseBridgeVsPanel({
 sampleRate=48000,key=48,seconds=.5,columns=8,rows=6
}={}){
 if(!Number.isInteger(key)||key<21||key>108||
    !Number.isFinite(seconds)||seconds<.35||seconds>1)
  throw new RangeError('invalid single-note audit');
 const piano=new SharedPassiveModalPiano({sampleRate});
 const old=new AnalyticSoundboardRadiator({sampleRate,columns,rows});
 const plateOnly=new AnalyticSoundboardRadiator({sampleRate,columns,rows});
 piano.setSustain(127);
 piano.noteOn(key,{velocity:100,peakForce:105,contactMs:3});
 const frames=Math.floor(seconds*sampleRate);
 const observed=new Float64Array(frames),
       correctedSource=new Float64Array(frames);
 let eBridge=0,ePlate=0;
 const from=Math.floor(.03*sampleRate),to=Math.floor(.27*sampleRate);
 for(let i=0;i<frames;i++){
  piano.step();
  old.step(piano.bridgeVelocity,piano.boardPanelVelocity);
  // Bridge is a point force connection; do NOT radiate it as a
  // full distributed surface. The panel coordinate is the only
  // real distributed plate DOF in the 2-DOF E2.3 model.
  plateOnly.step(piano.boardPanelVelocity,0);
  observed[i]=(old.left+old.right)*.5;
  correctedSource[i]=(plateOnly.left+plateOnly.right)*.5;
  if(i>=from&&i<to){
   eBridge+=piano.bridgeVelocity*piano.bridgeVelocity;
   ePlate+=piano.boardPanelVelocity*piano.boardPanelVelocity;
  }
 }
 const fundamental=440*2**((key-69)/12);
 const originalHarmonics=harmonicLevelsDb(observed,sampleRate,fundamental);
 const correctedHarmonics=harmonicLevelsDb(correctedSource,sampleRate,fundamental);
 const ratio=Math.sqrt(ePlate/eBridge);
 return {
  key,connectedKeys:88,stringCoordinates:piano.n,
  fundamentalHz:fundamental,bridgeRmsRelative:Math.sqrt(eBridge/(to-from)),
  panelRmsRelative:Math.sqrt(ePlate/(to-from)),
  panelToBridgeRmsRatio:ratio,
  formerRadiation:'distributed symmetric bridge mode + antisymmetric plate mode',
  physicallyConsistentRadiation:'symmetric plate mode only, no bridge area radiation',
  originalHarmonicsDb:originalHarmonics,
  surfaceOnlyHarmonicsDb:correctedHarmonics,
  originalHigherPartialsMissing:originalHarmonics[4]<-30,
  surfaceOnlyHigherPartialsMissing:correctedHarmonics[4]<-30,
  bridgeAndPanelPhysicallyCalibrated:false,
  truePianoTimbreVerified:false,
  proposedPromotion:false,
  mechanicalRelativeEnergyBalance:piano.energyBalanceError()
 };
}
