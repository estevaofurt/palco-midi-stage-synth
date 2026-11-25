// G2.09a: lifted moving-boundary reference, not production modal integrator.
import {PolarizedBridge} from '../stage-concert-grand/polarized-bridge.mjs';
import {stringMode,spatialWeight} from '../stage-concert-grand/stiff-string.mjs';
import {StringPilot,pilotCutoffHz,DESIGN} from './g2_string_pilot.mjs';
import {GROUP_COUNT,offsets} from './g2_group_hammer.mjs';
import {LOSS_CASES} from './g2_decay.mjs';
// Explicitly preserve G2 5 mm contact footprint; G1 reference uses 12 mm.
const helpers={stringMode,spatialWeight:(m,L,x,_width)=>spatialWeight(m,L,x,DESIGN.widthM)};
export const SUPPORT=Object.freeze({massKg:.025,stiffness:[1e6,2e6],damping:[20,5],angleRad:.5});
export function movingReference(key,sr=192000,{spread=.5,cutoffHz=pilotCutoffHz(key),loss=LOSS_CASES.control,support=SUPPORT}={}){
 if(![48000,96000,192000,384000].includes(sr)||!Number.isFinite(cutoffHz)||cutoffHz<=0||cutoffHz>.4*sr)throw RangeError('reference rate or band');
 const count=GROUP_COUNT[key];if(!count)throw RangeError('pilot key');
 // StringPilot supplies the physical tension-corrected geometry, not its integrator.
 const wires=offsets(count,spread).map(cents=>new StringPilot(key,96000,{cents,cutoffHz}).wire);
 const l=[loss.sigma0PerS,loss.sigma2M2PerS];
 return new PolarizedBridge(wires,{...support,sampleRate:sr,maxFrequencyHz:cutoffHz,verticalLoss:l,horizontalLoss:l},helpers);
}
// Independent dense assembly of the lifted M,C,K reference in physical coordinates.
// Ordering: vertical bridge, vertical sine modes, horizontal bridge, horizontal sine modes.
export function denseMatrices(b){
 const N=b.vAxis.modes.length+1,n=2*N;
 const mat=()=>Array.from({length:n},()=>new Float64Array(n));
 const M=mat(),C=mat(),K=mat(),ports=[];
 for(const [axis,a] of [b.vAxis,b.hAxis].entries()){
  const o=axis*N;M[o][o]=a.mB;C[o][o]=a.cB;K[o][o]=a.kB;
  for(let j=0;j<a.modes.length;j++){const m=a.modes[j],i=o+j+1;M[i][i]=m.m;K[i][i]=m.k;C[i][i]=m.c;M[i][o]=M[o][i]=m.cross;C[i][o]=C[o][i]=m.cc;}
  for(let j=0;j<b.wires.length;j++){const p=new Float64Array(n);p[o]=.13;for(let i=0;i<a.modes.length;i++)if(a.modes[i].j===j)p[o+i+1]=a.modes[i].weight;ports.push(p);}
 }
 C[0][N]=C[N][0]=b.C.vh;K[0][N]=K[N][0]=b.K.vh;
 return {M,C,K,ports,N,n};
}
export function denseStep(b,fv,fh,bv=0,bh=0){
 const {M,C,K,ports,N,n}=denseMatrices(b),h=b.h,axes=[b.vAxis,b.hAxis],x=new Float64Array(n),v=new Float64Array(n),F=new Float64Array(n);
 for(let a=0;a<2;a++){const o=a*N,z=axes[a];x[o]=z.b;v[o]=z.vb;x.set(z.x,o+1);v.set(z.v,o+1);}
 F[0]=bv;F[N]=bh;
 for(const [j,f] of [...fv,...fh].entries())for(let i=0;i<n;i++)F[i]+=ports[j][i]*f;
 const A=M.map((r,i)=>Float64Array.from(r,(m,j)=>m+h*C[i][j]/2+h*h*K[i][j]/4));
 const rhs=Float64Array.from(F,(f,i)=>h*f/2+M[i].reduce((s,m,j)=>s+m*v[j]-h*K[i][j]*x[j]/2,0));
 // Generic Cholesky, independent of reference's arrowhead Schur solve.
 const L=Array.from({length:n},()=>new Float64Array(n));
 for(let i=0;i<n;i++)for(let j=0;j<=i;j++){let r=A[i][j];for(let k=0;k<j;k++)r-=L[i][k]*L[j][k];if(i===j){if(!(r>0))throw Error('dense SPD');L[i][j]=Math.sqrt(r);}else L[i][j]=r/L[j][j];}
 const mid=new Float64Array(n);
 for(let i=0;i<n;i++){let r=rhs[i];for(let j=0;j<i;j++)r-=L[i][j]*mid[j];mid[i]=r/L[i][i];}
 for(let i=n-1;i>=0;i--){let r=mid[i];for(let j=i+1;j<n;j++)r-=L[j][i]*mid[j];mid[i]=r/L[i][i];}
 return {x:Float64Array.from(x,(q,i)=>q+h*mid[i]),v:Float64Array.from(v,(q,i)=>2*mid[i]-q)};
}
export function state(b){const x=[],v=[];for(const a of [b.vAxis,b.hAxis]){x.push(a.b,...a.x);v.push(a.vb,...a.v);}return {x,v};}
