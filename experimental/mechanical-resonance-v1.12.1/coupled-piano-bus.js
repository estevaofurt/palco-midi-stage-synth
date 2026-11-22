import {PianoResonanceBody} from './piano-resonance.js';

/**
 * Host integration helper: closes the reciprocal string–bridge–body loop
 * within one AUDIO sample callback. The string adapter MUST implement:
 *    sample()      -> sets its own finite .dryL, .dryR, .bridgeL, .bridgeR
 *    pushBridge(x) -> stores bounded response for its NEXT sample step.
 * IMPORTANT: no AudioNode feedback cables and no two separate AudioWorklets.
 * A physically derived waveguide source should provide those methods; this
 * component is a bridge integration CONTRACT, not a complete piano voice.
 */
export class CoupledPianoBus {
  constructor(source,{sampleRate=48000,divisor=4,wetMix=0.12,feedbackGain=0.8,body=null}={}){
    if(!source || typeof source.sample!=='function'||typeof source.pushBridge!=='function')throw new TypeError('source must implement sample() and pushBridge(x)');
    this.source=source;
    this.body=body||new PianoResonanceBody({sampleRate,divisor});
    this.wetMix=Math.max(0,Math.min(.6,wetMix));
    this.feedbackGain=Math.max(0,Math.min(1,feedbackGain));
  }
  noteOn(note,velocity){this.body.noteOn(note,velocity);this.source.noteOn?.(note,velocity)}
  noteOff(note){this.body.noteOff(note);this.source.noteOff?.(note)}
  setSustain(cc){this.body.setSustain(cc);this.source.setSustain?.(cc)}
  allKeysUp(){this.body.allKeysUp();this.source.allKeysUp?.()}
  reset(){this.body.reset();this.source.reset?.()}
  render(outL,outR,n=outL.length){
    if(n>outL.length||n>outR.length)throw new RangeError('output length');
    const source=this.source,body=this.body;
    for(let i=0;i<n;i++){
      source.sample();
      body.step(source.bridgeL,source.bridgeR);
      // One-sample delay is deliberate; output from the body influences
      // string displacement, not just wet volume.
      source.pushBridge(body.reaction*this.feedbackGain);
      outL[i]=source.dryL+body.wetL*this.wetMix;
      outR[i]=source.dryR+body.wetR*this.wetMix;
    }
  }
}
