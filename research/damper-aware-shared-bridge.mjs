/**
 * Research-only, 88-key passive shared bridge with damper and CC64 controls.
 * NOT sound pressure / commercial piano model; masses and stiffness are illustrative.
 *
 * Every string remains connected, including silent/damped keys; the bridge's
 * stiffness does not disappear on key-up. Damper changes change only C >= 0,
 * and refactor the O(N) implicit midpoint Schur terms at event time.
 * No heap allocation in step(), no independent soundboards per voice.
 */
import {SharedPassivePianoBridge} from './shared-passive-piano-bridge.mjs';
export const ALL_PIANO_KEYS=Object.freeze(Array.from({length:88},(_,i)=>i+21));

export class DamperAwareSharedBridge extends SharedPassivePianoBridge {
  constructor({sampleRate=48000,coupling=.12,releaseDamping=110}={}){
    super({sampleRate,keys:ALL_PIANO_KEYS,coupling});
    if(!Number.isFinite(releaseDamping)||releaseDamping<0||releaseDamping>400)
      throw new RangeError('release damping must be 0..400');
    this.held=new Uint8Array(88);
    this.pedal=0;
    this.releaseDamping=releaseDamping;
    this.openDamping=new Float64Array(this.damping);
    this.noteDamping=new Float64Array(88);
    this.updateDampers();
  }
  noteOn(key){
    if(!Number.isInteger(key)||key<21||key>108)throw new RangeError('MIDI key 21..108');
    const idx=key-21;
    if(this.held[idx]<255)this.held[idx]++;
    this.updateDampers();
  }
  noteOff(key){
    if(!Number.isInteger(key)||key<21||key>108)throw new RangeError('MIDI key 21..108');
    const idx=key-21;
    if(this.held[idx])this.held[idx]--;
    this.updateDampers();
  }
  setSustain(value){
    if(!Number.isFinite(value)||value<0||value>127)
      throw new RangeError('CC64 must be 0..127');
    this.pedal=value;
    this.updateDampers();
  }
  updateDampers(){
    // Full damper lift for depressed key / CC64>=64.
    // High register A6..C8 has no modeled dampers, following prototype policy.
    // Actual half-pedal/hysteresis and precise damper transition are NOT modeled.
    const pedalDown=this.pedal>=64;
    const h=this.dt;
    let schur=0;
    for(let i=0;i<this.n;i++){
      const k=i>>1;
      const open=k>=70||pedalDown||this.held[k]>0;
      this.damping[i]=this.openDamping[i]+(open?0:2*this.mass[i]*this.releaseDamping);
      const a=this.mass[i]+.5*h*this.damping[i]+.25*h*h*(this.ground[i]+this.coupling[i]);
      this.aInverse[i]=1/a;
      const s=this.offDiagonal[i];
      schur+=s*s/a;
    }
    // Matrix SPD continues to hold: M>0, C>=0, K>0.
    this.S00=this.bmass[0]+.5*h*this.bdamper[0]+
      .25*h*h*(this.bground[0]+this.boardSpring+this.sumK)-schur;
    this.determinant=this.S00*this.S11-this.S01*this.S01;
    if(!(this.S00>0&&this.determinant>0&&Number.isFinite(this.determinant)))
      throw new RangeError('non-passive damper configuration');
  }
  strike(key,{displacement=.00001,polarization=0}={}){
    if(!Number.isInteger(key)||key<21||key>108||
       !Number.isInteger(polarization)||polarization<0||polarization>1||
       !Number.isFinite(displacement))
      throw new RangeError('invalid normalized strike');
    this.setInitialStringDisplacement((key-21)*2+polarization,displacement);
  }
  reset(){
    super.reset();
    if(this.held){this.held.fill(0);this.pedal=0;this.updateDampers();}
  }
}
