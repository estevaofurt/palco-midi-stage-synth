/**
 * E2.9 — SAMPLE-FREE ANALYTIC ACOUSTIC RADIATION (RESEARCH ONLY).
 *
 * Rayleigh's first integral for a velocity-prescribed planar surface in an
 * infinite rigid baffle, integrated by midpoint quadrature:
 *
 * p(r,t) ~= (rho / 2π) Σ [ ΔA_i / |r-r_i| *
 *                  d(v_surface_i)/dt (t-|r-r_i|/c) ]
 *
 * The two surface mode shapes are ORIGINAL analytic functions:
 * φ0(x,y)=sin(πx/L)sin(πy/W) and φ1(x,y)=sin(2πx/L)sin(πy/W).
 * v_surface = mode0*φ0 + mode1*φ1.
 *
 * No recorded notes, soundfont, convolution IR, frequency EQ or reverb.
 * Delay is geometric (r/c), not a fitted filter. Area, shape, and radiation
 * directions are NOT identified from a real soundboard; modal amplitudes from
 * SharedPassiveModalPiano are GENERALIZED, not calibrated in m/s. Thus feeding
 * that model yields Pa-shaped RELATIVE output, NOT physically calibrated Pa.
 *
 * The one-way Rayleigh radiation does NOT add acoustic loading back into
 * the mechanical matrix, nor account for non-rigid baffle, rim, back side or
 * room. Sample-free does NOT mean acoustically realistic or product-ready.
 *
 * step() allocates no objects or arrays; call it after each mechanical step.
 */

const TWO_PI=2*Math.PI;
const finiteBetween=(n,lo,hi)=>Number.isFinite(n)&&n>=lo&&n<=hi;
const finitePoint=p=>p&&typeof p==='object'&&
 finiteBetween(p.x,-5,5)&&finiteBetween(p.y,-5,5)&&
 finiteBetween(p.z,.25,15);

export class AnalyticSoundboardRadiator {
 constructor({
  sampleRate=48000,airDensityKgM3=1.204,soundSpeedMps=343,
  plateWidthM=1.22,plateHeightM=.92,columns=8,rows=6,
  microphoneLeft={x:-.38,y:.14,z:1.35},
  microphoneRight={x:.38,y:.14,z:1.35}
 }={}){
  if(!Number.isInteger(sampleRate)||sampleRate<22050||sampleRate>192000||
     !finiteBetween(airDensityKgM3,.8,1.6)||
     !finiteBetween(soundSpeedMps,300,370)||
     !finiteBetween(plateWidthM,.08,2.5)||
     !finiteBetween(plateHeightM,.08,2.5)||
     !Number.isInteger(columns)||columns<2||columns>24||
     !Number.isInteger(rows)||rows<2||rows>24||
     columns*rows>256||!finitePoint(microphoneLeft)||
     !finitePoint(microphoneRight))
   throw new RangeError('invalid physically parameterized baffled plate');
  this.sampleRate=sampleRate;this.airDensityKgM3=airDensityKgM3;
  this.soundSpeedMps=soundSpeedMps;
  this.plateWidthM=plateWidthM;this.plateHeightM=plateHeightM;
  this.columns=columns;this.rows=rows;
  this.patchCount=rows*columns;
  // Per-ear-per-patch area/r, delay and analytic modal shape coefficients.
  const coeff0=[],coeff1=[],delays=[],frac=[],ear=[];
  const patchArea=plateWidthM*plateHeightM/this.patchCount;
  const mics=[microphoneLeft,microphoneRight];
  for(let e=0;e<2;e++){
   const mic=mics[e];
   for(let row=0;row<rows;row++)for(let col=0;col<columns;col++){
    const u=(col+.5)/columns,v=(row+.5)/rows;
    const px=(u-.5)*plateWidthM,py=(v-.5)*plateHeightM;
    const radius=Math.hypot(mic.x-px,mic.y-py,mic.z);
    const gain=airDensityKgM3*patchArea/(TWO_PI*radius);
    const t=radius*sampleRate/soundSpeedMps;
    const integralDelay=Math.floor(t);
    coeff0.push(gain*Math.sin(Math.PI*u)*Math.sin(Math.PI*v));
    coeff1.push(gain*Math.sin(2*Math.PI*u)*Math.sin(Math.PI*v));
    delays.push(integralDelay);frac.push(t-integralDelay);ear.push(e);
   }
  }
  const maxDelay=Math.max(...delays);
  this.ringLength=maxDelay+3;
  this.acc0=new Float64Array(this.ringLength);
  this.acc1=new Float64Array(this.ringLength);
  this.coeff0=Float64Array.from(coeff0);
  this.coeff1=Float64Array.from(coeff1);
  this.delays=Uint16Array.from(delays);
  this.fractions=Float64Array.from(frac);
  this.ears=Uint8Array.from(ear);
  this.cursor=0;this.previous0=0;this.previous1=0;
  this.left=0;this.right=0;this.samples=0;
 }
 reset(){
  this.acc0.fill(0);this.acc1.fill(0);
  this.cursor=0;this.previous0=0;this.previous1=0;
  this.left=0;this.right=0;this.samples=0;
 }
 /** mode0/mode1 are surface modal velocities in m/s IF calibrated.
  * The E2.3 generalized mechanical state is explicitly UNCALIBRATED.
  */
 step(mode0,mode1){
  if(!Number.isFinite(mode0)||!Number.isFinite(mode1))
   throw new TypeError('nonfinite surface mode velocity');
  const a0=(mode0-this.previous0)*this.sampleRate;
  const a1=(mode1-this.previous1)*this.sampleRate;
  this.previous0=mode0;this.previous1=mode1;
  const len=this.ringLength,head=this.cursor;
  this.acc0[head]=a0;this.acc1[head]=a1;
  let left=0,right=0;
  for(let i=0;i<this.coeff0.length;i++){
   let index=head-this.delays[i];
   if(index<0)index+=len;
   const prev=index===0?len-1:index-1;
   const frac=this.fractions[i],remain=1-frac;
   const v0=remain*this.acc0[index]+frac*this.acc0[prev];
   const v1=remain*this.acc1[index]+frac*this.acc1[prev];
   const sum=this.coeff0[i]*v0+this.coeff1[i]*v1;
   if(this.ears[i]===0)left+=sum;else right+=sum;
  }
  this.left=left;this.right=right;
  this.cursor=head===len-1?0:head+1;
  this.samples++;
  return left;
 }
}

