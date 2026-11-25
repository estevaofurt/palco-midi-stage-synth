// G2.07a: free-decay diagnostic from identical physical post-strike state.
// No acoustic radiation, bridge coupling, gain shaping, or fitted sustain.
import {StringPilot} from './g2_string_pilot.mjs';
export const LOSS_CASES=Object.freeze({
 control:Object.freeze({sigma0PerS:.4,sigma2M2PerS:.0002}),
 baseHalf:Object.freeze({sigma0PerS:.2,sigma2M2PerS:.0002}),
 bendHalf:Object.freeze({sigma0PerS:.4,sigma2M2PerS:.0001}),
 bothHalf:Object.freeze({sigma0PerS:.2,sigma2M2PerS:.0001})
});
export function snapshot(s){
 return s.modes.map(m=>({x:m.x,v:m.velocity()}));
}
export function cloneFree(s,loss){
 const q=new StringPilot(s.wire.midi,s.sr,{cutoffHz:s.cutoffHz,strikeFraction:s.strikeFraction,widthM:s.widthM,...loss});
 const state=snapshot(s);
 if(q.modes.length!==state.length)throw Error('mode count');
 for(let i=0;i<state.length;i++)q.modes[i].init(state[i].x,state[i].v);
 return q;
}
export function exactFree(m,t){
 if(!Number.isFinite(t)||t<0)throw RangeError('time');
 const r=Math.exp(-m.sigma*t),c=Math.cos(m.w*t),s=Math.sin(m.w*t);
 const x=r*(c*m.x-s*m.y),y=r*(s*m.x+c*m.y),v=-m.sigma*x-m.w*y;
 return {x,v,energyJ:.5*(m.p.massKg*v*v+m.p.k*x*x),envelopeM:r*Math.hypot(m.x,m.y)};
}
export function envelopeT60(sigma){if(!Number.isFinite(sigma)||sigma<0)throw RangeError('loss');return sigma===0?Infinity:Math.log(1000)/sigma;}
export function measureFree(s,t){
 const p=s.modes.map(m=>exactFree(m,t)),E0=s.energy(),E=p.reduce((a,b)=>a+b.energyJ,0);
 return {timeS:t,energyJ:E,energyDb:10*Math.log10(Math.max(E/E0,1e-300)),partialEnvelopeDb:p.map((q,i)=>20*Math.log10(Math.max(q.envelopeM/Math.max(Math.hypot(s.modes[i].x,s.modes[i].y),1e-300),1e-300)))};
}
