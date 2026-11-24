// F5.1: energy-consistent moving simply supported boundary, one polarization; midpoint reference, not real-time engine.
export class MovingBridge {
  // Galerkin lifting: y_i(x)=b*x/L_i + sum q_in sin(n*pi*x/L_i).
  constructor(wires,{sampleRate=192000,maxFrequencyHz=16000,bridgeMassKg=.025,bridgeK=1e6,bridgeC=20,sigma0=.4,sigma2=.0002}={},helpers){
    if(!Array.isArray(wires)||!wires.length||wires.length>88||![sampleRate,maxFrequencyHz,bridgeMassKg].every(v=>Number.isFinite(v)&&v>0)||![bridgeK,bridgeC,sigma0,sigma2].every(v=>Number.isFinite(v)&&v>=0))throw new RangeError('bridge parameters');
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
    const fB=bridgeForce+.13*Array.from(forces).reduce((a,b)=>a+b,0);
    let rhsB=this.mB*v0+h*(fB-this.kB*b0)/2;
    for(let i=0;i<this.modes.length;i++){const m=this.modes[i];rhsB+=m.cross*this.v[i];this.rhs[i]=m.m*this.v[i]+m.cross*v0+h*(m.weight*forces[m.j]-m.k*this.x[i])/2;rhsB-=m.B*this.rhs[i]/m.A;}
    const vbMid=rhsB/this.schur;
    let d=this.cB*vbMid**2,work=fB*vbMid;
    for(let i=0;i<this.modes.length;i++){const m=this.modes[i],v=(this.rhs[i]-m.B*vbMid)/m.A;this.mid[i]=v;d+=m.c*v*v+2*m.cc*v*vbMid;work+=m.weight*forces[m.j]*v;this.x[i]+=h*v;this.v[i]=2*v-this.v[i];}
    this.b+=h*vbMid;this.vb=2*vbMid-v0;this.workJ+=h*work;this.lossJ+=h*d;this.bridgeLossJ+=h*this.bridgeC*vbMid**2;this.stringLossJ+=h*(d-this.bridgeC*vbMid**2);
  }
  contactDisplacement(j){let x=.13*this.b;for(let i=0;i<this.modes.length;i++)if(this.modes[i].j===j)x+=this.modes[i].weight*this.x[i];return x;}
  mobility(f){
    if(!Number.isFinite(f)||f<=0)throw new RangeError('frequency');
    const w=2*Math.PI*f;let re=this.kB-w*w*this.mB,im=w*this.cB;
    for(const m of this.modes){const ar=m.k-w*w*m.m,ai=w*m.c,br=-w*w*m.cross,bi=w*m.cc,den=ar*ar+ai*ai;if(den===0)throw new RangeError('singular undamped pole');const nr=br*br-bi*bi,ni=2*br*bi;re-=(nr*ar+ni*ai)/den;im-=(ni*ar-nr*ai)/den;}
    const den=re*re+im*im;return {fHz:f,real:w*im/den,imag:w*re/den,magnitude:w/Math.sqrt(den)};
  }
}
