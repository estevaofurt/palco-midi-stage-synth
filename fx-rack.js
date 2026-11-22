import {engines,effectsDefinition} from './patches.js';
import {gain,filter,smooth,clamp,noiseBuffer} from './voice.js';
function impulse(ctx,seconds,seed=179){
  const len=Math.ceil(ctx.sampleRate*seconds),buffer=ctx.createBuffer(2,len,ctx.sampleRate);
  for(let ch=0;ch<2;ch++){
    const a=buffer.getChannelData(ch);let low=0;
    for(let i=0;i<len;i++){
      seed=(seed*1664525+1013904223)>>>0;
      const n=seed/2147483648-1;
      low=.58*low+.42*n;
      const x=i/ctx.sampleRate;
      a[i]=(low*.48+n*.1)*Math.exp(-x*5/seconds)*(1-Math.exp(-x*350));
    }
  }
  return buffer;
}
export class FXRack {
  constructor(ctx,master,state,buses){
    this.ctx=ctx;this.state=state;this.nodes={};this.sends={};
    for(const {id,type} of effectsDefinition){
      const input=gain(ctx,1),wet=gain(ctx,0),slot={input,wet};
      this.nodes[id]=slot;wet.connect(master);this.sends[id]={};
      for(const module of Object.keys(engines)){
        const send=gain(ctx,0);buses[module].connect(send).connect(input);this.sends[id][module]=send;
      }
      if(type==='reverb'){
        const conv=ctx.createConvolver();conv.buffer=impulse(ctx,id==='reverb1'?1.7:3.5,id==='reverb1'?171:431);
        input.connect(conv).connect(wet);slot.convolver=conv;
      } else if(type==='delay'){
        const delay=ctx.createDelay(2.5),loop=gain(ctx,.2),tone=filter(ctx,'lowpass',5400);
        input.connect(delay).connect(tone).connect(wet);
        delay.connect(loop).connect(delay);slot.delay=delay;slot.loop=loop;
      } else if(type==='mod'){
        const delay=ctx.createDelay(.04),lfo=ctx.createOscillator(),depth=gain(ctx,0);
        delay.delayTime.value=id==='mod1'?.018:.006;
        lfo.frequency.value=1.1;lfo.connect(depth).connect(delay.delayTime);lfo.start();
        input.connect(delay).connect(wet);slot.lfo=lfo;slot.depth=depth;
      } else if(type==='eq'){
        const low=filter(ctx,'lowshelf',170),mid=filter(ctx,'peaking',1000,1),high=filter(ctx,'highshelf',6200);
        input.connect(low).connect(mid).connect(high).connect(wet);slot.low=low;slot.mid=mid;slot.high=high;
      } else if(type==='comp'){
        const comp=ctx.createDynamicsCompressor();comp.attack.value=.008;comp.release.value=.18;
        input.connect(comp).connect(wet);slot.comp=comp;
      }
    }
    this.update();
  }
  update(){
    const now=this.ctx.currentTime;
    for(const {id,type} of effectsDefinition){
      const p=this.state.fx.slots[id],slot=this.nodes[id];
      const amount=clamp(p.mix,0,100)/100;
      // Only one selected engine feeds a session, and that engine can bypass all assigned effects.
      for(const [module,send] of Object.entries(this.sends[id])){
        const enabled=p.active&&p.target===module&&this.state.fx.enabled[module];
        smooth(send.gain,enabled?1:0,now,.02);
      }
      smooth(slot.wet.gain,p.active?amount*(type==='eq'||type==='comp'?.75:.55):0,now,.02);
      if(type==='reverb'){
        const seconds=clamp(p.time,.3,3.8);
        if(slot.impulseSeconds===undefined||Math.abs(seconds-slot.impulseSeconds)>.08){
          slot.impulseSeconds=seconds;clearTimeout(slot.impulseTimer);
          slot.impulseTimer=setTimeout(()=>{slot.convolver.buffer=impulse(this.ctx,seconds,id==='reverb1'?171:431)},140);
        }
      }else if(type==='delay'){
        smooth(slot.delay.delayTime,clamp(p.time,.04,1.5),now,.025);
        smooth(slot.loop.gain,clamp(p.feedback,0,80)/100,now,.03);
      }else if(type==='mod'){
        smooth(slot.lfo.frequency,clamp(p.rate,.1,12),now,.04);
        smooth(slot.depth.gain,id==='mod1'?.0035:.0009,now,.04);
      }else if(type==='eq'){
        smooth(slot.low.gain,clamp(p.low,-12,12),now);
        smooth(slot.mid.gain,clamp(p.mid,-12,12),now);
        smooth(slot.high.gain,clamp(p.high,-12,12),now);
      }else if(type==='comp'){
        smooth(slot.comp.threshold,clamp(p.threshold,-50,0),now);
        smooth(slot.comp.ratio,clamp(p.ratio,1,16),now);
      }
    }
  }
}
