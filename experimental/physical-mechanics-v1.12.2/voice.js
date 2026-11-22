export const clamp=(x,min,max)=>Math.max(min,Math.min(max,x));
export const hz=key=>440*2**((key-69)/12);
export function gain(ctx,value){
  const node=ctx.createGain();node.gain.value=value;return node;
}
export function filter(ctx,type,freq,q=.707){
  const node=ctx.createBiquadFilter();node.type=type;node.frequency.value=freq;node.Q.value=q;return node;
}
export function smooth(param,value,now,seconds=.018){
  param.setTargetAtTime(value,now,seconds);
}
// Continue a scheduled envelope from its current value before changing its target.
// cancelAndHoldAtTime is preferable because AudioParam.value need not reflect automation.
export function redirect(param, target, now, seconds=.02){
  if(param.cancelAndHoldAtTime)param.cancelAndHoldAtTime(now);
  else {const held=param.value;param.cancelScheduledValues(now);param.setValueAtTime(held,now)}
  param.setTargetAtTime(target,now,Math.max(.002,seconds));
}
export function saturation(amount,bias=0){
  if(amount<=0)return null;
  const drive=1+amount*.085;
  const curve=new Float32Array(1025);
  const center=Math.tanh(drive*bias), compensate=1/(1+.42*(drive-1));
  for(let i=0;i<curve.length;i++){
    const x=2*i/(curve.length-1)-1;
    curve[i]=(Math.tanh(drive*(x+bias))-center)*compensate;
  }
  return curve;
}
export function noiseBuffer(ctx,length=.07){
  const buffer=ctx.createBuffer(1,Math.ceil(ctx.sampleRate*length),ctx.sampleRate);
  const data=buffer.getChannelData(0);let seed=3721;
  for(let i=0;i<data.length;i++){seed=(1664525*seed+1013904223)>>>0;data[i]=seed/2147483648-1}
  return buffer;
}
// A separate release gate can damp any combination of oscillators or samples
// without cancelling the hammer, filter or amplitude envelope of the strike.
export class Part {
  constructor(ctx,output,expression,finished){
    this.ctx=ctx;this.expression=expression;this.finished=finished;
    this.gate=gain(ctx,1);this.gate.connect(output);
    this.nodes=[this.gate];this.sources=new Map();this.released=false;this.ended=false;
    this.releaseSeconds=.14;
  }
  own(...nodes){this.nodes.push(...nodes)}
  start(source,{pitch=true,when=this.ctx.currentTime,offset,until=Infinity}={}){
    const param=pitch?source.detune:null;
    if(param)this.expression.signal.connect(param);
    this.sources.set(source,until);
    source.onended=()=>{
      if(param){try{this.expression.signal.disconnect(param)}catch{}}
      source.disconnect();this.sources.delete(source);
      if(!this.sources.size){
        this.ended=true;
        for(const node of this.nodes)node.disconnect();
        this.finished();
      }
    };
    if(offset===undefined)source.start(when);else source.start(when,offset);
    if(Number.isFinite(until))source.stop(until);
  }
  release(fast=false){
    if(this.ended||(!fast&&this.released))return;
    if(!this.released)this.onRelease?.();
    this.released=true;
    const now=this.ctx.currentTime, duration=fast?.024:this.releaseSeconds;
    const gate=this.gate.gain;
    if(gate.cancelAndHoldAtTime)gate.cancelAndHoldAtTime(now);
    else {const current=gate.value;gate.cancelScheduledValues(now);gate.setValueAtTime(current,now)}
    gate.setTargetAtTime(0,now,Math.max(.002,duration/6));
    for(const [source,scheduled] of this.sources){
      try{source.stop(Math.min(now+duration,scheduled))}
      catch(error){if(error.name!=='InvalidStateError')throw error}
    }
  }
}
