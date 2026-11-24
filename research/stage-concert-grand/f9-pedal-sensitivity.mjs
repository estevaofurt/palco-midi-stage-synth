// F9.14c: selection of a passive damping-contact setting, not physical pedal travel.
export const POSITIONS=Object.freeze([.13,.27]);
export const PEDAL_PROXIES=Object.freeze([.8,.9,.95]);
export function windowEnergy(windows,start=.5,end=1.5){
 const q=windows.filter(w=>w.startS>=start&&w.endS<=end);
 if(!q.length||Math.abs(q[0].startS-start)>1e-9||Math.abs(q.at(-1).endS-end)>1e-9||q.some((w,i)=>!Number.isFinite(w.rms)||w.rms<0||w.endS-w.startS!==.25||(i&&w.startS!==q[i-1].endS)))throw RangeError('invalid analysis windows');
 return q.reduce((s,w)=>s+w.rms*w.rms*(w.endS-w.startS),0);
}
export function assessCandidate(candidate,closed,open){
 const E0=windowEnergy(closed.windows),E1=windowEnergy(open.windows),E=windowEnergy(candidate.windows);
 if(!(E1>E0&&E0>0))throw RangeError('invalid control ordering');
 const q=candidate.windows.filter(w=>w.startS>=.5&&w.endS<=1.5);
 const db=(a,b)=>20*Math.log10(a/b);
 const initDb=db(candidate.windows[0].rms,closed.windows[0].rms);
 const band=q.map(w=>{const a=closed.windows.find(x=>x.startS===w.startS),b=open.windows.find(x=>x.startS===w.startS);if(!a||!b||!(w.rms>0&&a.rms>0&&b.rms>0))throw Error('window mismatch');return {startS:w.startS,aboveClosedDb:db(w.rms,a.rms),belowOpenDb:db(b.rms,w.rms)};});
 const fraction=(E-E0)/(E1-E0),energyDb=10*Math.log10(E/E0),openDb=10*Math.log10(E1/E),eligible=Math.abs(initDb)<.01&&fraction>0&&fraction<1&&band.every(w=>w.aboveClosedDb>=-.25&&w.belowOpenDb>=-.25);
 return {position:candidate.position,pedalProxy:candidate.pedal,effectiveDampingNsM:1-candidate.pedal,energyFraction:fraction,energyAboveClosedDb:energyDb,energyBelowOpenDb:openDb,initialDb:initDb,windows:band,eligible};
}
export function rankCandidates(rows){
 return rows.filter(x=>x.eligible).sort((a,b)=>Math.abs(a.energyFraction-.5)-Math.abs(b.energyFraction-.5)||a.position-b.position||a.pedalProxy-b.pedalProxy);
}
