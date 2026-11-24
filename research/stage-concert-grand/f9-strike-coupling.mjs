import {BoardCoupledBridge} from './board-coupling.mjs';
// Conjugate loaded contact compliance for the generalized spatial string port.
export class StrikeCoupledBridge extends BoardCoupledBridge{
 constructor(bridge,board,options){
  super(bridge,board,options);
  const a=bridge.vAxis,t=this.wires.map(()=>a.contactFraction);
  for(const m of a.modes)t[m.j]-=m.B*m.weight/m.A;
  this.cross=t.map(v=>this.gb*v);
  this.G=bridge.contactCompliance().map((row,i)=>row.map((v,j)=>v-this.alpha*this.cross[i]*this.cross[j]));
 }
}
