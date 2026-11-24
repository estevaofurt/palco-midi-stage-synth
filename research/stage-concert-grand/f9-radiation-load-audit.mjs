// Compare resistance matrices on identical modal coordinates and block membership.
// All quantities here concern the resistive surrogate, not full radiation impedance.
export function matrixDifference(reference,candidate){
 if(!reference.length||reference.length!==candidate.length)throw RangeError('matrix dimensions');
 let delta=0,norm=0,maxAsymmetry=0,maxAbs=0;
 for(let i=0;i<reference.length;i++){
  if(reference[i].length!==reference.length||candidate[i].length!==reference.length)throw RangeError('matrix shape');
  for(let j=0;j<reference.length;j++){
   const a=reference[i][j],b=candidate[i][j];
   if(!Number.isFinite(a)||!Number.isFinite(b))throw RangeError('matrix entry');
   norm+=a*a;delta+=(a-b)**2;maxAbs=Math.max(maxAbs,Math.abs(b));maxAsymmetry=Math.max(maxAsymmetry,Math.abs(b-candidate[j][i]));
  }
 }
 return {relativeFrobenius:norm>0?Math.sqrt(delta/norm):null,referenceSquaredNorm:norm,squaredDifference:delta,maxAbs,maxAsymmetry};
}
export function resistancePower(blocks,velocity){
 let power=0,absoluteScale=0;
 for(const b of blocks)for(let i=0;i<b.indices.length;i++)for(let j=0;j<b.indices.length;j++){
  const a=velocity[b.indices[i]],z=velocity[b.indices[j]],q=.5*b.R[i][j]*(a[0]*z[0]+a[1]*z[1]);
  if(!Number.isFinite(q))throw RangeError('invalid power');
  power+=q;absoluteScale+=Math.abs(q);
 }
 return {power,absoluteScale,passive:power>=-1e-12*Math.max(absoluteScale,1e-30)};
}
export function compareBlocks(reference,candidate){
 if(reference.length!==candidate.length)throw Error('block count');
 let norm=0,delta=0;const blocks=reference.map((r,i)=>{
  const c=candidate[i];if(r.indices.length!==c.indices.length||r.indices.some((v,j)=>v!==c.indices[j]))throw Error('block membership');
  const q=matrixDifference(r.R,c.R);norm+=q.referenceSquaredNorm;delta+=q.squaredDifference;
  return {centerHz:r.f,modeCount:r.indices.length,...q};
 });
 return {relativeFrobenius:norm>0?Math.sqrt(delta/norm):null,blocks};
}
export function dbRatio(candidate,reference){return Number.isFinite(candidate)&&Number.isFinite(reference)&&candidate>0&&reference>0?10*Math.log10(candidate/reference):null;}
