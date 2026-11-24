import {ribbedPatchWeight} from './ribbed-plate.mjs';
import {modalCoefficients} from './exact-modal.mjs';
// F6.3: conjugate board/bridge attachment, shared constant force and discrete work.
export class BoardPort {
  constructor(p,modes,patch,h,{loss0=2,lossSlope=.0005}={},helpers){
    if(!modes.length||!Number.isFinite(h)||h<=0||![loss0,lossSlope].every(x=>Number.isFinite(x)&&x>=0))throw new RangeError('board');
    this.h=h;this.modes=modes.map(m=>({ ...m,w:ribbedPatchWeight(p,m,patch,helpers.patchWeight),coeff:modalCoefficients({massKg:1,frequencyHz:m.frequencyHz,dampingNsM:2*(loss0+lossSlope*2*Math.PI*m.frequencyHz),dt:h})}));
    this.x=new Float64Array(modes.length);this.v=new Float64Array(modes.length);this.workJ=0;this.lossJ=0;this.G=this.modes.reduce((s,m)=>s+m.w*m.w*m.coeff.G,0);
  }
  position(){return this.modes.reduce((s,m,i)=>s+m.w*this.x[i],0);}
  free(){return this.modes.reduce((s,m,i)=>s+m.w*(m.coeff.A*this.x[i]+m.coeff.S*this.v[i]),0);}
  energy(){return this.modes.reduce((s,m,i)=>s+.5*(this.v[i]**2+m.lambda*this.x[i]**2),0);}
  step(force){
    let work=0,loss=0;
    for(let i=0;i<this.modes.length;i++){const m=this.modes[i],p=m.coeff,x=this.x[i],v=this.v[i],f=m.w*force,xn=p.A*x+p.S*v+p.G*f,vn=p.H*x+p.D*v+p.J*f,w=f*(xn-x);work+=w;loss+=w+.5*(v*v-vn*vn+m.lambda*(x*x-xn*xn));this.x[i]=xn;this.v[i]=vn;}
    this.workJ+=work;this.lossJ+=loss;
  }
}

export class BoardCoupledBridge {
  constructor(bridge,board,{jointK=1e7,jointC=1}={}){
    if(bridge.h!==board.h||![jointK,jointC].every(x=>Number.isFinite(x)&&x>=0))throw new RangeError('joint');
    this.bridge=bridge;this.board=board;this.h=bridge.h;this.wires=bridge.wires;this.k=jointK;this.c=jointC;
    this.workJ=0;this.lossJ=0;this.jointLossJ=0;this.lastJointForce=0;
    const h=this.h,a=bridge.vAxis;this.gb=h*h/2*bridge.hAxis.schur/bridge.det;
    const t=this.wires.map(()=>.13);for(const m of a.modes)t[m.j]-=m.B*m.weight/m.A;
    this.cross=t.map(v=>this.gb*v);this.alpha=(jointK/2+jointC/h)/(1+(jointK/2+jointC/h)*(this.gb+board.G));
    this.G=bridge.contactCompliance().map((row,i)=>row.map((v,j)=>v-this.alpha*this.cross[i]*this.cross[j]));
  }
  contactDisplacement(j){return this.bridge.contactDisplacement(j);}
  contactCompliance(){return this.G.map(row=>row.slice());}
  relative(){return this.bridge.vAxis.b-this.board.position();}
  energy(){return this.bridge.energy()+this.board.energy()+.5*this.k*this.relative()**2;}
  prediction(fv,fh,bv=0,bh=0,boardForce=0){
    const b=this.bridge,p=this.board,h=this.h,r0=this.relative(),q=b.predict(fv,fh,bv,bh);
    const rf=b.vAxis.b+h*q.mv-p.free()-p.G*boardForce;
    const f=-(this.k*(r0+rf)/2+this.c*(rf-r0)/h)/(1+(this.k/2+this.c/h)*(this.gb+p.G));
    return {f,rf};
  }
  freeContacts(){
    const zero=this.wires.map(()=>0),{f}=this.prediction(zero,zero);
    return this.bridge.freeContacts().map((y,i)=>y+this.cross[i]*f);
  }
  step(fv=this.wires.map(()=>0),fh=this.wires.map(()=>0),bv=0,bh=0,boardForce=0){
    if(fv.length!==this.wires.length||fh.length!==this.wires.length||![...fv,...fh,bv,bh,boardForce].every(Number.isFinite))throw new RangeError('forces');
    const r0=this.relative(),b0=this.bridge.vAxis.b,p0=this.board.position(),w0=this.bridge.workJ+this.board.workJ,d0=this.bridge.lossJ+this.board.lossJ;
    const {f}=this.prediction(fv,fh,bv,bh,boardForce);
    this.bridge.step(fv,fh,bv+f,bh);this.board.step(boardForce-f);
    const dr=this.relative()-r0,loss=this.c*dr*dr/this.h;
    this.workJ+=this.bridge.workJ+this.board.workJ-w0-f*((this.bridge.vAxis.b-b0)-(this.board.position()-p0));
    this.lossJ+=this.bridge.lossJ+this.board.lossJ-d0+loss;this.jointLossJ+=loss;this.lastJointForce=f;
  }
}
