import {DYNAMIC_GAIN,commonCrossing,compareDynamics} from './f9-dynamics-analysis.mjs';
export function checks(){
 let n=0;const check=(m,b)=>{if(!b)throw Error(m);n++;};
 const fixture=(velocity,g)=>({velocity,gain:DYNAMIC_GAIN,analysis:{windowS:.5,broadband:{drops:{40:{status:'synthetic'}}},windows:[1,.1,.01,.001,.0001,.00001].map((x,i)=>({startS:i*.5,rms:x*g,partials:[{rms:x*g,contrastDb:30}]}))}});
 const q=compareDynamics([fixture(.5,.1),fixture(1,1),fixture(2.5,10)]);
 check('common reference medium',q.referenceRms===1);
 check('initial levels differ by 20 dB',Math.abs(q.entries[0].initialDbRelativeToMedium+20)<1e-10&&Math.abs(q.entries[2].initialDbRelativeToMedium-20)<1e-10);
 check('same relative drops retained',q.entries.every(e=>e.relativeDrops[40].status==='synthetic'));
 check('common 40dB differs by attack',q.entries.map(e=>e.commonDrops[40].startS).join(',')==='0.5,1,1.5');
 check('below from start distinguished',commonCrossing([.001,.001],.5,1,40).status==='below-from-first-window');
 check('transient dip rejected',commonCrossing([1,.001,1,.001],.5,1,40).status==='not-observed');
 check('no extrapolation',commonCrossing([1,.1,.01],.5,1,40).status==='not-observed');
 let invalid=false;try{compareDynamics([fixture(.5,.1),fixture(1,1),{...fixture(2.5,10),gain:.2}])}catch{invalid=true}check('different gain rejected',invalid);
 return n;
}
console.log('F9.10 analysis tests passed:',checks());
