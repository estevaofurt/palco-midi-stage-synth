// F5.1: energy-consistent moving simply supported boundary, one polarization; midpoint reference, not real-time engine.
export class SpatialMovingBridge {
  // Galerkin lifting: y_i(x)=b*x/L_i + sum q_in sin(n*pi*x/L_i).
  constructor(wires,{sampleRate=192000,maxFrequencyHz=16000,bridgeMassKg=.025,bridgeK=1e6,bridgeC=20,sigma0=.4,sigma2=.0002}={},helpers){
    if(!Array.isArray(wires)||!wires.length||wires.length>88||![sampleRate,maxFrequencyHz,bridgeMassKg].every(v=>Number.isFinite(v)&&v>0)||![bridgeK,bridgeC,sigma0,sigma2].every(v=>Number.isFinite(v)&&v>=0))throw new RangeError('bridge parameters');
    this.contactFraction=.13;this.contactWidth=.012;this.helpers=helpers;
    this.h=1/sampleRate;this.mB=bridgeMassKg;this.kB=bridgeK;this.cB=bridgeC;this.b=0;this.vb=0;this.modes=[];this.wires=wires.map(w=>({...w}));this.workJ=0;this.lossJ=0;this.bridgeLossJ=0;this.stringLossJ=0;this.bridgeK=bridgeK;this.bridgeC=bridgeC;this.massSchur=bridgeMassKg;
    const h=this.h,cut=Math.min(maxFrequencyHz,.4*sampleRate);
    for(let j=0;j<wires.length;j++){
      const w=wires[j],L=w.lengthM,mu=w.linearDensityKgM;
      this.mB+=mu*L/3;this.kB+=w.tensionN/L;this.cB+=2*mu*(sigma0*L/3+sigma2/L);this.massSchur+=mu*L/3;
      let count=0;
      for(let n=1;n<=4096;n++){
        const m=helpers.stringMode(w,n);if(m.frequencyHz>=cut)break;
        const cross=mu*L*(-1)**(n+1)/(n*Math.PI),c=2*m.massKg*(sigma0+sigma2*m.waveNumber**2),cc=2*sigma0*cross,k=m.stiffnessNPerM;
        const weight=helpers.spatialWeight(m,L,.13*L,.012);
        this.modes.push({j,n,m:m.massKg,k,c,cross,cc,weight,A:m.massKg+h*c/2+h*h*k/4,B:cross+h*cc/2});
        this.massSchur-=cross*cross/m.massKg;count++;
      }
      if(!count)throw new RangeError('no modes');
    }
    this.schur=this.mB+h*this.cB/2+h*h*this.kB/4-this.modes.reduce((s,m)=>s+m.B*m.B/m.A,0);
    if(!(this.schur>0&&this.massSchur>0))throw new RangeError('nonpositive matrix');
    this.x=new Float64Array(this.modes.length);this.v=new Float64Array(this.modes.length);this.rhs=new Float64Array(this.modes.length);this.mid=new Float64Array(this.modes.length);
  }
  energy(){
    let e=.5*(this.mB*this.vb**2+this.kB*this.b**2);
    for(let i=0;i<this.modes.length;i++){const m=this.modes[i];e+=.5*(m.m*this.v[i]**2+m.k*this.x[i]**2)+m.cross*this.v[i]*this.vb;}return e;
  }
  wireEnergy(j){
    const w=this.wires[j];let e=.5*(w.linearDensityKgM*w.lengthM/3*this.vb**2+w.tensionN/w.lengthM*this.b**2);
    for(let i=0;i<this.modes.length;i++){const m=this.modes[i];if(m.j===j)e+=.5*(m.m*this.v[i]**2+m.k*this.x[i]**2)+m.cross*this.v[i]*this.vb;}return e;
  }
  step(forces=Array(this.wires.length).fill(0),bridgeForce=0){
    if(forces.length!==this.wires.length||!Array.from(forces).every(Number.isFinite)||!Number.isFinite(bridgeForce))throw new RangeError('force');
    const h=this.h,b0=this.b,v0=this.vb;
    const fB=bridgeForce+this.contactFraction*Array.from(forces).reduce((a,b)=>a+b,0);
    let rhsB=this.mB*v0+h*(fB-this.kB*b0)/2;
    for(let i=0;i<this.modes.length;i++){const m=this.modes[i];rhsB+=m.cross*this.v[i];this.rhs[i]=m.m*this.v[i]+m.cross*v0+h*(m.weight*forces[m.j]-m.k*this.x[i])/2;rhsB-=m.B*this.rhs[i]/m.A;}
    const vbMid=rhsB/this.schur;
    let d=this.cB*vbMid**2,work=fB*vbMid;
    for(let i=0;i<this.modes.length;i++){const m=this.modes[i],v=(this.rhs[i]-m.B*vbMid)/m.A;this.mid[i]=v;d+=m.c*v*v+2*m.cc*v*vbMid;work+=m.weight*forces[m.j]*v;this.x[i]+=h*v;this.v[i]=2*v-this.v[i];}
    this.b+=h*vbMid;this.vb=2*vbMid-v0;this.workJ+=h*work;this.lossJ+=h*d;this.bridgeLossJ+=h*this.bridgeC*vbMid**2;this.stringLossJ+=h*(d-this.bridgeC*vbMid**2);
  }
  contactDisplacement(j){let x=this.contactFraction*this.b;for(let i=0;i<this.modes.length;i++)if(this.modes[i].j===j)x+=this.modes[i].weight*this.x[i];return x;}
  setContactPort(fraction,width){
    if(!Number.isFinite(fraction)||fraction<=0||fraction>=1||!Number.isFinite(width)||width<0||this.wires.some(w=>fraction*w.lengthM-width/2<0||fraction*w.lengthM+width/2>w.lengthM))throw RangeError('contact footprint');
    if(fraction===this.contactFraction&&width===this.contactWidth)return;
    const weights=this.modes.map(m=>{const wire=this.wires[m.j];return this.helpers.spatialWeight(this.helpers.stringMode(wire,m.n),wire.lengthM,fraction*wire.lengthM,width);});
    this.modes.forEach((m,i)=>m.weight=weights[i]);this.contactFraction=fraction;this.contactWidth=width;
  }
  mobility(f){
    if(!Number.isFinite(f)||f<=0)throw new RangeError('frequency');
    const w=2*Math.PI*f;let re=this.kB-w*w*this.mB,im=w*this.cB;
    for(const m of this.modes){const ar=m.k-w*w*m.m,ai=w*m.c,br=-w*w*m.cross,bi=w*m.cc,den=ar*ar+ai*ai;if(den===0)throw new RangeError('singular undamped pole');const nr=br*br-bi*bi,ni=2*br*bi;re-=(nr*ar+ni*ai)/den;im-=(ni*ar-nr*ai)/den;}
    const den=re*re+im*im;return {fHz:f,real:w*im/den,imag:w*re/den,magnitude:w/Math.sqrt(den)};
  }
}




