// G3.12q: conservative, local diagnostic; not real-time certification.
export const OPTIONS=Object.freeze([32,64,88,96,128,192]);
export function candidates(engine,quality,profile,rate){
  if(!['modal','physicalLegacy','physical','hybrid'].includes(engine)||!['eco','balanced','studio'].includes(quality)||!['lite','full'].includes(profile)||![44100,48000,96000].includes(rate))throw Error('configuração inválida');
  const ceiling=profile==='lite'||rate>48000?64:engine==='modal'?192:128;
  return OPTIONS.filter(n=>n<=Math.min(ceiling,engine!=='modal'&&quality==='eco'?32:192));
}
export function score(samples,active,rate,block=128){
  if(samples.length<200||!samples.every(x=>Number.isFinite(x)&&x>=0)||!samples.some(x=>x>0))throw Error('medição inválida');
  const t=[...samples].sort((a,b)=>a-b),budget=1000*block/rate;
  const p99=t[Math.ceil(.99*t.length)-1]/budget,overruns=t.filter(x=>x>budget).length;
  return {p99,overruns,active,pass:active===true&&p99<=.70&&overruns===0};
}
export function recommend(rows,expected){
  // Require two passes for every lower tested capacity; no leap over a failure.
  let value=null;
  for(const n of expected){
    const r=rows.filter(x=>x.voices===n);
    if(r.length!==2||!r.every(x=>x.pass===true))break;
    value=n;
  }
  return value;
}
