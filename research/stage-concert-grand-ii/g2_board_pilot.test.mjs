import assert from 'node:assert/strict';
import {buildBoard,BoardPilot,staticFlex,MATERIALS,PATCHES} from './g2_board_pilot.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
const bases=[],rows=[],checks=[];
for(const id of Object.keys(MATERIALS)){
 const coarse=buildBoard(id,2000),fine=buildBoard(id,4000);
 for(const b of [coarse,fine]){
  assert(b.modes.length===3*b.basisCount&&b.modes.every(m=>m.frequencyHz>0&&Number.isFinite(m.frequencyHz)));
  assert(b.residual<1e-6&&b.orthogonality<1e-9);
  const r={id,basisHz:b.basisHz,basisCount:b.basisCount,allModes:b.modes.length,below1k:b.modes.filter(m=>m.frequencyHz<1000).length,below3k:b.modes.filter(m=>m.frequencyHz<3000).length,massKg:b.p.massKg,ribMassKg:b.ribs.reduce((s,r)=>s+r.massKg,0),firstHz:b.modes[0].frequencyHz,first10:b.modes.slice(0,10).map(m=>m.frequencyHz),flex:PATCHES.map(p=>staticFlex(b,p)),flex3k:PATCHES.map(p=>staticFlex(b,p,3000)),residual:b.residual,orthogonality:b.orthogonality};
  bases.push(r);console.log('G2_BOARD_BASIS '+JSON.stringify(r));
 }
 const first10Error=Math.max(...coarse.modes.slice(0,10).map((m,i)=>Math.abs(m.frequencyHz/fine.modes[i].frequencyHz-1)));
 assert(coarse.modes.every((m,i)=>fine.modes[i].frequencyHz<=m.frequencyHz*(1+1e-7)));
 const flexError=PATCHES.map(p=>{const a=staticFlex(coarse,p),b=staticFlex(fine,p);assert(b>=a-1e-14);return Math.abs(a/b-1);});
 const gate=first10Error<=.02&&flexError.every(e=>e<=.1);checks.push({id,first10Error,flexError,gate});
 for(const sr of [48000,96000]){
  const q=new BoardPilot(fine,sr),frequencies=[100,130.81,261.63,500,1046.5,2000,2900];
  // Re(Y) is a Gram sum of real nonnegative modal contributions.
  for(const f of frequencies)for(let j=0;j<3;j++)for(let k=0;k<3;k++){
   const a=q.mobility(f,j,k),b=q.mobility(f,k,j);
   assert(Math.abs(a[0]-b[0])<1e-12&&Math.abs(a[1]-b[1])<1e-12);
   if(j===k)assert(a[0]>=0&&Number.isFinite(a[1]));
   else assert(a[0]**2<=q.mobility(f,j)[0]*q.mobility(f,k)[0]+1e-14);
  }
  for(let j=0;j<3;j++){
   const a=new BoardPilot(fine,sr),k=(j+1)%3,b=new BoardPilot(fine,sr);
   let maxBalance=0,maxIncrease=0,minLoss=0,maxReciprocity=0,peak=0;
   for(let i=0;i<sr*.02;i++){
    const fa=[0,0,0],fb=[0,0,0],f=i<sr*.001?.1*Math.sin(Math.PI*(i+.5)/(sr*.001))**2:0;
    fa[j]=f;fb[k]=f;const prev=a.energy();a.step(fa);b.step(fb);
    maxBalance=Math.max(maxBalance,Math.abs(a.energy()+a.lossJ-a.workJ),Math.abs(b.energy()+b.lossJ-b.workJ));
    minLoss=Math.min(minLoss,a.stepLossJ,b.stepLossJ);if(f===0)maxIncrease=Math.max(maxIncrease,a.energy()-prev);
    maxReciprocity=Math.max(maxReciprocity,Math.abs(a.position(k)-b.position(j)));peak=Math.max(peak,Math.abs(a.position(j)));
   }
   assert(maxBalance<1e-10&&minLoss>=-1e-12&&maxIncrease<=1e-12&&maxReciprocity<1e-12&&peak>0&&a.lossJ>0);
   rows.push({id,sr,patchKey:PATCHES[j].key,modes:a.modes.length,peakDisplacementM:peak,energyJ:a.energy(),lossJ:a.lossJ,workJ:a.workJ,maxBalance,minLoss,maxIncrease,maxReciprocity,mobility:frequencies.map(f=>({f,Y:a.mobility(f,j)}))});
  }
 }
}
assert.throws(()=>buildBoard('invalid'),/material/);
const gate=checks.every(r=>r.gate);
mkdirSync('/tmp/g2-board',{recursive:true});writeFileSync('/tmp/g2-board/report.json',JSON.stringify({scope:'isolated Mindlin board, fixed geometry, partial material comparison, hypothetical patches, no pressure',bases,rows,checks,gate},null,2));
for(const r of checks)console.log('G2_BOARD_CONVERGENCE '+JSON.stringify(r));
console.log('G2_BOARD_GATE '+JSON.stringify({bases:bases.length,physical:rows.length,convergence:checks.length,passed:checks.filter(r=>r.gate).length,gate}));
if(!gate)process.exitCode=1;
