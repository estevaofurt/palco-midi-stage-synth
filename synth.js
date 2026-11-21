import {clamp,filter,gain,hz,smooth} from './voice.js';
export class Synth {
  constructor(ctx,bus){this.ctx=ctx;this.input=bus}
  update(){}
  play(part,key,velocity,p){
    const ctx=this.ctx,now=ctx.currentTime,v=velocity/127,frequency=hz(key);
    const tone=filter(ctx,'lowpass',p.cutoff,p.resonance);
    const base=clamp(p.cutoff*2**((key-60)/40)*(.6+.40*v),55,ctx.sampleRate*.45);
    const peak=clamp(base*2**(p.filterEnv*(.25+.75*v)),60,ctx.sampleRate*.46);
    tone.frequency.setValueAtTime(base,now);
    tone.frequency.exponentialRampToValueAtTime(peak,now+Math.min(p.attack,.14));
    tone.frequency.setTargetAtTime(base,now+Math.min(p.attack,.14),p.decay*.32);
    const env=gain(ctx,0),volume=.20*v**1.12;
    env.gain.setValueAtTime(0,now);env.gain.linearRampToValueAtTime(volume,now+p.attack);
    env.gain.setTargetAtTime(volume*p.sustain/100,now+p.attack,p.decay/4);
    tone.connect(env).connect(part.gate);part.own(tone,env);
    const mix=p.blend/100;
    const oscillators=[];
    for(const [type,sign,level] of [[p.waveA,-1,Math.cos(mix*Math.PI/2)],[p.waveB,1,Math.sin(mix*Math.PI/2)]]){
      const osc=ctx.createOscillator(),amp=gain(ctx,level),pan=ctx.createStereoPanner();
      osc.type=type;osc.frequency.value=frequency;osc.detune.value=sign*p.detune*.5;
      pan.pan.value=sign*p.spread*.0065;osc.connect(amp).connect(pan).connect(tone);
      part.own(amp,pan);part.start(osc);oscillators.push({osc,amp,pan,sign});
    }
    part.releaseSeconds=p.release;
    part.onRelease=()=>{
      const t=ctx.currentTime;
      if(env.gain.cancelAndHoldAtTime)env.gain.cancelAndHoldAtTime(t);
      else {const current=env.gain.value;env.gain.cancelScheduledValues(t);env.gain.setValueAtTime(current,t)}
    };
    part.update=(next,changed)=>{
      const t=ctx.currentTime;
      if(!changed||['cutoff','resonance','filterEnv'].includes(changed)){
        const elapsed=Math.max(0,t-now-Math.min(next.attack,.14));
        const envOct=next.filterEnv*(.25+.75*v)*Math.exp(-elapsed/(next.decay*.32));
        tone.frequency.cancelScheduledValues(t);
        smooth(tone.frequency,clamp(next.cutoff*2**((key-60)/40+envOct)*(.6+.40*v),55,ctx.sampleRate*.46),t);
        smooth(tone.Q,next.resonance,t);
      }
      for(const {osc,sign,amp,pan} of oscillators){
        const wave=sign<0?next.waveA:next.waveB;
        if(osc.type!==wave)osc.type=wave;
        smooth(osc.detune,sign*next.detune*.5,t);
        const angle=next.blend*Math.PI/200;
        smooth(amp.gain,sign<0?Math.cos(angle):Math.sin(angle),t);
        smooth(pan.pan,sign*next.spread*.0065,t);
      }
      if((!changed||changed==='sustain')&&t>=now+p.attack)smooth(env.gain,volume*next.sustain/100,t);
      part.releaseSeconds=next.release;
    };
  }
}
