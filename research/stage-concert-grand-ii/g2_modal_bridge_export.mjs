// Export the validated physical matrices, not acoustic data.
import {movingReference,denseMatrices,state} from './g2_moving_reference.mjs';
import {PILOT_KEYS,pilotCutoffHz} from './g2_string_pilot.mjs';
import {LOSS_CASES} from './g2_decay.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
const out=[];
for(const key of PILOT_KEYS)for(const lossId of ['control','baseHalf']){
 const b=movingReference(key,384000,{loss:LOSS_CASES[lossId]}),{M,C,K,ports,N,n}=denseMatrices(b);
 b.vAxis.x[0]=1e-4;const initial=state(b),trace=[];
 const z=Array(b.wires.length).fill(0);
 for(let i=0;i<384000*.04;i++){b.step(z,z);if((i+1)%384===0)trace.push([b.vAxis.b,b.hAxis.b]);}
 const asArray=m=>m.map(r=>Array.from(r));
 out.push({key,lossId,cutoffHz:pilotCutoffHz(key),N,n,M:asArray(M),C:asArray(C),K:asArray(K),ports:asArray(ports),initial,trace});
}
mkdirSync('/tmp/g2-modal-bridge',{recursive:true});
writeFileSync('/tmp/g2-modal-bridge/physical.json',JSON.stringify(out));
