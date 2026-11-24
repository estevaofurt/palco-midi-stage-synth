import {HammerSharedNetwork} from './f9-sympathetic-network.mjs';
import {solveCholesky} from './radiation-loading.mjs';
// Switch the conjugate force/observation port only after hammer separation.
export class SpatialHammerNetwork extends HammerSharedNetwork{
 useDamperPort(fraction,width){
  const a=this.bridges[0].vAxis;a.setContactPort(fraction,width);
  const t=this.wires.map(()=>a.contactFraction);
  for(const m of a.modes)t[m.j]-=m.B*m.weight/m.A;
  this.contactCross=t.map(v=>this.gb[0]*v);
  const j=this.active.indexOf(0),alpha=j<0?0:solveCholesky(this.L,this.active.map((_,i)=>+(i===j)))[j];
  this.G=this.bridges[0].contactCompliance().map((row,i)=>row.map((v,k)=>v-alpha*this.contactCross[i]*this.contactCross[k]));
 }
}
