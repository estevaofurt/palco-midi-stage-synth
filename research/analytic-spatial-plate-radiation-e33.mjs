/**
 * E3.3: causal, sample-free Rayleigh radiation from FULLY DISTRIBUTED
 * plate modal velocities, never the local point-bridge velocity.
 *
 * Pressure for rigid infinite baffle:
 *   p(r,t) = rho/(2*pi) integral_S [ d/dt v_s(r',t-|r-r'|/c) / |r-r'| ] dS
 * v_s(u,v)=Σ_j qdot_j sin(mx_j*pi*u) sin(my_j*pi*v).
 *
 * A finite rectangular soundboard, mode shapes and far-field listener are
 * analytic hypothetical geometry. The mechanical E3.3 qdot units are not
 * acoustically calibrated in m/s. Therefore this output is RELATIVE
 * pressure only. No measured IR, convolution, piano PCM, samples or room.
 */
const TAU=2*Math.PI;
const bounded=(v,a,b)=>Number.isFinite(v)&&v>=a&&v<=b;
export class AnalyticSpatialPlateRadiatorE33 {
 constructor({
  sampleRate=48000,shapes=[[1,1],[2,1],[1,2],[2,2],[3,1],[1,3],[3,2],[2,3]],
  columns=8,rows=6,
  plateWidthM=1.22,plateHeightM=.92,
  rho=1.204,soundSpeed=343,
  microphones=[{x:-.38,y:.14,z:1.35},{x:.38,y:.14,z:1.35}]
 }={}){
  if(!Number.isInteger(sampleRate)||sampleRate<22050||sampleRate>96000||
     !Array.isArray(shapes)||shapes.length<1||shapes.length>16||
     shapes.some(x=>!Array.isArray(x)||x.length!==2||
      x.some(y=>!Number.isInteger(y)||y<1||y>6))||
     !Number.isInteger(columns)||columns<2||columns>24||
     !Number.isInteger(rows)||rows<2||rows>24||
     columns*rows>192||
     !bounded(plateWidthM,.1,2.5)||!bounded(plateHeightM,.1,2.5)||
     !bounded(rho,.8,1.6)||!bounded(soundSpeed,300,370)||
     !Array.isArray(microphones)||microphones.length!==2||
     microphones.some(p=>!p||!bounded(p.x,-5,5)||
      !bounded(p.y,-5,5)||!bounded(p.z,.25,15)))
    throw new RangeError('invalid spatial plate radiation');
  this.sampleRate=sampleRate;this.modeCount=shapes.length;
  this.patchCount=columns*rows;this.coefficients=new Float64Array(2*this.patchCount*this.modeCount);
  this.delays=new Uint16Array(2*this.patchCount);
  this.fractions=new Float64Array(2*this.patchCount);
  const area=plateWidthM*plateHeightM/this.patchCount;
  let maxDelay=0;
  for(let ear=0;ear<2;ear++){
   const mic=microphones[ear];
   for(let row=0;row<rows;row++)for(let col=0;col<columns;col++){
    const u=(col+.5)/columns,v=(row+.5)/rows,
      px=(u-.5)*plateWidthM,py=(v-.5)*plateHeightM;
    const radius=Math.hypot(mic.x-px,mic.y-py,mic.z);
    const time=radius*sampleRate/soundSpeed;
    const delay=Math.floor(time);
    const patch=ear*this.patchCount+row*columns+col;
    this.delays[patch]=delay;
    this.fractions[patch]=time-delay;
    maxDelay=Math.max(maxDelay,delay);
    const gain=rho*area/(TAU*radius);
    for(let mode=0;mode<this.modeCount;mode++){
     const [mx,my]=shapes[mode];
     const phi=Math.sin(mx*Math.PI*u)*Math.sin(my*Math.PI*v);
     this.coefficients[patch*this.modeCount+mode]=gain*phi;
    }
   }
  }
  this.ringLength=maxDelay+3;
  this.acceleration=new Float64Array(this.modeCount*this.ringLength);
  this.lastVelocity=new Float64Array(this.modeCount);
  this.cursor=0;this.left=0;this.right=0;
 }
 reset(){
  this.acceleration.fill(0);this.lastVelocity.fill(0);
  this.cursor=0;this.left=0;this.right=0;
 }
 step(velocities){
  if(!(velocities instanceof Float64Array||velocities instanceof Float32Array)||
     velocities.length!==this.modeCount)
   throw new RangeError('invalid plate velocity modes');
  const count=this.modeCount,len=this.ringLength,head=this.cursor;
  for(let j=0;j<count;j++){
   const value=velocities[j];
   if(!Number.isFinite(value))throw new TypeError('nonfinite panel velocity');
   this.acceleration[j*len+head]=(value-this.lastVelocity[j])*this.sampleRate;
   this.lastVelocity[j]=value;
  }
  let left=0,right=0;
  for(let patch=0;patch<2*this.patchCount;patch++){
   let time=head-this.delays[patch];
   if(time<0)time+=len;
   const prior=time===0?len-1:time-1;
   const frac=this.fractions[patch];
   let pressure=0;
   for(let j=0;j<count;j++){
    const base=j*len;
    const accel=(1-frac)*this.acceleration[base+time]+
      frac*this.acceleration[base+prior];
    pressure+=this.coefficients[patch*count+j]*accel;
   }
   if(patch<this.patchCount)left+=pressure;
   else right+=pressure;
  }
  this.cursor=head===len-1?0:head+1;
  this.left=left;this.right=right;
  return left;
 }
}
