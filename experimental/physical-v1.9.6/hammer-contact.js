/* Stage Synth — compact physically-informed hammer contact force.
 * Computed when a note starts (and cached by a bounded bank); never in the
 * per-sample AudioWorklet render loop. No recorded audio or sample library.
 * Semiquantitative nonlinear mass/felt/string-impedance surrogate:
 *    F=K max(0,delta)^p, m dv/dt=-F, delta'=v-F/(2 Z)
 * Parameters are tuning hypotheses, not measured Yamaha/Steinway constants.
 */
const clamp=(x,lo,hi)=>Math.min(hi,Math.max(lo,x));
export const HAMMER_REGISTERS=Object.freeze([24,36,48,60,72,84,96,108]);
export const HAMMER_VELOCITIES=Object.freeze([.18,.46,.72,.98]);
export const HAMMER_HARDNESSES=Object.freeze([.16,.52,.88]);

// Fixed-length maximum output avoids variable-sized allocations in the processor.
export function simulateHammerContact(rate,key,velocity,hardness,character='japanese'){
  const sr=clamp(rate,22050,96000),k=clamp(key,21,108),v=clamp(velocity,.015,1),h=clamp(hardness,0,1);
  const maxCount=Math.ceil(sr*.009),wave=new Float32Array(maxCount);
  const oversample=4,dt=1/(sr*oversample),felt=character==='felt';
  const mass=clamp(.006*2**((60-k)/48)*(character==='american'?1.05:character==='upright'?.89:1),.0023,.014);
  const exponent=felt?2.65:character==='american'?2.43:character==='upright'?2.31:2.38;
  const baseStiffness=felt?9.6e8:character==='american'?2.35e8:character==='upright'?3.0e8:2.5e8;
  const stiffness=baseStiffness*2**((k-60)/36)*(.5+2.2*h);
  const impedance=clamp(8*2**((k-60)/52),3.8,26);
  let compression=0,hammerVelocity=.14+3.1*v,contact=0,peak=0,total=0,done=false;
  // Micro-integration of the compression/rebound, including energy transferred
  // into the string via transverse-wave impedance. Output is contact force.
  for(let i=0;i<maxCount;i++){
    let acc=0;
    for(let sub=0;sub<oversample;sub++){
      if(done)continue;
      const f=compression>0?Math.min(4500,stiffness*compression**exponent):0;
      const stringVelocity=f/(2*impedance);
      hammerVelocity-=f/mass*dt;
      compression+=(hammerVelocity-stringVelocity)*dt;
      if(compression<=0&&i>0){compression=0;done=true;}
      acc+=f;
    }
    const value=acc/oversample;wave[i]=value;
    peak=Math.max(peak,value);total+=value;
    if(done&&i>0){contact=i+1;break;}
  }
  if(!contact)contact=maxCount;
  // Keep shape, but decouple excitation amplitude from the 3-D physical units;
  // the note-on velocity still controls actual musical loudness.
  const inv=total>1e-10?1/total:0;
  for(let i=0;i<contact;i++)wave[i]*=inv;
  return {wave,count:contact,durationMs:1000*contact/sr,peakForce:peak,impulse:total/sr};
}

// A compact cache, bounded by register/velocity/hardness grids.
// Each attack reads at most two force envelopes and blends continuously across
// register (no re-running the nonlinear solver on 32- or 64-note chords).
export class HammerContactBank {
  constructor(sampleRate=48000){
    this.rate=sampleRate;this.entries={};
    this.grid=new Map();
    for(const character of ['japanese','american','felt','upright']){
      const kernels=[];
      for(const key of HAMMER_REGISTERS){
        const vGroup=[];
        for(const v of HAMMER_VELOCITIES){
          const hGroup=[];
          for(const h of HAMMER_HARDNESSES)hGroup.push(simulateHammerContact(sampleRate,key,v,h,character));
          vGroup.push(hGroup);
        }
        kernels.push(vGroup);
      }
      this.grid.set(character,kernels);
    }
  }
  locate(values,value){
    if(value<=values[0])return [0,0,0];
    const last=values.length-1;
    if(value>=values[last])return [last,last,0];
    for(let i=0;i<last;i++)if(value<=values[i+1])return [i,i+1,(value-values[i])/(values[i+1]-values[i])];
    return [last,last,0];
  }
  // Trilinear interpolation prevents sudden timbre jumps as MIDI velocity,
  // key range and hammer hardness change. Interpolation runs once per note.
  select(key,velocity,hardness,character='japanese'){
    const group=this.grid.get(character)||this.grid.get('japanese');
    const [lo,hi,t]=this.locate(HAMMER_REGISTERS,key);
    const [vl,vh,tv]=this.locate(HAMMER_VELOCITIES,velocity);
    const [hl,hh,th]=this.locate(HAMMER_HARDNESSES,hardness);
    const entries=[],weights=[];let durationMs=0,maxCount=0;
    const segments=[[[lo,1-t],[hi,t]],[[vl,1-tv],[vh,tv]],[[hl,1-th],[hh,th]]];
    for(const [ki,kw] of segments[0])for(const [vi,vw] of segments[1])for(const [hj,hw] of segments[2]){
      const weight=kw*vw*hw;if(weight<=0)continue;
      const kernel=group[ki][vi][hj];
      entries.push(kernel);weights.push(weight);
      durationMs+=weight*kernel.durationMs;
      maxCount=Math.max(maxCount,kernel.count);
    }
    return {entries,weights,durationMs,maxCount,first:group[lo][vl][hl],second:group[hi][vh][hh],blend:t};
  }
}
