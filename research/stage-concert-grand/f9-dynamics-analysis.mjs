// F9.10: common-gain listening and common-reference decay. No psychoacoustic threshold.
export const DYNAMIC_GAIN=.1;
export const DYNAMIC_SPEEDS=Object.freeze([.5,1,2.5]);
export function commonCrossing(values,step,reference,drop,hold=2){
 if(!Array.isArray(values)||!values.length||!values.every(x=>Number.isFinite(x)&&x>=0)||!Number.isFinite(step)||step<=0||!Number.isFinite(reference)||reference<=0||!Number.isFinite(drop)||drop<=0||!Number.isInteger(hold)||hold<1)throw RangeError('crossing options');
 const threshold=reference*10**(-drop/20);
 for(let i=0;i+hold<=values.length;i++)if(values.slice(i,i+hold).every(x=>x<=threshold*(1+1e-12)))return {status:i===0?'below-from-first-window':'observed-window',threshold,startS:i*step,endS:(i+1)*step,confirmedThroughS:(i+hold)*step};
 return {status:'not-observed',threshold,analyzedThroughS:values.length*step};
}
export function compareDynamics(entries){
 if(!Array.isArray(entries)||entries.length!==3||!DYNAMIC_SPEEDS.every(v=>entries.filter(e=>e.velocity===v).length===1))throw RangeError('expected three velocities');
 const medium=entries.find(e=>e.velocity===1),ref=medium.analysis.windows[0].rms,step=medium.analysis.windowS;
 if(!Number.isFinite(ref)||ref<=0||!Number.isFinite(step)||step<=0)throw RangeError('invalid medium reference');
 const db=(x,y)=>x>0&&y>0?20*Math.log10(x/y):null;
 return {method:'all float signals use one gain; common thresholds relative to medium first complete window, not SPL audibility; per-note relative crossing also retained',gain:DYNAMIC_GAIN,referenceRms:ref,windowS:step,entries:DYNAMIC_SPEEDS.map(velocity=>{
  const e=entries.find(q=>q.velocity===velocity),a=e.analysis,values=a.windows.map(w=>w.rms);
  if(e.gain!==DYNAMIC_GAIN||a.windowS!==step||a.windows.length!==medium.analysis.windows.length||a.windows.some((w,i)=>Math.abs(w.startS-i*step)>1e-9)||!Number.isFinite(values[0])||values[0]<=0)throw RangeError('inconsistent analysis');
  return {velocity,initialRms:values[0],initialDbRelativeToMedium:db(values[0],ref),relativeDrops:a.broadband.drops,commonDrops:Object.fromEntries([20,40,60,80].map(d=>[d,commonCrossing(values,step,ref,d)])),windows:a.windows.filter(w=>[0,1,2,4,8,10,14,19,24,29,34,39].includes(w.startS)).map(w=>({startS:w.startS,rms:w.rms,dbRelativeToMedium:db(w.rms,ref),dbRelativeToOwnStart:db(w.rms,values[0]),partials:w.partials.map((p,i)=>({h:i+1,rms:p.rms,contrastDb:p.contrastDb,relativeDb:db(p.rms,a.windows[0].partials[i].rms)}))}))};
 })};
}
