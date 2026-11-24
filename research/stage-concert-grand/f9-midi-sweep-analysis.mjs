// Diagnostic over a complete sampled MIDI velocity range, not a perceptual score.
export function summarizeVelocitySweep(rows,hammerSpeed){
 if(!Array.isArray(rows)||rows.length!==127)throw Error('complete 127-row sweep required');
 const fields=['velocity','rmsPa','peakPa','peakForce','contactSpanS','impulseNs','reboundMps','maxBalance','maxIncrease','centroidHz','upperFraction'];
 for(let i=0;i<rows.length;i++){
  const r=rows[i];
  if(r.midiVelocity!==i+1||r.velocity!==hammerSpeed(i+1)||fields.some(k=>!Number.isFinite(r[k]))||!(r.rmsPa>0&&r.peakPa>0&&r.peakForce>0&&r.contactSpanS>0&&r.impulseNs>0&&r.reboundMps<0&&r.centroidHz>0)||r.maxBalance<0||r.maxIncrease<0||r.maxBalance>1e-9||r.maxIncrease>1e-9||r.upperFraction<0||r.upperFraction>1)throw Error('invalid row '+(i+1));
 }
 const steps=rows.slice(1).map((r,i)=>{const p=rows[i];return {from:p.midiVelocity,to:r.midiVelocity,rmsDb:20*Math.log10(r.rmsPa/p.rmsPa),peakDb:20*Math.log10(r.peakPa/p.peakPa),forceDb:20*Math.log10(r.peakForce/p.peakForce),centroidDeltaHz:r.centroidHz-p.centroidHz,upperFractionDelta:r.upperFraction-p.upperFraction,contactDeltaS:r.contactSpanS-p.contactSpanS};});
 const bounds=k=>({min:Math.min(...steps.map(s=>s[k])),max:Math.max(...steps.map(s=>s[k])),negative:steps.filter(s=>s[k]<0).map(s=>s.to),zero:steps.filter(s=>s[k]===0).map(s=>s.to)});
 return {count:rows.length,rangeRmsDb:20*Math.log10(rows.at(-1).rmsPa/rows[0].rmsPa),maxBalanceJ:Math.max(...rows.map(r=>r.maxBalance)),maxIncreaseJ:Math.max(...rows.map(r=>r.maxIncrease)),metrics:Object.fromEntries(['rmsDb','peakDb','forceDb','centroidDeltaHz','upperFractionDelta','contactDeltaS'].map(k=>[k,bounds(k)])),steps};
}
