// F3.2: independent trichord and two orthogonal polarizations; no bridge coupling or sound radiation yet.
export class Trichord {
  constructor({detuneCents=[-.5,0,.5],centerFraction=.13,widthM=.012,stringOptions={},horizontalLoss={sigma0PerS:.2,sigma2M2PerS:.00012}}={},helpers){
    if(!Array.isArray(detuneCents)||detuneCents.length!==3||!detuneCents.every(v=>Number.isFinite(v)&&Math.abs(v)<=10)||!Number.isFinite(centerFraction)||centerFraction<=0||centerFraction>=1)throw new RangeError('trichord hypothesis');
    const {solidWire,makeDesign,StiffString,modalCoefficients}=helpers;
    this.strings=detuneCents.map(c=>{
      const wire=makeDesign(solidWire,{f1Hz:440*2**(-9/12+c/1200)});
      const vertical=new StiffString(wire,stringOptions,modalCoefficients),horizontal=new StiffString(wire,{...stringOptions,...horizontalLoss},modalCoefficients);
      if(vertical.dt!==horizontal.dt)throw new RangeError('polarization dt');
      return {cents:c,wire,vertical,horizontal,weightsV:vertical.weights(centerFraction*wire.lengthM,widthM),weightsH:horizontal.weights(centerFraction*wire.lengthM,widthM)};
    });
  }
  step(forces){
    if(!Array.isArray(forces)||forces.length!==3||forces.some(f=>!Number.isFinite(f?.verticalN)||!Number.isFinite(f?.horizontalN)))throw new RangeError('three vector forces required');
    for(let i=0;i<3;i++){const s=this.strings[i];s.vertical.step(s.weightsV,forces[i].verticalN);s.horizontal.step(s.weightsH,forces[i].horizontalN);}
  }
  energy(){return this.strings.reduce((e,s)=>e+s.vertical.energy()+s.horizontal.energy(),0);}
  ledger(){return this.strings.reduce((a,s)=>({workJ:a.workJ+s.vertical.workJ+s.horizontal.workJ,lossJ:a.lossJ+s.vertical.lossJ+s.horizontal.lossJ}),{workJ:0,lossJ:0});}
  supportForce(){return this.strings.reduce((f,s)=>({verticalN:f.verticalN+s.vertical.rightSupportForceN(),horizontalN:f.horizontalN+s.horizontal.rightSupportForceN()}),{verticalN:0,horizontalN:0});}
}

export function beatPredictions(tri){
  return [1,4,8,16].map(n=>{
    const hz=tri.strings.map(s=>s.vertical.modes[n-1].frequencyHz).sort((a,b)=>a-b),spanHz=hz[2]-hz[0];
    return {n,hz,adjacentHz:[hz[1]-hz[0],hz[2]-hz[1]],outerSpanHz:spanHz,outerBeatPeriodS:spanHz>0?1/spanHz:null};
  });
}

export function acousticWindowAudit(report,tri){
  if(report.source_instrument!=='Yamaha C5, not Yamaha C3X'||report.reference_note!=='C4 MIDI60')throw new Error('source identity');
  const rows=[],excluded=[];
  for(const layer of ['v1','v8','v16']){
    const l=report.layers[layer];
    if(l.not_a_measurement_of_C3X!==true||!/^[a-f0-9]{64}$/.test(l.verified_sha256))throw new Error('provenance');
    const body=l.spectral_windows.body_260_700ms,tail=l.spectral_windows.tail_900_1400ms;
    for(let n=1;n<=8;n++){
      const b=body.find(p=>p.n===n),t=tail.find(p=>p.n===n);
      if(!b||!t||![b,t].every(p=>p.contrast_db>=20&&p.relative_db>=-60&&Number.isFinite(p.amplitude)&&p.amplitude>0)){excluded.push({layer,n});continue;}
      const changeDb=20*Math.log10(t.amplitude/b.amplitude);
      rows.push({layer,n,changeDb,isolatedVerticalEnvelopeChangeDb:-20/Math.LN10*tri.strings[1].vertical.modes[n-1].sigma*.67});
    }
  }
  return {scope:'peak magnitude changes in two unequal analysis windows versus isolated modal envelope over midpoint separation 0.67 s; not calibrated pressure, decay constants or directly comparable output',rows,excluded};
}

export function truncationStudy(helpers){
  const {solidWire,makeDesign,StiffString,modalCoefficients}=helpers,wire=makeDesign(solidWire),rate=192000,dt=1/rate,duration=.005;
  const simulate=(cut,width)=>{
    const s=new StiffString(wire,{sampleRate:rate,maxFrequencyHz:cut},modalCoefficients),w=s.weights(.13*wire.lengthM,width),x=[],f=[];
    for(let i=0;i<rate*duration;i++){const t=(i+.5)*dt,F=t<.0005?.1*Math.sin(Math.PI*t/.0005)**2:0;s.step(w,F);x.push(s.projection(w));f.push(s.rightSupportForceN());}
    return {x,f,count:s.modes.length};
  };
  const rmsError=(a,b)=>Math.sqrt(a.reduce((s,v,i)=>s+(v-b[i])**2,0)/b.reduce((s,v)=>s+v*v,0));
  return [0,.012].flatMap(width=>{const ref=simulate(70000,width);return [8000,16000,32000].map(cut=>{const q=simulate(cut,width);return {widthM:width,cutoffHz:cut,modes:q.count,referenceModes:ref.count,displacementRmsRelative:rmsError(q.x,ref.x),supportForceRmsRelative:rmsError(q.f,ref.f)};});});
}