// F5.3 two physical polarizations and rotated passive bridge tensors; offline reference.
function rotatedTensor(a,b,angle){
  if(![a,b,angle].every(Number.isFinite)||a<0||b<0)throw new RangeError('tensor');
  const c=Math.cos(angle),s=Math.sin(angle);
  return {vv:a*c*c+b*s*s,hh:a*s*s+b*c*c,vh:(a-b)*c*s};
}

export class SpatialPolarizedBridge {
  constructor(wires,{sampleRate=192000,maxFrequencyHz=16000,massKg=.025,stiffness=[1e6,2e6],damping=[20,5],angleRad=.25,verticalLoss=[.4,.0002],horizontalLoss=[.2,.00012]}={},helpers){
    this.K=rotatedTensor(...stiffness,angleRad);this.C=rotatedTensor(...damping,angleRad);
    this.h=1/sampleRate;this.wires=wires;this.workJ=0;this.lossJ=0;this.bridgeLossJ=0;this.stringLossJ=0;
    const common={sampleRate,maxFrequencyHz,bridgeMassKg:massKg};
    this.vAxis=new SpatialMovingBridge(wires,{...common,bridgeK:this.K.vv,bridgeC:this.C.vv,sigma0:verticalLoss[0],sigma2:verticalLoss[1]},helpers);
    this.hAxis=new SpatialMovingBridge(wires,{...common,bridgeK:this.K.hh,bridgeC:this.C.hh,sigma0:horizontalLoss[0],sigma2:horizontalLoss[1]},helpers);
    const h=this.h;this.crossA=h*this.C.vh/2+h*h*this.K.vh/4;
    this.det=this.vAxis.schur*this.hAxis.schur-this.crossA*this.crossA;
    if(!(this.det>0&&Number.isFinite(this.det)))throw new RangeError('bridge Schur');
  }
  energy(){return this.vAxis.energy()+this.hAxis.energy()+this.K.vh*this.vAxis.b*this.hAxis.b;}
  wireEnergy(axis,j){return (axis==='v'?this.vAxis:this.hAxis).wireEnergy(j);}
  contactDisplacement(j){return this.vAxis.contactDisplacement(j);}
  predict(fv,fh,bv=0,bh=0){
    const h=this.h;
    const reduce=(a,f,b,other)=>{
      let rhs=a.mB*a.vb+h*(b+a.contactFraction*f.reduce((s,v)=>s+v,0)-a.kB*a.b-this.K.vh*other.b)/2;
      const rr=a.modes.map((m,i)=>{const v=m.m*a.v[i]+m.cross*a.vb+h*(m.weight*f[m.j]-m.k*a.x[i])/2;rhs+=m.cross*a.v[i]-m.B*v/m.A;return v;});
      return {rhs,rr};
    };
    const v=reduce(this.vAxis,fv,bv,this.hAxis),u=reduce(this.hAxis,fh,bh,this.vAxis);
    return {mv:(v.rhs*this.hAxis.schur-this.crossA*u.rhs)/this.det,mh:(u.rhs*this.vAxis.schur-this.crossA*v.rhs)/this.det,rv:v.rr,rh:u.rr};
  }
  freeContacts(){
    const zero=this.wires.map(()=>0),q=this.predict(zero,zero),a=this.vAxis,h=this.h;
    const y=this.wires.map((_,j)=>a.contactDisplacement(j)+a.contactFraction*h*q.mv);
    for(let i=0;i<a.modes.length;i++){const m=a.modes[i];y[m.j]+=h*m.weight*(q.rv[i]-m.B*q.mv)/m.A;}
    return y;
  }
  contactCompliance(){
    const a=this.vAxis,n=this.wires.length,d=Array(n).fill(0),t=Array(n).fill(a.contactFraction);
    for(const m of a.modes){d[m.j]+=m.weight*m.weight/m.A;t[m.j]-=m.B*m.weight/m.A;}
    return d.map((v,i)=>d.map((_,j)=>this.h*this.h/2*((i===j?v:0)+t[i]*t[j]*this.hAxis.schur/this.det)));
  }
  step(fv=this.wires.map(()=>0),fh=this.wires.map(()=>0),bv=0,bh=0){
    if(fv.length!==this.wires.length||fh.length!==this.wires.length||![...fv,...fh,bv,bh].every(Number.isFinite))throw new RangeError('forces');
    const {mv,mh}=this.predict(fv,fh,bv,bh),h=this.h,v=this.vAxis,u=this.hAxis;
    const crossV=-this.K.vh*(u.b+h*mh/2)-this.C.vh*mh,crossH=-this.K.vh*(v.b+h*mv/2)-this.C.vh*mv;
    const w0=v.workJ+u.workJ,d0=v.lossJ+u.lossJ,s0=v.stringLossJ+u.stringLossJ;
    v.step(fv,bv+crossV);u.step(fh,bh+crossH);
    this.workJ+=v.workJ+u.workJ-w0-h*(crossV*mv+crossH*mh);
    this.lossJ+=v.lossJ+u.lossJ-d0+2*h*this.C.vh*mv*mh;
    this.stringLossJ+=v.stringLossJ+u.stringLossJ-s0;
    this.bridgeLossJ+=h*(this.C.vv*mv*mv+2*this.C.vh*mv*mh+this.C.hh*mh*mh);
  }
  mobility(f){
    if(!Number.isFinite(f)||f<=0)throw new RangeError('frequency');
    const w=2*Math.PI*f;
    const diag=a=>{let re=a.kB-w*w*a.mB,im=w*a.cB;
      for(const m of a.modes){const ar=m.k-w*w*m.m,ai=w*m.c,br=-w*w*m.cross,bi=w*m.cc,den=ar*ar+ai*ai;if(den===0)throw new RangeError('singular');const nr=br*br-bi*bi,ni=2*br*bi;re-=(nr*ar+ni*ai)/den;im-=(ni*ar-nr*ai)/den;}return [re,im];};
    const mul=([a,b],[c,d])=>[a*c-b*d,a*d+b*c],sub=([a,b],[c,d])=>[a-c,b-d],div=([a,b],[c,d])=>[(a*c+b*d)/(c*c+d*d),(b*c-a*d)/(c*c+d*d)];
    const v=diag(this.vAxis),u=diag(this.hAxis),c=[this.K.vh,w*this.C.vh],det=sub(mul(v,u),mul(c,c));
    const vv=div(mul([0,w],u),det),hh=div(mul([0,w],v),det),vh=div(mul([0,-w],c),det);
    return {f,vv,hh,vh,realDet:vv[0]*hh[0]-vh[0]*vh[0],crossMagnitude:Math.hypot(...vh)};
  }
}

