import {boardMobility,contactDrive} from './f11l-coupled-mobility.mjs';
import {kernelResponse} from './surface-radiation.mjs';
const add=([a,b],[c,d])=>[a+c,b+d],mul=([a,b],[c,d])=>[a*c-b*d,a*d+b*c],abs=z=>Math.hypot(...z);
const div=([a,b],[c,d])=>{const n=c*c+d*d;if(!(n>0))throw Error('singular');return [(a*c+b*d)/n,(b*c-a*d)/n];};
// Same radiation kernels as the time-domain export. Continuous mechanical
// response with approximate derivative (not exact discrete integrator).
export function radiatedResponse(bridge,board,joint,kernels,f){
 if(kernels.length!==2||kernels.some(k=>k.length!==board.modes.length))throw Error('kernel shape');
 const w=2*Math.PI*f,Ys=bridge.mobility(f).vv,{Y:Yb,vel}=boardMobility(board,f),Z=[joint.c,-joint.k/w];
 const force=mul(contactDrive(bridge,f),div(mul(Z,Ys),add([1,0],mul(Z,add(Ys,Yb)))));
 const acceleration=vel.map(v=>mul([0,w],mul(v,force)));
 const stereo=kernels.map(ks=>{
  const contributions=ks.map((k,i)=>{const H=kernelResponse(k,f);return mul([H.re,H.im],acceleration[i]);});
  const pressure=contributions.reduce(add,[0,0]),sumMagnitude=contributions.reduce((s,z)=>s+abs(z),0);
  return {pressure,magnitude:abs(pressure),sumMagnitude,coherence:sumMagnitude?abs(pressure)/sumMagnitude:0,topModes:contributions.map((z,i)=>({i,hz:board.modes[i].frequencyHz,magnitude:abs(z),complex:z})).sort((a,b)=>b.magnitude-a.magnitude).slice(0,4)};
 });
 return {f,stereo,magnitude:Math.hypot(...stereo.map(s=>s.magnitude))/Math.sqrt(2)};
}
export function scanRadiation(bridge,board,joint,kernels,center,spanCents=80,stepHz=.05){
 if(!(center>0&&spanCents>0&&stepHz>0))throw RangeError('scan');
 const lo=center*2**(-spanCents/1200),hi=center*2**(spanCents/1200),n=Math.ceil((hi-lo)/stepHz);
 if(n>5000)throw RangeError('scan size');
 const samples=Array.from({length:n+1},(_,i)=>radiatedResponse(bridge,board,joint,kernels,lo+(hi-lo)*i/n));
 const peaks=samples.filter((v,i)=>i>0&&i<n&&v.magnitude>=samples[i-1].magnitude&&v.magnitude>samples[i+1].magnitude).sort((a,b)=>b.magnitude-a.magnitude).slice(0,6).map(v=>({...v,cents:1200*Math.log2(v.f/center)}));
 return {center,stepHz:(hi-lo)/n,peaks,samples};
}
