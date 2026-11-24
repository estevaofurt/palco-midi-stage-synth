// Compare adjacent resolution pairs on identical windows and gain, not a C5 fit.
export function compareResolutions(a,b,{minContrastDb=15}={}){
 if(a.windows.length!==b.windows.length||!a.windows.length||!Number.isFinite(minContrastDb))throw RangeError('windows');
 const db=(x,y)=>x>0&&y>0?20*Math.log10(x/y):null;
 const windows=a.windows.map((w,i)=>{
  const v=b.windows[i];if(w.startS!==v.startS||w.endS!==v.endS||w.partials.length!==10||v.partials.length!==10)throw Error('window mismatch');
  return {startS:w.startS,globalDeltaDb:db(v.rms,w.rms),partials:w.partials.map((p,j)=>{const q=v.partials[j],valid=[p,q].every(x=>Number.isFinite(x.contrastDb)&&x.contrastDb>=minContrastDb);return {h:j+1,deltaDb:valid?db(q.rms,p.rms):null,contrastA:p.contrastDb,contrastB:q.contrastDb};})};
 });
 const stats=arr=>{const x=arr.filter(Number.isFinite);return {count:x.length,maxAbsDb:x.length?Math.max(...x.map(Math.abs)):null,meanAbsDb:x.length?x.reduce((s,v)=>s+Math.abs(v),0)/x.length:null};};
 return {from:a.resolution,to:b.resolution,windows,global:stats(windows.map(w=>w.globalDeltaDb)),byPartial:Array.from({length:10},(_,j)=>({h:j+1,...stats(windows.map(w=>w.partials[j].deltaDb))}))};
}
