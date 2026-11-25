// Export physical control: three groups, one shared board, no duplicated vertical ground load.
import {movingReference,denseMatrices} from './g2_moving_reference.mjs';
import {PILOT_KEYS} from './g2_string_pilot.mjs';
import {buildBoard,PATCHES,weights} from './g2_board_pilot.mjs';
import {mkdirSync,writeFileSync} from 'node:fs';
const groups=PILOT_KEYS.map(key=>{
 const b=movingReference(key,96000,{support:{massKg:.025,stiffness:[0,2e6],damping:[0,5],angleRad:0}});
 const {M,C,K,ports,N,n}=denseMatrices(b),arr=a=>a.map(r=>Array.from(r));
 return {key,N,n,M:arr(M),C:arr(C),K:arr(K),ports:arr(ports)};
});
const boards=[4000,6000].map(basis=>{
 const b=buildBoard('control',basis),w=PATCHES.map(p=>weights(b,p));
 return {basis,residual:b.residual,orthogonality:b.orthogonality,modes:b.modes.map((m,i)=>({f:m.frequencyHz,lambda:m.lambda,w:w.map(q=>q[i]),components:m.components.map(c=>({m:c.m,n:c.n,kx:c.kx,ky:c.ky,coefficient:c.coefficient}))})).filter(m=>m.f<8000)};
});
mkdirSync('/tmp/g2-shared-board',{recursive:true});writeFileSync('/tmp/g2-shared-board/model.json',JSON.stringify({groups,boards}));
