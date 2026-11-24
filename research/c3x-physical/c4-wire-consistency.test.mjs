import {solidWire,solveAtLength,auditV10C4} from './c4-wire-consistency.mjs';
function runTests(){
  const a=(v,m)=>{if(!v)throw Error(m)},near=(x,y,t)=>Math.abs(x-y)<t;
  const reject=fn=>{let bad=false;try{fn()}catch(e){bad=true}a(bad,'expected rejection')};
  const x=auditV10C4(),b=x.base;
  const cases=[
    ['cross section',()=>a(near(b.areaM2,Math.PI*b.diameterM**2/4,1e-18),'area')],
    ['inertia',()=>a(near(b.inertiaM4,Math.PI*b.diameterM**4/64,1e-24),'I')],
    ['mass follows geometry',()=>a(near(b.linearDensityKgM,b.areaM2*b.densityKgM3,1e-15),'mass')],
    ['original V10 B reproduced',()=>a(near(b.B,.0005284491799769235,1e-14),'B')],
    ['original V10 target-based mass reproduced',()=>a(near(x.v10Mu,.008640011278,1e-12),'mu')],
    ['mass inconsistency positive',()=>a(x.massExcessPct>30&&x.massExcessPct<35,'gap')],
    ['tuning preserves T B',()=>a(near(x.v10TunedT*x.v10TunedB,b.tensionN*b.B,1e-12),'EI')],
    ['using solid mass changes pitch',()=>a(x.actualWireAtTunedT.f1Hz>x.f1TargetHz,'pitch')],
    ['solid retune matches target',()=>a(near(x.solidRetuned.f1Hz,x.f1TargetHz,1e-9),'target')],
    ['solid retune changes B',()=>a(x.solidRetuned.B>x.v10TunedB,'B')],
    ['inverse matches original wire',()=>{const q=solveAtLength(b);a(near(q.diameterM,b.diameterM,1e-12)&&near(q.tensionN,b.tensionN,1e-8),'inverse')}],
    ['families reproduce target and B',()=>a(x.families.every(q=>near(q.f1Hz,x.f1TargetHz,1e-9)&&near(q.B,x.Bc5,1e-14)),'families')],
    ['distinct geometries same frequencies',()=>a(x.families[0].diameterM!==x.families[4].diameterM&&x.families[0].tensionN!==x.families[4].tensionN,'nonunique')],
    ['diameter scales with length squared',()=>a(near(x.families[4].diameterM/x.families[0].diameterM,(.65/.45)**2,1e-12),'d scaling')],
    ['tension scales with length to sixth power',()=>a(near(x.families[4].tensionN/x.families[0].tensionN,(.65/.45)**6,1e-10),'T scaling')],
    ['same-length V10 B alternative',()=>a(near(x.sameLengthV10B.B,x.v10TunedB,1e-14)&&near(x.sameLengthV10B.f1Hz,x.f1TargetHz,1e-9),'alternative')],
    ['invalid and unknown inputs rejected',()=>{for(const patch of [{lengthM:0},{diameterM:-1},{tensionN:NaN},{youngPa:Infinity},{densityKgM3:undefined}])reject(()=>solidWire({...b,...patch}));reject(()=>solveAtLength({...b,B:0}));}]
  ];for(const [name,fn] of cases){try{fn()}catch(e){throw Error(name+': '+e.message)}}return cases.map(c=>c[0]);
}
const passed=runTests();for(const name of passed)console.log('PASS '+name);console.log(`${passed.length}/${passed.length} tests passed`);console.log(JSON.stringify(auditV10C4(),null,2));
