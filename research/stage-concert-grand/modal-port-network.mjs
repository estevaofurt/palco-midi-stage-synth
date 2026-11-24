// F2.3: passive fixed-coefficient modal ports, offline; sparse mode-port weights and pre-factored small SPD system.
export class ModalPortNetwork {
  constructor(modes,ports,coefficients){
    if(!Array.isArray(modes)||!modes.length||modes.length>16384||!Array.isArray(ports)||ports.length>128)throw new RangeError('dimensions');
    this.n=modes.length;this.dt=modes[0].dt;this.modes=modes.map(m=>{if(m.dt!==this.dt)throw new RangeError('shared dt required');return coefficients(m);});
    this.ports=[];this.byMode=Array.from({length:this.n},()=>[]);
    for(const {weights,k,c} of ports){
      if(![k,c].every(v=>Number.isFinite(v)&&v>=0)||!Array.isArray(weights)||!weights.length)throw new RangeError('invalid port');
      const seen=new Set();
      const w=weights.map(({i,b})=>{if(!Number.isInteger(i)||i<0||i>=this.n||seen.has(i)||!Number.isFinite(b)||b===0)throw new RangeError('invalid port weight');seen.add(i);return {i,b};});
      if(k===0&&c===0)continue;
      const d=k/2+c/this.dt,s=Math.sqrt(d);
      if(!Number.isFinite(s)||s<=0)throw new RangeError('port scale');
      const j=this.ports.length;this.ports.push({weights:w,k,c,s,ratio:(k/2-c/this.dt)/s});
      for(const {i,b} of w)this.byMode[i].push({j,b:b*s});
    }
    const p=this.p=this.ports.length;
    this.matrix=new Float64Array(p*p);for(let j=0;j<p;j++)this.matrix[j*p+j]=1;
    for(let i=0;i<this.n;i++)for(const a of this.byMode[i])for(const b of this.byMode[i])this.matrix[a.j*p+b.j]+=this.modes[i].G*a.b*b.b;
    this.L=new Float64Array(p*p);
    for(let i=0;i<p;i++)for(let j=0;j<=i;j++){
      let v=this.matrix[i*p+j];for(let k=0;k<j;k++)v-=this.L[i*p+k]*this.L[j*p+k];
      if(i===j){if(!Number.isFinite(v)||v<=0)throw new RangeError('nonpositive factor');this.L[i*p+j]=Math.sqrt(v);}
      else this.L[i*p+j]=v/this.L[j*p+j];
    }
    this.x=new Float64Array(this.n);this.v=new Float64Array(this.n);this.force=new Float64Array(this.n);this.freeX=new Float64Array(this.n);this.freeV=new Float64Array(this.n);
    this.r0=new Float64Array(p);this.rhs=new Float64Array(p);this.tmp=new Float64Array(p);this.z=new Float64Array(p);
    this.workJ=0;this.localLossJ=0;this.portLossJ=0;
    this.conditionUpper=1;
    for(let i=0;i<p;i++){let sum=0;for(let j=0;j<p;j++)sum+=Math.abs(this.matrix[i*p+j]);this.conditionUpper=Math.max(this.conditionUpper,sum);}
  }
  energy(){
    let e=0;for(let i=0;i<this.n;i++){const m=this.modes[i];e+=.5*(m.massKg*this.v[i]**2+m.k*this.x[i]**2);}
    for(const p of this.ports){let r=0;for(const {i,b} of p.weights)r+=b*this.x[i];e+=.5*p.k*r*r;}
    return e;
  }
  step(){
    const n=this.n,p=this.p,h=this.dt;
    for(let i=0;i<n;i++){const m=this.modes[i],x=this.x[i],v=this.v[i],f=this.force[i];if(!Number.isFinite(f)||!Number.isFinite(x)||!Number.isFinite(v))throw new RangeError('nonfinite input');this.freeX[i]=m.A*x+m.S*v+m.G*f;this.freeV[i]=m.H*x+m.D*v+m.J*f;}
    for(let j=0;j<p;j++){const port=this.ports[j];let r=0,rf=0;for(const {i,b} of port.weights){r+=b*this.x[i];rf+=b*this.freeX[i];}this.r0[j]=r;this.rhs[j]=port.s*rf+port.ratio*r;}
    for(let i=0;i<p;i++){let v=this.rhs[i];for(let j=0;j<i;j++)v-=this.L[i*p+j]*this.tmp[j];this.tmp[i]=v/this.L[i*p+i];}
    for(let i=p-1;i>=0;i--){let v=this.tmp[i];for(let j=i+1;j<p;j++)v-=this.L[j*p+i]*this.z[j];this.z[i]=v/this.L[i*p+i];}
    let work=0,local=0,edge=0;
    for(let i=0;i<n;i++){const m=this.modes[i],x=this.x[i],v=this.v[i];let internal=0;for(const {j,b} of this.byMode[i])internal-=b*this.z[j];
      const xn=this.freeX[i]+m.G*internal,vn=this.freeV[i]+m.J*internal,dx=xn-x;
      if(!Number.isFinite(xn)||!Number.isFinite(vn))throw new RangeError('nonfinite state');
      work+=this.force[i]*dx;local+=(this.force[i]+internal)*dx+.5*(m.massKg*(v*v-vn*vn)+m.k*(x*x-xn*xn));
      this.x[i]=xn;this.v[i]=vn;
    }
    for(let j=0;j<p;j++){const port=this.ports[j];let r=0;for(const {i,b} of port.weights)r+=b*this.x[i];edge+=port.c*(r-this.r0[j])**2/h;}
    this.workJ+=work;this.localLossJ+=local;this.portLossJ+=edge;
  }
}
