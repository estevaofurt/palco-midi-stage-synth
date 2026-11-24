import {plateDesign,plateModes,patchWeight} from './orthotropic-plate.mjs';
import {ribDesign,ribbedModes,ribbedPatchWeight} from './ribbed-plate.mjs';
function checks(helpers){
  const a=(v,m)=>{if(!v)throw Error(m)},p=helpers.plateDesign(),ribs=[.14,.31,.48,.65,.82,.99,1.16,1.29].map(xM=>ribDesign(p,{xM}));
  const make=(basisHz,params={})=>ribbedModes(p,ribs,{basisHz,...params},helpers),bare=make(1000,{massScale:0,stiffnessScale:0}),mass=make(1000,{stiffnessScale:0}),stiff=make(1000,{massScale:0}),full=make(1000);
  const bases=[250,500,1000,2000,4000].map(f=>({cut:f,...make(f)})),ref=bases.at(-1);
  const convergence=bases.map(q=>({cut:q.cut,count:q.basisCount,first:q.modes[0].frequencyHz,maxFirst10Pct:100*Math.max(...q.modes.slice(0,10).map((m,i)=>Math.abs(m.frequencyHz/ref.modes[i].frequencyHz-1))),residual:q.maxResidual,orthogonality:q.maxOrthogonality}));
  const patch={xM:.83,yM:.46,dxM:.04,dyM:.025},other={xM:.37,yM:.71,dxM:.04,dyM:.025};
  const compliance=bases.map(q=>({cut:q.cut,value:q.modes.reduce((s,m)=>s+ribbedPatchWeight(p,m,patch,helpers.patchWeight)**2/m.lambda,0)}));
  const table=full.modes.slice(0,10).map((q,i)=>({i:i+1,bare:bare.modes[i].frequencyHz,mass:mass.modes[i].frequencyHz,stiff:stiff.modes[i].frequencyHz,full:q.frequencyHz,n:q.n,dominant:q.components.reduce((a,b)=>Math.abs(b.coefficient)>Math.abs(a.coefficient)?b:a).m}));
  const mobility=(f,pa,pb)=>{let re=0,im=0;const w=2*Math.PI*f;for(const m of ref.modes){const a=m.lambda-w*w,b=w*2*(2+.0005*Math.sqrt(m.lambda)),d=a*a+b*b,prod=ribbedPatchWeight(p,m,pa,helpers.patchWeight)*ribbedPatchWeight(p,m,pb,helpers.patchWeight);re+=w*b*prod/d;im+=w*a*prod/d;}return {re,im};};
  const frf=[30,100,261.63,500,1000].map(f=>{const aa=mobility(f,patch,patch),bb=mobility(f,other,other),ab=mobility(f,patch,other),ba=mobility(f,other,patch);return {f,aa,bb,ab,reciprocalError:Math.hypot(ab.re-ba.re,ab.im-ba.im),det:aa.re*bb.re-ab.re**2};});
  const wave=helpers.plateModes(p,16000),thin=[250,1000,4000,16000].map(cut=>{const q=wave.filter(m=>m.frequencyHz<cut);return {cut,count:q.length,maxKh:Math.max(...q.map(m=>p.thicknessM*Math.hypot(m.kx,m.ky))),aboveIllustrative02:q.filter(m=>p.thicknessM*Math.hypot(m.kx,m.ky)>.2).length};});
  const cases=[
    ['zero rib corrections reproduce bare analytic modes',()=>a(bare.modes.every((q,i)=>Math.abs(q.frequencyHz/helpers.plateModes(p,1000)[i].frequencyHz-1)<1e-10),'bare')],
    ['physical rib mass and stiffness',()=>a(ribs.every(q=>q.massKg>0&&q.EI>0)&&Math.abs(full.ribMassKg-8*.022*.025*430*1.1)<1e-12,'rib')],
    ['mass only cannot increase sorted eigenfrequencies',()=>a(mass.modes.every((q,i)=>q.frequencyHz<=bare.modes[i].frequencyHz*(1+1e-10)),'mass')],
    ['stiffness only cannot decrease sorted eigenfrequencies',()=>a(stiff.modes.every((q,i)=>q.frequencyHz>=bare.modes[i].frequencyHz*(1-1e-10)),'stiff')],
    ['generalized eigen residual and mass orthogonality',()=>a(bases.every(q=>q.maxResidual<1e-8&&q.maxOrthogonality<1e-9),'eigen '+JSON.stringify(convergence))],
    ['nested Ritz frequencies nonincreasing',()=>a(bases.slice(1).every((q,i)=>bases[i].modes.every((m,j)=>q.modes[j].frequencyHz<=m.frequencyHz*(1+1e-9))),'Ritz')],
    ['low band converges with larger basis',()=>a(convergence[3].maxFirst10Pct<convergence[0].maxFirst10Pct,'convergence')],
    ['patch static compliance monotonic under basis enrichment',()=>a(compliance.slice(1).every((q,i)=>q.value>=compliance[i].value-1e-15),'compliance')],
    ['reciprocity and nonnegative mobility real matrix',()=>a(frf.every(q=>q.aa.re>=0&&q.bb.re>=0&&q.det>=-1e-15&&q.reciprocalError<1e-14),'FRF')],
    ['mass normalized mode recovers correct patch scaling in bare limit',()=>{const q=bare.modes[0],target=helpers.patchWeight(p,helpers.plateModes(p,1000)[0],patch)/Math.sqrt(p.massKg/4);a(Math.abs(Math.abs(ribbedPatchWeight(p,q,patch,helpers.patchWeight))-Math.abs(target))<1e-12,'normalization')}],
    ['invalid rib geometry rejected',()=>{let bad=false;try{ribDesign(p,{xM:0})}catch(e){bad=true}a(bad,'invalid')}],
    ['thin plate high band diagnostic grows',()=>a(thin.at(-1).maxKh>thin[0].maxKh&&thin.at(-1).aboveIllustrative02>0,'kh')]
  ];
  for(const [n,f] of cases){try{f()}catch(e){throw Error(n+': '+e.message)}}
  return {passed:cases.map(c=>c[0]),ribs,ribMass:full.ribMassKg,table,convergence,compliance,frf,thin};
}
const result=checks({plateDesign,plateModes,patchWeight});for(const n of result.passed)console.log('PASS '+n);console.log(JSON.stringify(result,null,2));
