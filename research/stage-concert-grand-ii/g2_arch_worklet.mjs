import {CoupledCore} from './g2_arch_port.mjs';
// Architecture proof only: one force input, stereo causal observer, no MIDI or production integration.
class G2PortProof extends AudioWorkletProcessor {
 constructor(){super();this.core=new CoupledCore(sampleRate);}
 process(inputs,outputs){const bus=outputs[0];if(bus?.length>=2)this.core.render(inputs[0]?.[0],bus[0],bus[1]);return true;}
}
registerProcessor('g2-port-proof',G2PortProof);
