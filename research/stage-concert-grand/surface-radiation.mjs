// F7.1: one-way Rayleigh radiation from prescribed normal acceleration in an infinite rigid baffle. No fluid loading or room.
export function radiationGrid(p,listener,{nx=64,ny=48,rho=1.204,c=343}={}){
 if(![p.lengthM,p.widthM,rho,c,listener.z].every(v=>Number.isFinite(v)&&v>0)||![listener.x,listener.y].every(Number.isFinite)||![nx,ny].every(v=>Number.isInteger(v)&&v>=2&&v<=512))throw new RangeError('radiation geometry');
 const dx=p.lengthM/nx,dy=p.widthM/ny,points=[];
 for(let i=0;i<nx;i++)for(let j=0;j<ny;j++){
  const x=(i+.5)*dx,y=(j+.5)*dy,R=Math.hypot(listener.x-x,listener.y-y,listener.z);
  points.push({x,y,delay:R/c,weight:rho*dx*dy/(2*Math.PI*R)});
 }
 return points;
}

export function surfaceShape(mode,x,y){return mode.components.reduce((s,q)=>s+q.coefficient*Math.sin(q.kx*x)*Math.sin(q.ky*y),0);}

export function harmonicRadiation(grid,shape,f){
 if(!Number.isFinite(f)||f<0)throw new RangeError('frequency');
 let re=0,im=0;for(const q of grid){const a=q.weight*shape(q.x,q.y),phase=2*Math.PI*f*q.delay;re+=a*Math.cos(phase);im-=a*Math.sin(phase);}
 return {re,im,magnitude:Math.hypot(re,im)};
}

export function radiationKernel(grid,shape,rate){
 if(!Number.isFinite(rate)||rate<=0)throw new RangeError('rate');
 let min=Infinity,max=0;for(const q of grid){min=Math.min(min,Math.floor(q.delay*rate));max=Math.max(max,Math.ceil(q.delay*rate));}
 if(!Number.isSafeInteger(max)||max>rate*10||max-min>1000000)throw new RangeError('delay span');
 const taps=new Float64Array(max-min+1);
 for(const q of grid){const t=q.delay*rate,i=Math.floor(t),f=t-i,a=q.weight*shape(q.x,q.y);taps[i-min]+=a*(1-f);if(f>0)taps[i-min+1]+=a*f;}
 return {offset:min,taps,rate};
}

export function kernelResponse(k,f){
 let re=0,im=0;for(let i=0;i<k.taps.length;i++){const t=2*Math.PI*f*(k.offset+i)/k.rate;re+=k.taps[i]*Math.cos(t);im-=k.taps[i]*Math.sin(t);}return {re,im,magnitude:Math.hypot(re,im)};
}

export class SurfaceRadiator{
 constructor(p,modes,listener,{rate=96000,...options}={}){
  const grid=radiationGrid(p,listener,options);this.kernels=modes.map(m=>radiationKernel(grid,(x,y)=>surfaceShape(m,x,y),rate));
  if(!this.kernels.length)throw new RangeError('empty modes');
  this.size=Math.max(...this.kernels.map(k=>k.offset+k.taps.length));this.hist=this.kernels.map(()=>new Float64Array(this.size));this.index=0;
 }
 step(acceleration){
  if(acceleration.length!==this.kernels.length||!Array.from(acceleration).every(Number.isFinite))throw new RangeError('modal acceleration');
  let pressure=0;for(let m=0;m<this.kernels.length;m++){const k=this.kernels[m],h=this.hist[m];h[this.index]=acceleration[m];for(let i=0;i<k.taps.length;i++)pressure+=k.taps[i]*h[(this.index-k.offset-i+this.size)%this.size];}
  this.index=(this.index+1)%this.size;return pressure;
 }
}
