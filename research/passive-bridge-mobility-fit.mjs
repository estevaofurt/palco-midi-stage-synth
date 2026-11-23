/**
 * E2.5 research: fit a POSITIVE-REAL passive modal mobility against calibrated
 * bridge driving-point data. No synthetic spectra are admitted as real data.
 *
 * Y(omega) = sum_j weight_j * (i omega) /
 *    (omega_j² - omega² + i 2 damping_j omega_j omega)
 *
 * Each term is the velocity/force transfer of a damped mass-spring mode:
 * weight_j=1/m_j >= 0. Re(Y)>=0 for omega>0 and damping_j>0.
 * This is a driving-point mobility hypothesis, not radiation to Pa.
 *
 * Frequencies and damping are a PREDECLARED candidate grid. Only positive
 * weights are fitted by projected coordinate descent; no negative modes,
 * nonpassive inverse filters, or imagined extra wood partials. Expects
 * independently measured, already authenticated H1 as input. Synthetic
 * fixtures may be used in tests but never claim identified piano parameters.
 */
const TWO_PI=2*Math.PI;
function assertPositive(v,label){if(!Number.isFinite(v)||v<=0)throw new RangeError(label)}
function term(f,mode){
 const w=TWO_PI*f,w0=TWO_PI*mode.frequencyHz;
 const a=w0*w0-w*w,b=2*mode.damping*w0*w;
 const denominator=a*a+b*b;
 return {re:w*b/denominator,im:w*a/denominator};
}
export function passiveModalMobilityAt(frequencyHz,modes){
 assertPositive(frequencyHz,'frequency');
 if(!Array.isArray(modes)||!modes.length||modes.length>12)throw new RangeError('modes');
 let real=0,imag=0;
 for(const m of modes){
  assertPositive(m.frequencyHz,'mode frequency');
  assertPositive(m.damping,'mode damping');
  if(!Number.isFinite(m.weight)||m.weight<0)throw new RangeError('passive weight');
  const t=term(frequencyHz,m);
  real+=m.weight*t.re;
  imag+=m.weight*t.im;
 }
 return {real,imag};
}
function validBins(input,minHz,maxHz){
 if(!input||input.inputUnit!=='N'||input.outputUnit!=='m/s'||
    input.transferUnit!=='(m/s)/N'||!Array.isArray(input.spectrum))
  throw new TypeError('must supply H1 force/velocity bridge spectrum in SI');
 const bins=[];
 for(const point of input.spectrum){
  if(!point.valid||point.frequencyHz<minHz||point.frequencyHz>maxHz)continue;
  if(!Number.isFinite(point.frequencyHz)||!Number.isFinite(point.real)||
     !Number.isFinite(point.imag)||!Number.isFinite(point.coherence)||
     point.coherence<0||point.coherence>1)
   throw new TypeError('invalid finite coherent complex bin');
  bins.push(point);
 }
 return bins;
}
const rms=(observed,pred)=>Math.sqrt(observed.reduce((a,d,i)=>
 a+(d.real-pred[i].real)**2+(d.imag-pred[i].imag)**2,0)/observed.length);
export function fitPassiveBridgeMobility({
 measuredSpectrum,modalGrid,trainBand=[60,1400],validationBand=[1400,2800],
 iterations=280,regularization=1e-10
}={}){
 if(!Array.isArray(modalGrid)||modalGrid.length<1||modalGrid.length>12||
    modalGrid.some(m=>!Number.isFinite(m.frequencyHz)||m.frequencyHz<=0||
                      !Number.isFinite(m.damping)||m.damping<=0))
  throw new RangeError('predeclared passive modal grid required');
 if(!Array.isArray(trainBand)||!Array.isArray(validationBand)||
    trainBand.length!==2||validationBand.length!==2||
    ![...trainBand,...validationBand].every(Number.isFinite)||
    trainBand[0]<=0||trainBand[0]>=trainBand[1]||
    validationBand[0]<=0||validationBand[0]>=validationBand[1]||
    trainBand[1]>validationBand[0]||
    !Number.isInteger(iterations)||iterations<1||iterations>3000||
    !Number.isFinite(regularization)||regularization<0)
  throw new RangeError('train/validation bands must be disjoint with finite limits');
 const train=validBins(measuredSpectrum,...trainBand);
 const holdout=validBins(measuredSpectrum,...validationBand);
 if(train.length<modalGrid.length*3||holdout.length<6)
  throw new RangeError('insufficient independently held-out frequency bins');
 // Column norms prevent parameter scaling from killing coordinate descent.
 const basis=modalGrid.map(mode=>train.map(point=>term(point.frequencyHz,mode)));
 const weights=new Float64Array(modalGrid.length),predicted=train.map(()=>({real:0,imag:0}));
 for(let epoch=0;epoch<iterations;epoch++){
  for(let j=0;j<modalGrid.length;j++){
   const column=basis[j];let numerator=0,denom=regularization;
   for(let i=0;i<train.length;i++){
    const q=column[i],p=predicted[i],y=train[i];
    const residualR=y.real-p.real+weights[j]*q.re;
    const residualI=y.imag-p.imag+weights[j]*q.im;
    numerator+=q.re*residualR+q.im*residualI;
    denom+=q.re*q.re+q.im*q.im;
   }
   if(!(denom>0))throw new RangeError('degenerate passive fit');
   const next=Math.max(0,numerator/denom);
   const delta=next-weights[j];weights[j]=next;
   for(let i=0;i<train.length;i++){
    predicted[i].real+=delta*column[i].re;
    predicted[i].imag+=delta*column[i].im;
   }
  }
 }
 const modes=modalGrid.map((m,j)=>({
  frequencyHz:m.frequencyHz,damping:m.damping,weight:weights[j]
 }));
 const trainRms=rms(train,predicted);
 const holdoutRms=rms(holdout,holdout.map(p=>passiveModalMobilityAt(p.frequencyHz,modes)));
 // Pure research result; never claim fitted data are verified measurements.
 return {
  model:'positive-real damped mobility modes, constrained nonnegative weights',
  units:'(m/s)/N',modes,trainBins:train.length,holdoutBins:holdout.length,
  trainBand,validationBand:holdout.length?validationBand:null,
  trainComplexRms:trainRms,holdoutComplexRms:holdoutRms,
  provenance:measuredSpectrum.provenance||null,
  provenanceExternallyAudited:false,
  extrapolationCertified:false
 };
}