export function encodeRelativeStereoWav16(left,right,sampleRate=48000){
 if(!(left instanceof Float64Array||left instanceof Float32Array)||
    !(right instanceof Float64Array||right instanceof Float32Array)||
    left.length!==right.length||left.length<1||
    !Number.isInteger(sampleRate)||sampleRate<22050||sampleRate>192000||
    left.length>sampleRate*30)
  throw new RangeError('invalid physical-only stereo signal');
 let peak=0;
 for(let i=0;i<left.length;i++){
  if(!Number.isFinite(left[i])||!Number.isFinite(right[i]))
   throw new TypeError('nonfinite physical acoustic proxy');
  peak=Math.max(peak,Math.abs(left[i]),Math.abs(right[i]));
 }
 if(!(peak>0))throw new RangeError('silent physical radiation');
 const wav=Buffer.alloc(44+left.length*4);
 wav.write('RIFF',0);wav.writeUInt32LE(wav.length-8,4);
 wav.write('WAVE',8);wav.write('fmt ',12);
 wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);
 wav.writeUInt16LE(2,22);wav.writeUInt32LE(sampleRate,24);
 wav.writeUInt32LE(sampleRate*4,28);wav.writeUInt16LE(4,32);
 wav.writeUInt16LE(16,34);wav.write('data',36);
 wav.writeUInt32LE(left.length*4,40);
 const gain=.82/peak;
 const fadeIn=Math.max(1,Math.round(.006*sampleRate));
 const fadeOut=Math.max(1,Math.round(.18*sampleRate));
 for(let i=0;i<left.length;i++){
  const fade=Math.min(1,(i+1)/fadeIn,(left.length-i)/fadeOut);
  wav.writeInt16LE(Math.round(32767*left[i]*gain*fade),44+4*i);
  wav.writeInt16LE(Math.round(32767*right[i]*gain*fade),46+4*i);
 }
 return {wav,gain,peakRelativePressure:peak};
}
