// F1.9: SI-unit audit of idealized bare homogeneous round wire, offline only. NOT for wound strings or real instrument tuning.
export function solidWire({lengthM,diameterM,tensionN,youngPa,densityKgM3}){
  for(const v of [lengthM,diameterM,tensionN,youngPa,densityKgM3])if(!Number.isFinite(v)||v<=0)throw new RangeError('positive SI parameters required');
  const areaM2=Math.PI*diameterM**2/4, inertiaM4=Math.PI*diameterM**4/64;
  const linearDensityKgM=densityKgM3*areaM2,EI=youngPa*inertiaM4;
  const B=Math.PI**2*EI/(tensionN*lengthM**2);
  const f1Hz=Math.sqrt(tensionN/linearDensityKgM*(1+B))/(2*lengthM);
  const stressPa=tensionN/areaM2;
  if(![areaM2,inertiaM4,linearDensityKgM,EI,B,f1Hz,stressPa].every(v=>Number.isFinite(v)&&v>0))throw new RangeError('numerically invalid');
  return {lengthM,diameterM,tensionN,youngPa,densityKgM3,areaM2,inertiaM4,linearDensityKgM,EI,B,f1Hz,stressPa};
}

export function solveAtLength({lengthM,f1Hz,B,youngPa,densityKgM3}){
  for(const v of [lengthM,f1Hz,B,youngPa,densityKgM3])if(!Number.isFinite(v)||v<=0)throw new RangeError('positive finite inputs required');
  const diameterM=Math.sqrt(64*densityKgM3*lengthM**4*f1Hz**2*B/(Math.PI**2*youngPa*(1+B)));
  const linearDensityKgM=densityKgM3*Math.PI*diameterM**2/4;
  const tensionN=4*lengthM**2*linearDensityKgM*f1Hz**2/(1+B);
  return solidWire({lengthM,diameterM,tensionN,youngPa,densityKgM3});
}

export function auditV10C4(){
  // V10 parameters.py: interpolation at MIDI 60 between 50 and 69.
  const lengthM=.545,diameterM=(1.125+(.95-1.125)*10/19)/1000,tensionN=720+(687-720)*10/19,youngPa=200e9,densityKgM3=7850,f1TargetHz=440*2**(-9/12);
  const base=solidWire({lengthM,diameterM,tensionN,youngPa,densityKgM3});
  const v10Mu=tensionN/(4*lengthM**2*f1TargetHz**2);
  const v10TunedT=tensionN*(1-base.B);
  const v10TunedB=base.B/(1-base.B);
  const actualWireAtTunedT=solidWire({...base,tensionN:v10TunedT});
  const inferredDensity=v10Mu/base.areaM2;
  const tensionForSolidAtTarget=4*lengthM**2*base.linearDensityKgM*f1TargetHz**2-Math.PI**2*base.EI/lengthM**2;
  const solidRetuned=solidWire({...base,tensionN:tensionForSolidAtTarget});
  const Bc5=.00029561290712381465;
  const families=[.45,.50,.545,.60,.65].map(lengthM=>solveAtLength({lengthM,f1Hz:f1TargetHz,B:Bc5,youngPa,densityKgM3}));
  const sameLengthV10B=solveAtLength({lengthM,f1Hz:f1TargetHz,B:v10TunedB,youngPa,densityKgM3});
  return {scope:'hypothetical homogeneous bare steel wire with pinned ends; no real C3X dimensions or safe tension specification',base,v10Mu,v10TunedT,v10TunedB,inferredDensity,massExcessPct:100*(v10Mu/base.linearDensityKgM-1),actualWireAtTunedT,solidRetuned,sameLengthV10B,f1TargetHz,Bc5,families};
}
