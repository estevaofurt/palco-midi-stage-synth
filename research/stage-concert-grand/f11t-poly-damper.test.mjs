import {PolyDamperController,viscousMultiDamperStep} from './f11t-poly-damper.mjs';
let n=0;const check=(s,b)=>{if(!b)throw Error(s);n++},rejects=f=>{try{f();return false}catch{return true}};
const events=[{ms:0,type:'pedal',value:127},{ms:20,type:'off',midi:48},{ms:60,type:'pedal',value:0},{ms:90,type:'off',midi:64}];
const c=new PolyDamperController([48,64],events,.2);
check('pedal down',c.coefficientsAt(.05).every(x=>x===0));
check('first released note',c.coefficientsAt(.072)[0]>.4&&c.coefficientsAt(.072)[1]===0);
check('damper ramp',c.coefficientsAt(.087)[0]===1);
check('second released note',c.coefficientsAt(.1)[0]===1&&c.coefficientsAt(.1)[1]>.3);
check('duplicate off rejected',rejects(()=>new PolyDamperController([48],[{ms:5,type:'off',midi:48},{ms:6,type:'off',midi:48}],1)));
check('invalid pedal rejected',rejects(()=>new PolyDamperController([48],[{ms:0,type:'pedal',value:0}],1)));
check('event order enforced',rejects(()=>new PolyDamperController([48],[{ms:9,type:'off',midi:48},{ms:1,type:'pedal',value:127}],1)));
check('restrains note-on',rejects(()=>new PolyDamperController([48],[{ms:2,type:'on',midi:48}],1)));
check('duration check',rejects(()=>new PolyDamperController([48],[{ms:1000,type:'off',midi:48}],1)));
check('monotonic control',rejects(()=>c.coefficientsAt(.01)));
const make=()=>({
 bridges:[{},{ }],contacts:[{g:0,j:0},{g:1,j:0}],zero:[[0],[0]],h:.001,
 G:[[.0001,.00002],[.00002,.0001]],x:[.1,.08],free:[.09,.071],
 displacement(){return this.x.slice();},
 freeContacts(){return this.free.slice();},
 step(f=[[0],[0]]){this.x=this.free.map((v,i)=>v+this.G[i].reduce((s,g,j)=>s+g*f[j][0],0));}
});
const no=make();check('no damper',viscousMultiDamperStep(no,[0,0])===0&&no.x[0]===.09);
const one=make();check('selective damper',viscousMultiDamperStep(one,[1,0])>0&&one.x[1]!==one.free[1]);
const both=make();check('coupled damper',viscousMultiDamperStep(both,[1,1])>0&&both.x.every(Number.isFinite));
console.log('F11T_POLY_DAMPER_TESTS '+n);
