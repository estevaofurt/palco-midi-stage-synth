/**
 * Stage Synth — OFFLINE H1 estimator for physically measured bridge FORCE [N]
 * -> bridge VELOCITY [m/s]. NOT part of any synth DSP.
 *
 * Y(f) = S_vF(f) / S_FF(f), coherence = |S_vF|² / (S_FF*S_vv).
 * Spectra use overlapped, detrended Hann-windowed FFTs (Welch averaging).
 * This IS a linear estimate of driving-point mobility v_bridge/F_bridge
 * when probes measure those TWO quantities at the same bridge location.
 * Hammer shank / key-bed force is NOT F_bridge. It is NOT sound bridgeVelocity.
 * Calibration, shared clock, location, sample alignment, permission and
 * provenance must be established by an independent acquisition protocol.
 */
const isFiniteSignal = v => v instanceof Float32Array || v instanceof Float64Array || Array.isArray(v);
const powerOfTwo = n => Number.isInteger(n) && n >= 128 && n <= 16384 && (n & (n - 1)) === 0;

function fft(re, im){
  const n=re.length;
  for(let i=1,j=0;i<n;i++){
    let bit=n>>1;
    for(;j&bit;bit>>=1)j^=bit;
    j^=bit;
    if(i<j){
      [re[i],re[j]]=[re[j],re[i]];
      [im[i],im[j]]=[im[j],im[i]];
    }
  }
  for(let len=2;len<=n;len<<=1){
    const angle=-2*Math.PI/len;
    const wr=Math.cos(angle),wi=Math.sin(angle);
    for(let i=0;i<n;i+=len){
      let pr=1,pi=0;
      for(let j=0;j<len/2;j++){
        const a=i+j,b=a+len/2;
        const tr=pr*re[b]-pi*im[b],ti=pr*im[b]+pi*re[b];
        re[b]=re[a]-tr;im[b]=im[a]-ti;
        re[a]+=tr;im[a]+=ti;
        const next=pr*wr-pi*wi;
        pi=pr*wi+pi*wr;
        pr=next;
      }
    }
  }
}

function windowedSpectrum(signal,start,window,re,im){
  let mean=0;
  const n=window.length;
  for(let i=0;i<n;i++)mean+=signal[start+i];
  mean/=n;
  for(let i=0;i<n;i++){
    re[i]=(signal[start+i]-mean)*window[i];
    im[i]=0;
  }
  fft(re,im);
}

/**
 * Do not call this from the AudioWorklet. Provide arrays from the *same*
 * measured event and sample clock; these conditions cannot be proved by code.
 * Valid bins only are returned as estimates. Low coherence/energy => null H.
 */
