// F9.18: provisional controller mapping, not a measured keyboard action.
// Log-domain monotone Hermite interpolation preserves all sampled hammer speeds.
// MIDI note-on velocity zero denotes note-off; it never launches a hammer.
export const VELOCITY_ANCHORS=Object.freeze([[1,.06],[8,.09],[16,.12],[24,.15],[36,.25],[44,.35],[52,.5],[76,1],[127,2.5]].map(Object.freeze));
const x=VELOCITY_ANCHORS.map(a=>a[0]),y=VELOCITY_ANCHORS.map(a=>Math.log(a[1]));
const h=x.slice(1).map((v,i)=>v-x[i]),d=h.map((v,i)=>(y[i+1]-y[i])/v);
const tangent=Array(x.length);
tangent[0]=d[0];tangent[x.length-1]=d.at(-1);
for(let i=1;i<x.length-1;i++){
 const w1=2*h[i]+h[i-1],w2=h[i]+2*h[i-1];
 tangent[i]=(w1+w2)/(w1/d[i-1]+w2/d[i]);
}
export function hammerSpeed(midiVelocity){
 if(!Number.isInteger(midiVelocity)||midiVelocity<0||midiVelocity>127)throw RangeError('MIDI velocity must be integer 0–127');
 if(midiVelocity===0)return null;
 const exact=VELOCITY_ANCHORS.find(a=>a[0]===midiVelocity);
 if(exact)return exact[1];
 const i=x.findIndex(v=>v>midiVelocity)-1,t=(midiVelocity-x[i])/h[i],t2=t*t,t3=t2*t;
 return Math.exp((2*t3-3*t2+1)*y[i]+(t3-2*t2+t)*h[i]*tangent[i]+(-2*t3+3*t2)*y[i+1]+(t3-t2)*h[i]*tangent[i+1]);
}
export function velocityTable(){
 return Array.from({length:127},(_,i)=>{const midiVelocity=i+1,velocityMps=hammerSpeed(midiVelocity);return {midiVelocity,velocityMps,hammerEnergyJ:.005*velocityMps**2};});
}
