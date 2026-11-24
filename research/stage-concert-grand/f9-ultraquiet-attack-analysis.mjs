// Relative attack shape metrics, not an audibility or musicality score.
export function compareQuietAttacks(rows){
 const speeds=[.06,.09,.12,.15];
 if(rows.length!==4||rows.some((r,i)=>r.velocity!==speeds[i]||r.windows.length!==3))throw RangeError('four matched quiet attacks required');
 const ref=rows[3];
 return {referenceVelocity:.15,rows:rows.map(r=>({velocity:r.velocity,windows:r.windows.map((w,i)=>{
  const b=ref.windows[i];
  if(w.startS!==b.startS||w.endS!==b.endS||![w.rms,w.centroidHz,w.upperFraction,b.rms,b.centroidHz,b.upperFraction].every(Number.isFinite)||w.rms<=0||w.centroidHz<=0||w.upperFraction<0||w.upperFraction>1||b.rms<=0||b.upperFraction<0||b.upperFraction>1)throw Error('invalid matched window');
  return {startS:w.startS,endS:w.endS,relativeRmsDb:20*Math.log10(w.rms/b.rms),centroidDeltaHz:w.centroidHz-b.centroidHz,upperFraction:w.upperFraction,upperFractionDelta:w.upperFraction-b.upperFraction,upperFractionRatio:b.upperFraction>0?w.upperFraction/b.upperFraction:null};
 })}))};
}
