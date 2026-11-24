// F1.7: independent unweighted linear fit of (f_n/n)^2 vs n^2, using archived pressure peaks. No audio/DSP integration.
export function fitStiffString(peaks) {
  if(!Array.isArray(peaks)||peaks.length<4) throw new RangeError('at least four distinct partials required');
  const seen=new Set();
  const p=peaks.map(({n,freq_hz:f})=>{
    if(!Number.isInteger(n)||n<1||n>64||seen.has(n)||!Number.isFinite(f)||f<=0)throw new RangeError('invalid partial');
    seen.add(n);return {n,f,x:n*n,y:(f/n)**2};
  });
  const mean=(arr)=>arr.reduce((a,b)=>a+b,0)/arr.length;
  const mx=mean(p.map(v=>v.x)),my=mean(p.map(v=>v.y));
  const den=p.reduce((s,v)=>s+(v.x-mx)**2,0);
  const slope=p.reduce((s,v)=>s+(v.x-mx)*(v.y-my),0)/den;
  const intercept=my-slope*mx;
  const B=slope/intercept;
  if(!Number.isFinite(B)||B<0||intercept<=0)throw new RangeError('nonphysical fit');
  const idealHz=Math.sqrt(intercept), f1Hz=idealHz*Math.sqrt(1+B);
  const residualHzRms=Math.sqrt(mean(p.map(v=>(v.f-v.n*idealHz*Math.sqrt(1+B*v.n*v.n))**2)));
  if(![idealHz,f1Hz,residualHzRms].every(Number.isFinite))throw new RangeError('nonfinite fit');
  return {B,idealHz,f1Hz,residualHzRms,partials:p.map(v=>v.n)};
}
export function auditC5Report(report) {
  if(report.source_instrument!=='Yamaha C5, not Yamaha C3X'||report.reference_note!=='C4 MIDI60'||report.commercial_c3x_calibration_approved!==false)throw new Error('unexpected source identity');
  const windows=['attack_35_255ms','body_260_700ms','tail_900_1400ms'];
  const results=[];
  for(const layer of ['v1','v8','v16']){
    const entry=report.layers[layer];
    if(entry.not_a_measurement_of_C3X!==true||!(/^[a-f0-9]{64}$/).test(entry.verified_sha256))throw new Error('missing archived provenance');
    for(const window of windows){
      const peaks=entry.spectral_windows[window].filter(p=>p.n>=2&&p.n<=8&&p.contrast_db>=20&&p.relative_db>=-60);
      const fit=fitStiffString(peaks);
      const loo=peaks.map((_,i)=>fitStiffString(peaks.filter((_,j)=>i!==j)).B);
      results.push({layer,window,...fit,looMinB:Math.min(...loo),looMaxB:Math.max(...loo)});
    }
  }
  return {scope:'C5 C4 pressure peak sensitivity only, not C3X physical measurements or confidence intervals',sourceCommit:report.source_commit,sourceCI:report.source_ci_run,filter:'partials 2..8, contrast >=20 dB, relative level >= -60 dB',results,
    allBMin:Math.min(...results.map(x=>x.B)),allBMax:Math.max(...results.map(x=>x.B)),
    allLooMin:Math.min(...results.map(x=>x.looMinB)),allLooMax:Math.max(...results.map(x=>x.looMaxB))};
}
