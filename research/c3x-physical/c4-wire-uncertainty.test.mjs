import {solidWire,auditV10C4} from './c4-wire-consistency.mjs';
import {logSensitivities,corners,inverseFromGeometry,analyzeUncertainty} from './c4-wire-uncertainty.mjs';
function runTests(solidWire,auditV10C4){
  const a=(v,m)=>{if(!v)throw Error(m)},near=(x,y,t)=>Math.abs(x-y)<t;
  const reject=fn=>{let bad=false;try{fn()}catch(e){bad=true}a(bad,'expected rejection')};
  const x=analyzeUncertainty(solidWire,auditV10C4),b=x.baseline;
  const cases=[
    ['analytic log Jacobian agrees with centered finite differences',()=>{for(const [k,s] of Object.entries(x.sensitivities)){const h=1e-5,lo=solidWire({...b,[k]:b[k]*Math.exp(-h)}),hi=solidWire({...b,[k]:b[k]*Math.exp(h)});a(near((Math.log(hi.f1Hz)-Math.log(lo.f1Hz))/(2*h),s.f1,1e-8),k+' f1');a(near((Math.log(hi.B)-Math.log(lo.B))/(2*h),s.B,1e-8),k+' B')}}],
    ['diameter fourth power stiffness',()=>a(x.sensitivities.diameterM.B===4,'d')],
    ['density does not enter B',()=>a(x.sensitivities.densityKgM3.B===0,'rho')],
    ['zero-width bounds return nominal',()=>{const q=corners(b,{lengthM:0},solidWire,['f1Hz','B']);a(near(q.f1Hz.min,b.f1Hz,1e-12)&&near(q.B.max,b.B,1e-15),'zero')}],
    ['forward bounds contain nominal',()=>a(x.forward.f1Hz.min<b.f1Hz&&x.forward.f1Hz.max>b.f1Hz&&x.forward.B.min<b.B&&x.forward.B.max>b.B,'forward')],
    ['forward extrema agree with monotonic signs',()=>{const lo={...b},hi={...b};for(const [k,v] of Object.entries(x.bounds)){const sign=Math.sign(x.sensitivities[k].f1);lo[k]-=sign*v;hi[k]+=sign*v;}a(near(solidWire(lo).f1Hz,x.forward.f1Hz.min,1e-10)&&near(solidWire(hi).f1Hz,x.forward.f1Hz.max,1e-10),'extrema')}],
    ['interior samples lie inside bounds',()=>{for(let i=0;i<100;i++){const p={...b};let j=0;for(const [k,v] of Object.entries(x.bounds))p[k]+=v*Math.sin(i*3.17+(++j)*2.12);const q=solidWire(p);for(const k of ['f1Hz','B'])a(q[k]>=x.forward[k].min&&q[k]<=x.forward[k].max,k)}}],
    ['inverse recovers tension and E',()=>{const q=inverseFromGeometry(b);a(near(q.tensionN,b.tensionN,1e-9)&&near(q.youngPa,b.youngPa,1e-3),'inverse')}],
    ['material scale ambiguity survives known geometry',()=>{for(const k of [.5,2]){const q=solidWire({...b,tensionN:b.tensionN*k,youngPa:b.youngPa*k,densityKgM3:b.densityKgM3*k});a(near(q.f1Hz,b.f1Hz,1e-9)&&near(q.B,b.B,1e-14),'scale')}}],
    ['inverse material scaling',()=>{const q=inverseFromGeometry({...b,densityKgM3:b.densityKgM3*1.1});a(near(q.tensionN/b.tensionN,1.1,1e-12)&&near(q.youngPa/b.youngPa,1.1,1e-12),'scale')}],
    ['inverse bounds contain nominal',()=>a(x.inverse.tensionN.min<b.tensionN&&x.inverse.tensionN.max>b.tensionN&&x.inverse.youngPa.min<b.youngPa&&x.inverse.youngPa.max>b.youngPa,'inverse')],
    ['all inverse corners reconstruct their f1 and B',()=>{const ks=Object.keys(x.inverseBounds);for(let mask=0;mask<32;mask++){const p={...b};ks.forEach((k,i)=>p[k]+=(mask&(1<<i)?1:-1)*x.inverseBounds[k]);const q=solidWire({...p,...inverseFromGeometry(p)});a(near(q.f1Hz,p.f1Hz,1e-9)&&near(q.B,p.B,1e-14),'roundtrip')}}],
    ['missing or invalid inputs rejected',()=>{reject(()=>inverseFromGeometry({...b,densityKgM3:undefined}));reject(()=>inverseFromGeometry({...b,B:0}));reject(()=>corners(b,{diameterM:b.diameterM},solidWire,['B']));reject(()=>corners(b,{lengthM:-1},solidWire,['B']));reject(()=>logSensitivities(NaN))}]
  ];for(const [name,fn] of cases){try{fn()}catch(e){throw Error(name+': '+e.message)}}return cases.map(c=>c[0]);
}
const passed=runTests(solidWire,auditV10C4);for(const name of passed)console.log('PASS '+name);console.log(`${passed.length}/${passed.length} tests passed`);console.log(JSON.stringify(analyzeUncertainty(solidWire,auditV10C4),null,2));
