// F1.10: offline uncertainty and identifiability; bounded illustrative inputs, not real instrument measurements.
export function logSensitivities(B){
  if(!Number.isFinite(B)||B<0)throw new RangeError('B');
  const q=B/(1+B);
  return {lengthM:{f1:-1-q,B:-2},diameterM:{f1:-1+2*q,B:4},tensionN:{f1:(1-q)/2,B:-1},youngPa:{f1:q/2,B:1},densityKgM3:{f1:-.5,B:0}};
}

export function corners(base,bounds,evaluate,outputs){
  const keys=Object.keys(bounds);
  if(keys.length<1||keys.length>10)throw new RangeError('bounds');
  for(const k of keys)if(!Number.isFinite(base[k])||!Number.isFinite(bounds[k])||bounds[k]<0||base[k]-bounds[k]<=0)throw new RangeError('invalid bound '+k);
  const extrema=Object.fromEntries(outputs.map(k=>[k,{min:Infinity,max:-Infinity}]));
  for(let mask=0;mask<2**keys.length;mask++){
    const p={...base};keys.forEach((k,i)=>p[k]+=(mask&(1<<i)?1:-1)*bounds[k]);
    const x=evaluate(p);
    for(const k of outputs){if(!Number.isFinite(x[k]))throw new RangeError('invalid result');extrema[k].min=Math.min(extrema[k].min,x[k]);extrema[k].max=Math.max(extrema[k].max,x[k]);}
  }
  return extrema;
}

export function inverseFromGeometry({lengthM,diameterM,densityKgM3,f1Hz,B}){
  for(const v of [lengthM,diameterM,densityKgM3,f1Hz,B])if(!Number.isFinite(v)||v<=0)throw new RangeError('positive measured or assumed inputs required');
  const area=Math.PI*diameterM**2/4,I=Math.PI*diameterM**4/64;
  const tensionN=4*lengthM**2*densityKgM3*area*f1Hz**2/(1+B);
  const youngPa=B*tensionN*lengthM**2/(Math.PI**2*I);
  if(![tensionN,youngPa].every(v=>Number.isFinite(v)&&v>0))throw new RangeError('invalid result');
  return {tensionN,youngPa};
}

export function analyzeUncertainty(solidWire,auditV10C4){
  const baseline=auditV10C4().solidRetuned;
  const b=baseline.B,s=logSensitivities(b);
  const bounds={lengthM:.0005,diameterM:.000005,tensionN:baseline.tensionN*.01,youngPa:baseline.youngPa*.05,densityKgM3:baseline.densityKgM3*.01};
  const individual=Object.keys(bounds).map(k=>{
    const e=corners(baseline,{[k]:bounds[k]},solidWire,['f1Hz','B']);
    return {parameter:k,relativeBoundPct:100*bounds[k]/baseline[k],frequencyCents:[1200*Math.log2(e.f1Hz.min/baseline.f1Hz),1200*Math.log2(e.f1Hz.max/baseline.f1Hz)],BChangePct:[100*(e.B.min/b-1),100*(e.B.max/b-1)]};
  });
  const forward=corners(baseline,bounds,solidWire,['f1Hz','B']);
  const inverseBounds={lengthM:bounds.lengthM,diameterM:bounds.diameterM,densityKgM3:bounds.densityKgM3,f1Hz:.1,B:b*.05};
  const inverse=corners(baseline,inverseBounds,inverseFromGeometry,['tensionN','youngPa']);
  return {scope:'illustrative bounded errors, not sensor uncertainty or C3X acceptance',baseline,sensitivities:s,bounds,individual,forward,forwardCents:[1200*Math.log2(forward.f1Hz.min/baseline.f1Hz),1200*Math.log2(forward.f1Hz.max/baseline.f1Hz)],forwardBChangePct:[100*(forward.B.min/b-1),100*(forward.B.max/b-1)],inverseBounds,inverse,inverseRelativePct:{tensionN:[100*(inverse.tensionN.min/baseline.tensionN-1),100*(inverse.tensionN.max/baseline.tensionN-1)],youngPa:[100*(inverse.youngPa.min/baseline.youngPa-1),100*(inverse.youngPa.max/baseline.youngPa-1)]}};
}
