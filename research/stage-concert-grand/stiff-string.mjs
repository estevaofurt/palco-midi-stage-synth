// F3.1: simply supported stiff string, one transverse polarization, physical SI modal coordinates. Not acoustic pressure or piano engine.
export function stringMode(wire,n){
  if(!Number.isInteger(n)||n<1||n>16384)throw new RangeError('mode index');
  const {lengthM:L,tensionN:T,linearDensityKgM:mu,EI}=wire;
  if(![L,T,mu].every(v=>Number.isFinite(v)&&v>0)||!Number.isFinite(EI)||EI<0)throw new RangeError('invalid wire');
  const waveNumber=n*Math.PI/L,massKg=mu*L/2;
  const tensionStiffness=T*L*waveNumber**2/2,bendingStiffness=EI*L*waveNumber**4/2;
  const stiffnessNPerM=tensionStiffness+bendingStiffness;
  const frequencyHz=Math.sqrt(stiffnessNPerM/massKg)/(2*Math.PI);
  const phaseSpeedMps=Math.sqrt((T+EI*waveNumber**2)/mu),groupSpeedMps=(T+2*EI*waveNumber**2)/(mu*phaseSpeedMps);
  if(![massKg,stiffnessNPerM,frequencyHz,phaseSpeedMps,groupSpeedMps].every(v=>Number.isFinite(v)&&v>0))throw new RangeError('invalid mode');
  return {n,waveNumber,massKg,frequencyHz,stiffnessNPerM,tensionStiffness,bendingStiffness,phaseSpeedMps,groupSpeedMps};
}

export function spatialWeight(mode,L,centerM,widthM=0){
  if(!Number.isFinite(L)||L<=0||![centerM,widthM].every(Number.isFinite)||widthM<0||centerM-widthM/2<0||centerM+widthM/2>L)throw new RangeError('footprint outside string');
  if(centerM===0||centerM===L)return 0;
  const z=mode.waveNumber*widthM/2;
  return Math.sin(mode.waveNumber*centerM)*(Math.abs(z)<1e-8?1-z*z/6:Math.sin(z)/z);
}

export class StiffString {
  constructor(wire,{sampleRate=48000,maxFrequencyHz=16000,maxModes=256,sigma0PerS=.4,sigma2M2PerS=.0002}={},coefficients){
    if(!Number.isFinite(sampleRate)||sampleRate<=0||!Number.isFinite(maxFrequencyHz)||maxFrequencyHz<=0||!Number.isInteger(maxModes)||maxModes<1||maxModes>16384||![sigma0PerS,sigma2M2PerS].every(v=>Number.isFinite(v)&&v>=0))throw new RangeError('invalid string setup');
    this.wire={...wire};this.dt=1/sampleRate;this.cutoffHz=Math.min(maxFrequencyHz,.4*sampleRate);
    this.modes=[];
    for(let n=1;n<=maxModes;n++){
      const mode=stringMode(wire,n);
      if(mode.frequencyHz>=this.cutoffHz)break;
      const sigma=sigma0PerS+sigma2M2PerS*mode.waveNumber**2,dampingNsM=2*mode.massKg*sigma;
      this.modes.push({...mode,sigma,dampingNsM,coeff:coefficients({massKg:mode.massKg,frequencyHz:mode.frequencyHz,dampingNsM,dt:this.dt})});
    }
    if(!this.modes.length)throw new RangeError('no resolved modes');
    this.x=new Float64Array(this.modes.length);this.v=new Float64Array(this.modes.length);
    this.workJ=0;this.lossJ=0;
  }
  weights(centerM,widthM=0){return Float64Array.from(this.modes,m=>spatialWeight(m,this.wire.lengthM,centerM,widthM));}
  projection(weights,state=this.x){if(weights.length!==this.modes.length||state.length!==weights.length)throw new RangeError('projection size');let v=0;for(let i=0;i<weights.length;i++){if(!Number.isFinite(weights[i])||!Number.isFinite(state[i]))throw new RangeError('projection value');v+=weights[i]*state[i];}return v;}
  energy(){let e=0;for(let i=0;i<this.modes.length;i++){const m=this.modes[i];e+=.5*(m.massKg*this.v[i]**2+m.stiffnessNPerM*this.x[i]**2);}return e;}
  step(weights,forceN=0){
    if(weights.length!==this.modes.length||!Number.isFinite(forceN)||Array.from(weights).some(w=>!Number.isFinite(w)))throw new RangeError('force projection');
    let work=0,loss=0;
    for(let i=0;i<this.modes.length;i++){
      const p=this.modes[i].coeff,x=this.x[i],v=this.v[i],f=weights[i]*forceN;
      const xn=p.A*x+p.S*v+p.G*f,vn=p.H*x+p.D*v+p.J*f;
      if(!Number.isFinite(xn)||!Number.isFinite(vn))throw new RangeError('nonfinite state');
      const w=f*(xn-x);work+=w;loss+=w+.5*(p.massKg*(v*v-vn*vn)+p.k*(x*x-xn*xn));this.x[i]=xn;this.v[i]=vn;
    }
    this.workJ+=work;this.lossJ+=loss;
  }
  rightSupportForceN(){
    // Force exerted on ideal pinned support by the string: -T*y_x(L)+EI*y_xxx(L).
    let f=0;for(let i=0;i<this.modes.length;i++){const m=this.modes[i],k=m.waveNumber;f-=(-1)**m.n*(this.wire.tensionN*k+this.wire.EI*k**3)*this.x[i];}return f;
  }
}

export function staticCompliance(wire,centerM,widthM,count){
  if(!Number.isInteger(count)||count<1||count>16384)throw new RangeError('count');
  let c=0;for(let n=1;n<=count;n++){const m=stringMode(wire,n),w=spatialWeight(m,wire.lengthM,centerM,widthM);c+=w*w/m.stiffnessNPerM;}return c;
}
