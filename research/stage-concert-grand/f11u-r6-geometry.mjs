// R6: exploratory bridge trajectory, anchored at C4, not measured piano geometry.
export function bridgePatches(notes,layout,p){
 if(!['coincident','narrow','wide'].includes(layout)||!notes.length)throw RangeError('bridge layout');
 const span={coincident:0,narrow:.12,wide:.24}[layout];
 return notes.map(midi=>{
  const d=(midi-60)/12;
  const xM=.83+span*d,yM=.46+.35*span*d,dxM=.04,dyM=.025;
  if(xM-dxM/2<0||xM+dxM/2>p.lengthM||yM-dyM/2<0||yM+dyM/2>p.widthM)throw RangeError('experimental patch outside board');
  return {xM,yM,dxM,dyM};
 });
}
export function portSummary(G){
 const pairs=[];
 for(let i=0;i<G.length;i++){
  if(!(G[i][i]>0))throw Error('nonpositive port diagonal');
  for(let j=0;j<i;j++){
   const scale=Math.sqrt(G[i][i]*G[j][j]);
   if(Math.abs(G[i][j]-G[j][i])>1e-10*scale)throw Error('nonreciprocal port matrix');
   const v=(G[i][j]+G[j][i])/(2*scale);
   if(Math.abs(v)>1+1e-9)throw Error('nonpassive port correlation');
   pairs.push(v);
  }
 }
 return {pairs,meanAbs:pairs.length?pairs.reduce((s,v)=>s+Math.abs(v),0)/pairs.length:null};
}
