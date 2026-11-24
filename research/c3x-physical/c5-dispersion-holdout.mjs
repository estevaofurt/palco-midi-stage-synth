// F1.8 offline only: separate pitch scale from dispersion using archived C5 peaks. No render or parameter changes.
export function partialHz(n,f1,B) {
  if(!Number.isInteger(n)||n<1||n>128||!Number.isFinite(f1)||f1<=0||!Number.isFinite(B)||B<0)throw new RangeError('invalid stiff-string arguments');
  const f=n*f1*Math.sqrt((1+B*n*n)/(1+B));if(!Number.isFinite(f))throw new RangeError('overflow');return f;
}

export function centsRatio(a,b){if(!Number.isFinite(a)||!Number.isFinite(b)||a<=0||b<=0)throw new RangeError('positive frequencies required');return 1200*Math.log2(a/b);}

export function fitPitchFixedB(peaks,B){
  if(!Array.isArray(peaks)||peaks.length<2||new Set(peaks.map(p=>p.n)).size!==peaks.length)throw new RangeError('distinct partials required');
  const logs=peaks.map(p=>{if(!Number.isFinite(p.freq_hz)||p.freq_hz<=0)throw new RangeError('bad peak');return Math.log(p.freq_hz/partialHz(p.n,1,B));});
  return Math.exp(logs.reduce((a,b)=>a+b,0)/logs.length);
}

export function evaluateDispersion(report,fitStiffString){
  if(report.source_instrument!=='Yamaha C5, not Yamaha C3X'||report.reference_note!=='C4 MIDI60'||report.commercial_c3x_calibration_approved!==false)throw new Error('source identity');
  const baseB=.0005284491799769235, fixedB=baseB/(1-baseB),nominal=440*2**((60-69)/12);
  const rows=[],excluded=[],trainingBs=[];
  for(const layer of ['v1','v8','v16']){
    const item=report.layers[layer];
    if(item.not_a_measurement_of_C3X!==true||!(/^[a-f0-9]{64}$/).test(item.verified_sha256))throw new Error('missing archived provenance');
    for(const window of ['attack_35_255ms','body_260_700ms','tail_900_1400ms']){
      const eligible=item.spectral_windows[window].filter(p=>p.n>=2&&p.n<=12&&p.contrast_db>=20&&p.relative_db>=-60);
      const train=eligible.filter(p=>p.n<=8),hold=eligible.filter(p=>p.n>=9);
      if(train.length<4){excluded.push({layer,window,reason:'insufficient training peaks'});continue;}
      const free=fitStiffString(train);trainingBs.push(free.B);
      if(hold.length<1){excluded.push({layer,window,reason:'no eligible held-out peaks'});continue;}
      const freePitch=fitPitchFixedB(train,free.B),fixedPitch=fitPitchFixedB(train,fixedB);
      const errors=hold.map(p=>({n:p.n,measuredHz:p.freq_hz,freeErrorCents:centsRatio(partialHz(p.n,freePitch,free.B),p.freq_hz),fixedErrorCents:centsRatio(partialHz(p.n,fixedPitch,fixedB),p.freq_hz)}));
      const rms=k=>Math.sqrt(errors.reduce((s,e)=>s+e[k]**2,0)/errors.length);
      rows.push({layer,window,train:train.map(p=>p.n),hold:hold.map(p=>p.n),freeB:free.B,freePitchHz:freePitch,fixedPitchHz:fixedPitch,freeRmsCents:rms('freeErrorCents'),fixedRmsCents:rms('fixedErrorCents'),errors});
    }
  }
  if(!rows.length)throw new RangeError('no eligible validation windows');
  const all=rows.flatMap(r=>r.errors),rms=k=>Math.sqrt(all.reduce((s,e)=>s+e[k]**2,0)/all.length);
  trainingBs.sort((a,b)=>a-b);const mid=Math.floor(trainingBs.length/2);
  const representativeB=trainingBs.length%2?trainingBs[mid]:(trainingBs[mid-1]+trainingBs[mid])/2;
  const sensitivity=[1,2,4,5,8,12,16].map(n=>{const v10Hz=partialHz(n,nominal,fixedB),c5Hz=partialHz(n,nominal,representativeB);return {n,v10Hz,c5Hz,deltaHz:v10Hz-c5Hz,deltaCents:centsRatio(v10Hz,c5Hz)};});
  return {scope:'archived C5 pressure peaks; no C3X calibration or DSP change',baseB,fixedB,nominal,representativeB,rows,excluded,sensitivity,holdoutCount:all.length,freeRmsCents:rms('freeErrorCents'),fixedRmsCents:rms('fixedErrorCents'),windowsImproved:rows.filter(r=>r.freeRmsCents<r.fixedRmsCents).length};
}
