// F6.1 uniform rectangular simply supported thin orthotropic plate, no ribs, no acoustic radiation. SI.
export function plateDesign({lengthM=1.4,widthM=1.1,thicknessM=.008,densityKgM3=430,ExPa=11e9,EyPa=.8e9,GxyPa=.65e9,nuXY=.3}={}){
  if(![lengthM,widthM,thicknessM,densityKgM3,ExPa,EyPa,GxyPa].every(x=>Number.isFinite(x)&&x>0)||!Number.isFinite(nuXY)||nuXY<0)throw new RangeError('plate parameters');
  const nuYX=nuXY*EyPa/ExPa,den=1-nuXY*nuYX;if(den<=0)throw new RangeError('nonpositive elastic tensor');
  const h3=thicknessM**3/12,D11=ExPa*h3/den,D22=EyPa*h3/den,D12=nuXY*D22,D66=GxyPa*h3,areaM2=lengthM*widthM,arealMass=densityKgM3*thicknessM;
  if(![D11,D22,D66,areaM2,arealMass].every(v=>Number.isFinite(v)&&v>0)||!Number.isFinite(D12))throw new RangeError('plate scale');
  return {lengthM,widthM,thicknessM,densityKgM3,ExPa,EyPa,GxyPa,nuXY,nuYX,D11,D22,D12,D66,areaM2,arealMass,massKg:areaM2*arealMass};
}

export function plateMode(p,m,n){
  if(![m,n].every(x=>Number.isInteger(x)&&x>0))throw new RangeError('mode index');
  const kx=m*Math.PI/p.lengthM,ky=n*Math.PI/p.widthM,omega2=(p.D11*kx**4+2*(p.D12+2*p.D66)*kx*kx*ky*ky+p.D22*ky**4)/p.arealMass,massKg=p.massKg/4;
  return {m,n,kx,ky,massKg,frequencyHz:Math.sqrt(omega2)/(2*Math.PI),stiffnessNPerM:massKg*omega2};
}

export function plateModes(p,cutoffHz){
  if(!Number.isFinite(cutoffHz)||cutoffHz<=0)throw new RangeError('cutoff');
  const mx=Math.ceil(p.lengthM/Math.PI*(p.arealMass*(2*Math.PI*cutoffHz)**2/p.D11)**.25),ny=Math.ceil(p.widthM/Math.PI*(p.arealMass*(2*Math.PI*cutoffHz)**2/p.D22)**.25);
  if(mx*ny>200000)throw new RangeError('reference basis too large');
  const modes=[];for(let m=1;m<=mx;m++)for(let n=1;n<=ny;n++){const q=plateMode(p,m,n);if(q.frequencyHz<cutoffHz)modes.push(q);}
  return modes.sort((a,b)=>a.frequencyHz-b.frequencyHz||a.m-b.m||a.n-b.n);
}

export function patchWeight(p,q,{xM,yM,dxM=0,dyM=0}){
  if(![xM,yM,dxM,dyM].every(Number.isFinite)||dxM<0||dyM<0||xM-dxM/2<0||xM+dxM/2>p.lengthM||yM-dyM/2<0||yM+dyM/2>p.widthM)throw new RangeError('patch outside plate');
  if(xM===0||xM===p.lengthM||yM===0||yM===p.widthM)return 0;
  const sinc=x=>Math.abs(x)<1e-8?1-x*x/6:Math.sin(x)/x;
  return Math.sin(q.kx*xM)*Math.sin(q.ky*yM)*sinc(q.kx*dxM/2)*sinc(q.ky*dyM/2);
}

export class OrthotropicPlate {
  constructor(p,{sampleRate=48000,cutoffHz=4000,loss0=2,lossSlope=.0005}={},coefficients){
    if(!Number.isFinite(sampleRate)||sampleRate<=0||![loss0,lossSlope].every(x=>Number.isFinite(x)&&x>=0))throw new RangeError('plate integration parameters');
    this.p=p;this.h=1/sampleRate;this.modes=plateModes(p,Math.min(cutoffHz,.4*sampleRate)).map(q=>{const sigma=loss0+lossSlope*2*Math.PI*q.frequencyHz,c=2*q.massKg*sigma;return {...q,sigma,c,coeff:coefficients({massKg:q.massKg,frequencyHz:q.frequencyHz,dampingNsM:c,dt:this.h})};});
    if(!this.modes.length)throw new RangeError('empty basis');
    this.x=new Float64Array(this.modes.length);this.v=new Float64Array(this.modes.length);this.workJ=0;this.lossJ=0;
  }
  weights(patch){return Float64Array.from(this.modes,q=>patchWeight(this.p,q,patch));}
  projection(w,state=this.x){if(w.length!==this.modes.length||state.length!==w.length)throw new RangeError('projection');let y=0;for(let i=0;i<w.length;i++)y+=w[i]*state[i];return y;}
  energy(){return this.modes.reduce((s,q,i)=>s+.5*(q.massKg*this.v[i]**2+q.stiffnessNPerM*this.x[i]**2),0);}
  step(ports=[]){
    if(ports.some(({weights,forceN})=>weights.length!==this.modes.length||!Number.isFinite(forceN)||Array.from(weights).some(w=>!Number.isFinite(w))))throw new RangeError('ports');
    let work=0,loss=0;
    for(let i=0;i<this.modes.length;i++){const p=this.modes[i].coeff,x=this.x[i],v=this.v[i],f=ports.reduce((s,q)=>s+q.weights[i]*q.forceN,0),xn=p.A*x+p.S*v+p.G*f,vn=p.H*x+p.D*v+p.J*f;if(!Number.isFinite(xn)||!Number.isFinite(vn))throw new RangeError('state');const w=f*(xn-x);work+=w;loss+=w+.5*(p.massKg*(v*v-vn*vn)+p.k*(x*x-xn*xn));this.x[i]=xn;this.v[i]=vn;}
    this.workJ+=work;this.lossJ+=loss;
  }
  mobility(f,wa,wb=wa){
    if(!Number.isFinite(f)||f<=0||wa.length!==this.modes.length||wb.length!==wa.length)throw new RangeError('mobility');
    const w=2*Math.PI*f;let real=0,imag=0;
    for(let i=0;i<wa.length;i++){const q=this.modes[i],a=q.stiffnessNPerM-q.massKg*w*w,b=w*q.c,d=a*a+b*b;if(d===0)throw new RangeError('undamped pole');real+=wa[i]*wb[i]*w*b/d;imag+=wa[i]*wb[i]*w*a/d;}
    return {real,imag,magnitude:Math.hypot(real,imag)};
  }
}
