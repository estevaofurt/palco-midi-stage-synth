import {PianoResonanceBody} from './piano-resonance.js';

/**
 * 1 mono/stereo input: DRY bridge bus from the Stage piano string engine.
 * 1 stereo output: WET shared soundboard and sympathetic strings ONLY.
 * The host, not this processor, mixes wet into the original piano output.
 *
 * Example usage (after an AudioContext is resumed):
 *   await ctx.audioWorklet.addModule('./piano-resonance-worklet.js');
 *   const body = new AudioWorkletNode(ctx,'stage-physical-resonance', {
 *      numberOfInputs:1, numberOfOutputs:1, outputChannelCount:[2]
 *   });
 *   stringBridgeBus.connect(body);
 *   body.connect(wetGain).connect(masterBus);
 *   body.port.postMessage({type:'noteOn',note:60,velocity:90});
 *   body.port.postMessage({type:'noteOff',note:60});
 *   body.port.postMessage({type:'sustain',value:127});
 */
if (typeof AudioWorkletProcessor!=='undefined' && typeof registerProcessor==='function') {
  class StagePhysicalResonanceProcessor extends AudioWorkletProcessor {
    constructor(){
      super();
      this.resonance=new PianoResonanceBody({sampleRate});
      this.zero=new Float32Array(128);
      this.port.onmessage=({data:d})=>{
        if(!d)return;
        if(d.type==='noteOn')this.resonance.noteOn(d.note,d.velocity);
        else if(d.type==='noteOff')this.resonance.noteOff(d.note);
        else if(d.type==='sustain')this.resonance.setSustain(d.value);
        else if(d.type==='allKeysUp')this.resonance.allKeysUp();
        else if(d.type==='reset')this.resonance.reset();
        else if(d.type==='set'){
          if(typeof d.sympathetic==='number')this.resonance.sympathetic=Math.max(0,Math.min(1,d.sympathetic));
          if(typeof d.body==='number')this.resonance.body=Math.max(0,Math.min(1,d.body));
          if(typeof d.mechanical==='number')this.resonance.mechanical=Math.max(0,Math.min(1,d.mechanical));
        }
      };
    }
    process(inputs,outputs){
      const out=outputs[0];if(!out?.[0])return true;
      const n=out[0].length;
      const x=inputs[0];
      const silence=this.zero.length===n?this.zero:new Float32Array(n);
      const l=x?.[0]||silence,r=x?.[1]||l;
      const wetL=out[0],wetR=out[1]||out[0];
      this.resonance.process(l,r,wetL,wetR);
      return true;
    }
  }
  registerProcessor('stage-physical-resonance',StagePhysicalResonanceProcessor);
}