export function estimateBridgeMobilityH1({
  bridgeForce,bridgeVelocity,sampleRate,windowSize=1024,hopSize=windowSize/2,
  coherenceThreshold=.85,relativeInputFloor=1e-8
}={}){
  if(!isFiniteSignal(bridgeForce)||!isFiniteSignal(bridgeVelocity)||
     bridgeForce.length!==bridgeVelocity.length)
    throw new TypeError('requires equal-length bridge force and velocity arrays');
  if(!Number.isFinite(sampleRate)||sampleRate<8000||sampleRate>192000)
    throw new RangeError('invalid sample rate');
  if(!powerOfTwo(windowSize))throw new RangeError('windowSize must be power of two 128..16384');
  if(!Number.isInteger(hopSize)||hopSize<1||hopSize>windowSize)
    throw new RangeError('invalid hopSize');
  if(!Number.isFinite(coherenceThreshold)||coherenceThreshold<=0||coherenceThreshold>1)
    throw new RangeError('coherence threshold must be in (0,1]');
  if(!Number.isFinite(relativeInputFloor)||relativeInputFloor<=0||relativeInputFloor>=1)
    throw new RangeError('relativeInputFloor must be in (0,1)');
  const len=bridgeForce.length;
  if(len<windowSize+hopSize*3)
    throw new RangeError('at least four Welch windows required');
  for(let i=0;i<len;i++){
    if(!Number.isFinite(bridgeForce[i])||!Number.isFinite(bridgeVelocity[i]))
      throw new TypeError('non-finite sensor signal');
  }
  const n=windowSize,bins=n/2+1;
  const win=Float64Array.from({length:n},(_,i)=>.5-.5*Math.cos(2*Math.PI*i/n));
  const xr=new Float64Array(n),xi=new Float64Array(n);
  const yr=new Float64Array(n),yi=new Float64Array(n);
  const aa=new Float64Array(bins),pp=new Float64Array(bins);
  const paRe=new Float64Array(bins),paIm=new Float64Array(bins);
  let segments=0;
  for(let start=0;start+n<=len;start+=hopSize){
    windowedSpectrum(bridgeForce,start,win,xr,xi);
    windowedSpectrum(bridgeVelocity,start,win,yr,yi);
    for(let k=0;k<bins;k++){
      aa[k]+=xr[k]*xr[k]+xi[k]*xi[k];
      pp[k]+=yr[k]*yr[k]+yi[k]*yi[k];
      // S_vF = P * conj(A): phase is bridgeVelocity minus bridgeForce.
      paRe[k]+=yr[k]*xr[k]+yi[k]*xi[k];
      paIm[k]+=yi[k]*xr[k]-yr[k]*xi[k];
    }
    segments++;
  }
  let peak=0;
  for(let k=1;k<bins-1;k++)peak=Math.max(peak,aa[k]);
  if(!(peak>0))throw new RangeError('bridge force has no resolvable energy');
  const floor=peak*relativeInputFloor;
  let count=0;
  const spectrum=[];
  for(let k=0;k<bins;k++){
    const power=aa[k],outputPower=pp[k];
    const crossMag2=paRe[k]**2+paIm[k]**2;
    const denominator=power*outputPower;
    const coherence=denominator>0?
      Math.max(0,Math.min(1,crossMag2/denominator)):0;
    // Skip DC/Nyquist; low-excitation or low-coherence bins are NOT data.
    const valid=k>0&&k<bins-1&&power>floor&&outputPower>0&&
      coherence>=coherenceThreshold;
    if(valid)count++;
    const real=valid?paRe[k]/power:null;
    const imag=valid?paIm[k]/power:null;
    spectrum.push({frequencyHz:k*sampleRate/n,
      coherence,valid,
      real,imag,
      magnitude:valid?Math.hypot(real,imag):null,
      phaseRadians:valid?Math.atan2(imag,real):null});
  }
  return {
    method:'Welch H1, bridge velocity/bridge force',
    inputUnit:'N',outputUnit:'m/s',transferUnit:'(m/s)/N',
    sampleRate,windowSize,hopSize,segments,
    frequencyResolutionHz:sampleRate/n,
    validBins:count,eligibleBins:bins-2,
    validFraction:count/(bins-2),
    // Coherence is diagnostic, not evidence of sensor calibration or rights.
    spectrum
  };
}

/**
 * A strict physical-provenance gate, separate from the mathematical estimator.
 * This gate checks metadata declarations only; independent rights/sensor
 * calibration audit must happen before identifying a commercial model.
 */
export function estimateDocumentedBridgeMobility({force,velocity,sampleRate,metadata,...opts}={}){
 if(!metadata||metadata.inputUnit!=='N'||metadata.outputUnit!=='m/s'||
    metadata.transferUnit!=='(m/s)/N'||
    metadata.forceLocation!=='bridge'||
    metadata.velocityLocation!=='same-bridge-point'||
    metadata.synchronized!==true||metadata.calibrated===false||
    metadata.calibrated!==true||
    metadata.sourceType!=='instrumented-bridge-force-velocity'||
    !metadata.sourceId||!metadata.rightsDocumentId||
    metadata.commercialUseAuthorized!==true||
    metadata.sampleRate!==sampleRate)
  throw new RangeError('documented calibrated bridge force and velocity required, not key force or board acoustics');
 return {
  ...estimateBridgeMobilityH1({
   bridgeForce:force,bridgeVelocity:velocity,sampleRate,...opts
  }),
  provenance:{
   sourceId:metadata.sourceId,
   rightsDocumentId:metadata.rightsDocumentId,
   forceLocation:metadata.forceLocation,
   velocityLocation:metadata.velocityLocation,
   metadataOnly:true
  }
 };
}
