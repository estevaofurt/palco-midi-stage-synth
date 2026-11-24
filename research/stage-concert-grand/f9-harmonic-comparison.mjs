// F9.16: compare like-window partial RMS, never absolute C5 recording level.
// A low-contrast measurement is censored rather than counted as a fit.
export function comparePartialWindows(stage,reference,{minContrastDb=15}={}){
 if(!Array.isArray(stage)||!Array.isArray(reference)||!Number.isFinite(minContrastDb))throw RangeError('comparison options');
 const db=(a,b)=>20*Math.log10(a/b);
 const positive=p=>p&&Number.isFinite(p.rms)&&p.rms>0&&Number.isFinite(p.contrastDb)&&p.contrastDb>=minContrastDb;
 const windows=[];
 for(const sw of stage){
  const rw=reference.find(x=>Math.abs(x.startS-sw.startS)<1e-8);if(!rw)continue;
  if(sw.partials.length!==10||rw.partials.length!==10)throw Error('expected ten partials');
  const firstS=stage[0].partials,firstR=reference[0].partials;
  const partials=sw.partials.map((p,i)=>{
   const q=rw.partials[i],balance=positive(p)&&positive(q)&&positive(sw.partials[0])&&positive(rw.partials[0]),
    decay=positive(p)&&positive(q)&&positive(firstS[i])&&positive(firstR[i]);
   const stageBalanceDb=balance?db(p.rms,sw.partials[0].rms):null,referenceBalanceDb=balance?db(q.rms,rw.partials[0].rms):null,
     stageDecayDb=decay?db(p.rms,firstS[i].rms):null,referenceDecayDb=decay?db(q.rms,firstR[i].rms):null;
   return {h:i+1,stageContrastDb:p.contrastDb,referenceContrastDb:q.contrastDb,stageBalanceDb,referenceBalanceDb,balanceErrorDb:balance?stageBalanceDb-referenceBalanceDb:null,stageDecayDb,referenceDecayDb,decayErrorDb:decay?stageDecayDb-referenceDecayDb:null};
  });
  windows.push({startS:sw.startS,partials});
 }
 if(!windows.length)throw Error('no aligned windows');
 return {minContrastDb,windows,byPartial:Array.from({length:10},(_,i)=>{
  const p=windows.map(w=>w.partials[i]),stats=k=>{const v=p.map(x=>x[k]).filter(Number.isFinite);return {count:v.length,meanAbsoluteDb:v.length?v.reduce((s,x)=>s+Math.abs(x),0)/v.length:null};};
  return {h:i+1,balance:stats('balanceErrorDb'),decay:stats('decayErrorDb')};
 })};
}
