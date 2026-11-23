/**
 * E2.1 — force-driven, sample-accurate research adapter for the 88-key
 * passive shared bridge. No AudioWorklet / public D connection.
 *
 * Positive, finite hammer-contact force is applied directly to the SAME
 * mechanical coordinates used for output and reaction. No add-on wet body,
 * no arbitrary dry-feedback gain, and no allocation in step()/render().
 *
 * Discrete energy audit (implicit midpoint):
 *   E(after) - E(before) = externalWork - dissipated
 * up to floating-point rounding, for any scheduled force sequence.
 * The force is normalized, not calibrated in newtons.
 */
import {DamperAwareSharedBridge} from './damper-aware-shared-bridge.mjs';

const TWO_PI=2*Math.PI;
export class HammerDrivenPassivePiano {
  constructor({sampleRate=48000,coupling=.12,releaseDamping=110,maxContactMs=12}={}){
    if(!Number.isFinite(maxContactMs)||maxContactMs<=0||maxContactMs>25)
      throw new RangeError('maxContactMs must be within (0,25]');
    this.bridge=new DamperAwareSharedBridge({sampleRate,coupling,releaseDamping});
    this.rate=sampleRate;
    this.maxContactSamples=Math.max(2,Math.ceil(sampleRate*maxContactMs/1000));
    this.remaining=new Int32Array(88);
    this.duration=new Int32Array(88);
    this.progress=new Int32Array(88);
    this.amplitude=new Float64Array(88);
    this.activeContactCount=0;
    this.samples=0;
  }
  noteOn(key,{velocity=80,contactMs=3,peakForce=1}={}){
    if(!Number.isInteger(key)||key<21||key>108||
       !Number.isFinite(velocity)||velocity<1||velocity>127||
       !Number.isFinite(contactMs)||contactMs<=0||
       !Number.isFinite(peakForce)||peakForce<0||peakForce>1e5)
      throw new RangeError('invalid normalized hammer event');
    const length=Math.max(2,Math.round(contactMs*this.rate/1000));
    if(length>this.maxContactSamples)throw new RangeError('hammer pulse too long');
    const i=key-21;
    this.bridge.noteOn(key);
    // Re-striking a key restarts the contact. 88 independent hammer states,
    // while the passive coordinates and bridge remain physically shared.
    if(this.remaining[i]===0)this.activeContactCount++;
    this.remaining[i]=length;
    this.duration[i]=length;
    this.progress[i]=0;
    this.amplitude[i]=peakForce*(velocity/127)**1.5;
  }
  noteOff(key){this.bridge.noteOff(key)}
  setSustain(cc64){this.bridge.setSustain(cc64)}
  step(){
    const forces=this.bridge.forces;
    // All 176 mechanical coordinates remain connected even with key off.
    // Populate both transverse polarizations with a single shared pulse.
    // Squared sine has zero force at start/end and positive contact only.
    for(let key=0;key<88;key++){
      const at=key*2;
      let force=0;
      if(this.remaining[key]>0){
        const phase=(this.progress[key]+.5)/this.duration[key];
        const sine=Math.sin(Math.PI*phase);
        force=this.amplitude[key]*sine*sine;
        this.progress[key]++;
        if(--this.remaining[key]===0)this.activeContactCount--;
      }
      forces[at]=force*.65;
      forces[at+1]=force*.35;
    }
    this.samples++;
    return this.bridge.step();
  }
  /**
   * Mechanical bridge velocity proxy, NOT audible piano PCM or Pa.
   * Caller provides preallocated buffers; no allocation inside render.
   */
  render(boardVelocity,offset=0,length=boardVelocity.length-offset){
    if(!(boardVelocity instanceof Float32Array||boardVelocity instanceof Float64Array)||
       !Number.isInteger(offset)||!Number.isInteger(length)||
       offset<0||length<0||offset+length>boardVelocity.length)
      throw new RangeError('invalid output buffer');
    for(let i=0;i<length;i++)boardVelocity[offset+i]=this.step();
  }
  energyBalanceError(){
    return this.bridge.energy()-(this.bridge.externalWork-this.bridge.dissipated);
  }
  reset(){
    this.bridge.reset();
    this.remaining.fill(0);this.duration.fill(0);
    this.progress.fill(0);this.amplitude.fill(0);
    this.activeContactCount=0;this.samples=0;
  }
}
