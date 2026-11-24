import {boardMobility,loadedMobility,scanBand} from './f9-loaded-mobility.mjs';
export function checks(){
 let n=0;const check=(m,v)=>{if(!v)throw Error(m);n++;};
 const f=100,w=2*Math.PI*f,board={modes:[{lambda:w*w,w:2,coeff:{dampingNsM:3}}],blocks:[{indices:[0],R:[[5]]}]};
 const q=boardMobility(board,f);
 check('single mode resonant mobility',Math.abs(q.Y[0]-.5)<1e-12&&Math.abs(q.Y[1])<1e-12);
 check('power balance',Math.abs(q.powerResidualW)<1e-12&&Math.abs(q.inputW-.25)<1e-12);
 check('radiation structural split',Math.abs(q.radiationW/q.structuralW-5/3)<1e-12);
 const bare={vv:[.1,0],vh:[.02,0],hh:[.2,0]},none=loadedMobility(bare,q.Y,f,0,0);
 check('zero joint recovers bare',none.vv[0]===bare.vv[0]&&none.hh[0]===bare.hh[0]&&none.vh[0]===bare.vh[0]);
 const loaded=loadedMobility(bare,q.Y,f,0,4);
 check('series resistive load',Math.abs(loaded.Zload[0]-4/3)<1e-12);
 check('loaded network passive',loaded.vv[0]>0&&loaded.hh[0]>0&&loaded.realDet>0&&loaded.bridgeAndStringsW>0);
 check('input power split',Math.abs(loaded.inputW-loaded.boardInputW-loaded.jointLossW-loaded.bridgeAndStringsW)<1e-12);
 const scan=scanBand({mobility:()=>bare},board,{centerHz:f,halfWidthHz:1,stepHz:.5});
 check('scan grid',scan.length===5&&scan[0].f===99&&scan[4].f===101);
 const coupled={modes:[{lambda:w*w,w:2,coeff:{dampingNsM:3}},{lambda:1.1*w*w,w:-1,coeff:{dampingNsM:4}}],blocks:[{indices:[0,1],R:[[5,2],[2,4]]}]},c=boardMobility(coupled,f);
 check('coupled radiation power balance',Math.abs(c.powerResidualW)<1e-12&&c.radiationW>=0&&c.structuralW>=0&&c.maxRelativeResidual<1e-12);
 return n;
}
console.log('F9.11 mobility tests passed:',checks());
