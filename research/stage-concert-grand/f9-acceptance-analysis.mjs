// Compare only common valid cells of the sparse F9.16 C5 summary.
export function compareCandidates(referenceWindows,candidates,layers,{minContrastDb=15}={}){
 if(!candidates.length||!Number.isFinite(minContrastDb))throw RangeError('candidates');
 const all=[{name:'reference',windows:referenceWindows},...candidates],db=(a,b)=>20*Math.log10(a/b);
 const valid=p=>p&&Number.isFinite(p.rms)&&p.rms>0&&Number.isFinite(p.contrastDb)&&p.contrastDb>=minContrastDb;
 return layers.map(layer=>{
  const cells=[];
  for(const w of layer.windows){
   if(![1,4,10,14].includes(w.startS))continue;
   const ws=all.map(c=>c.windows.find(x=>x.startS===w.startS));
   if(ws.some(x=>!x))continue;
   for(const p of w.partials){
    if(p.h===1||!Number.isFinite(p.referenceBalanceDb)||!ws.every(x=>valid(x.partials[0])&&valid(x.partials[p.h-1])))continue;
    const balances=ws.map(x=>db(x.partials[p.h-1].rms,x.partials[0].rms));
    cells.push({startS:w.startS,h:p.h,referenceBalanceDb:p.referenceBalanceDb,errors:balances.map(v=>v-p.referenceBalanceDb)});
   }
  }
  if(!cells.length)throw Error('no common support');
  const stats=(i,filter)=>{const x=cells.filter(filter).map(c=>c.errors[i]);return {count:x.length,meanAbsoluteDb:x.length?x.reduce((s,v)=>s+Math.abs(v),0)/x.length:null};};
  return {layer:layer.layer,cells,metrics:all.map((c,i)=>({name:c.name,all:stats(i,()=>true),upper:stats(i,x=>x.h>=6),p2:stats(i,x=>x.h===2)}))};
 });
}
export function contextualCrossing(windows,threshold,hold=2){
 if(!Number.isFinite(threshold)||threshold<=0||!Number.isInteger(hold)||hold<1||!windows.length||windows.some((w,i)=>!Number.isFinite(w.rms)||w.rms<0||w.endS-w.startS!==.5||(i&&w.startS!==windows[i-1].endS)))throw RangeError('complete half-second windows required');
 for(let i=0;i+hold<=windows.length;i++)if(windows.slice(i,i+hold).every(w=>w.rms<threshold))return {status:'observed-window',threshold,startS:windows[i].startS,confirmedThroughS:windows[i+hold-1].endS};
 return {status:'not-observed',threshold,analyzedThroughS:windows.at(-1).endS};
}
