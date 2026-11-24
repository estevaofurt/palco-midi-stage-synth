// F9.8: nonnegative distributed loss factors. No per-partial gain or time-dependent damping.
export function stringLossCase(name){
 switch(name){
 case 'control': return {verticalLoss:[.4,.0002],horizontalLoss:[.2,.00012]};
 case 'horizontal-half': return {verticalLoss:[.4,.0002],horizontalLoss:[.1,.00012]};
 case 'both-half': return {verticalLoss:[.2,.0002],horizontalLoss:[.1,.00012]};
 default: throw RangeError('unknown string loss case');
 }
}
