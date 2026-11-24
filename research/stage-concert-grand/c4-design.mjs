// Stage Concert Grand: original design candidate, C4 only, offline, no DSP integration.
export function makeDesign(solidWire,{lengthM=.65,diameterM=.00096,youngPa=200e9,densityKgM3=7850,f1Hz=440*2**(-9/12)}={}){
  for(const v of [lengthM,diameterM,youngPa,densityKgM3,f1Hz])if(!Number.isFinite(v)||v<=0)throw new RangeError('positive finite SI inputs required');
  const area=Math.PI*diameterM**2/4,I=Math.PI*diameterM**4/64;
  const tensionN=4*lengthM**2*densityKgM3*area*f1Hz**2-Math.PI**2*youngPa*I/lengthM**2;
  const wire=solidWire({lengthM,diameterM,youngPa,densityKgM3,tensionN});
  return {...wire,scope:'Stage original C4 design hypothesis, not a measured Yamaha',massKg:wire.linearDensityKgM*lengthM,transverseImpedanceNsM:Math.sqrt(wire.tensionN*wire.linearDensityKgM)};
}

export function compareReference(report,design,{partialHz,centsRatio,fitPitchFixedB}){
  if(report.source_instrument!=='Yamaha C5, not Yamaha C3X'||report.reference_note!=='C4 MIDI60'||report.commercial_c3x_calibration_approved!==false)throw new Error('unexpected source identity');
  const v10B=.0005284491799769235/(1-.0005284491799769235);
  const rows=[],excluded=[];
  for(const layer of ['v1','v8','v16']){
    const entry=report.layers[layer];
    if(entry.not_a_measurement_of_C3X!==true||!(/^[a-f0-9]{64}$/).test(entry.verified_sha256))throw new Error('missing provenance');
    for(const window of ['attack_35_255ms','body_260_700ms','tail_900_1400ms']){
      const peaks=entry.spectral_windows[window].filter(p=>p.n>=2&&p.n<=12&&p.contrast_db>=20&&p.relative_db>=-60);
      const train=peaks.filter(p=>p.n<=8),hold=peaks.filter(p=>p.n>=9);
      if(train.length<4||!hold.length){excluded.push({layer,window});continue;}
      const pitch=fitPitchFixedB(train,design.B),legacyPitch=fitPitchFixedB(train,v10B);
      const errors=hold.map(p=>({n:p.n,designErrorCents:centsRatio(partialHz(p.n,pitch,design.B),p.freq_hz),legacyErrorCents:centsRatio(partialHz(p.n,legacyPitch,v10B),p.freq_hz)}));
      const rms=k=>Math.sqrt(errors.reduce((s,e)=>s+e[k]**2,0)/errors.length);
      rows.push({layer,window,count:hold.length,designRms:rms('designErrorCents'),legacyRms:rms('legacyErrorCents'),errors});
    }
  }
  if(!rows.length)throw new Error('no scored windows');
  const all=rows.flatMap(x=>x.errors),rms=k=>Math.sqrt(all.reduce((s,e)=>s+e[k]**2,0)/all.length);
  return {scope:'retrospective C5 comparison; design selected using prior C5 results, not independent validation or audio render',rows,excluded,count:all.length,designRms:rms('designErrorCents'),legacyRms:rms('legacyErrorCents'),improvedWindows:rows.filter(x=>x.designRms<x.legacyRms).length};
}
