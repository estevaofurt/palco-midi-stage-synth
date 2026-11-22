import {clamp,filter,gain,hz,smooth,noiseBuffer} from './voice.js';
function pulseWave(ctx,duty){
  const real=new Float32Array(49),imag=new Float32Array(49);
  const d=clamp(duty/100,.05,.95);
  for(let n=1;n<49;n++){
    real[n]=Math.sin(2*Math.PI*n*d)/(Math.PI*n);
    imag[n]=(1-Math.cos(2*Math.PI*n*d))/(Math.PI*n);
  }
  return ctx.createPeriodicWave(real,imag);
}
function hardSyncWave(ctx,wave,ratio,pulseWidth){
  // Band-limited wavetable approximation of a slave oscillator reset by master cycles.
  // Reconstruct periodic Fourier harmonics for browser-native OscillatorNode playback.
  const samples=1024,harmonics=48,real=new Float32Array(harmonics+1),imag=new Float32Array(harmonics+1);
  for(let n=0;n<samples;n++){
    const master=n/samples,slave=(master*ratio)%1;
    const y=wave==='sine'?Math.sin(2*Math.PI*slave):wave==='triangle'?4*Math.abs(slave-.5)-1:
      wave==='square'?(slave<.5?1:-1):wave==='pulse'?(slave<pulseWidth/100?1:-1):2*slave-1;
    for(let k=1;k<=harmonics;k++){
      const angle=2*Math.PI*k*master;
      real[k]+=2*y*Math.cos(angle)/samples;
      imag[k]+=2*y*Math.sin(angle)/samples;
    }
  }
  return ctx.createPeriodicWave(real,imag);
}
function pinkNoise(ctx){
  const buf=noiseBuffer(ctx,1.15),a=buf.getChannelData(0);
  let b0=0,b1=0,b2=0,b3=0,b4=0,b5=0,b6=0;
  for(let i=0;i<a.length;i++){
    const white=a[i];b0=.99886*b0+white*.0555179;b1=.99332*b1+white*.0750759;
    b2=.969*b2+white*.153852;b3=.8665*b3+white*.3104856;
    b4=.55*b4+white*.5329522;b5=-.7616*b5-white*.016898;
    a[i]=clamp((b0+b1+b2+b3+b4+b5+b6+white*.5362)*.11,-1,1);b6=white*.115926;
  }
  return buf;
}
export class Synth{
  constructor(ctx,bus){this.ctx=ctx;this.input=bus;this.previousHz=new Map();this.white=noiseBuffer(ctx,1.15);this.pink=pinkNoise(ctx);this.syncCache=new Map()}
  update(){}
  setWave(osc,wave,p,side){
    if(p.sync==='on'&&side==='B'){
      const key=wave+'/'+p.syncRatio+'/'+p.pulseWidth;
      if(!this.syncCache.has(key)){
        this.syncCache.set(key,hardSyncWave(this.ctx,wave,p.syncRatio,p.pulseWidth));
        if(this.syncCache.size>30)this.syncCache.delete(this.syncCache.keys().next().value);
      }
      osc.setPeriodicWave(this.syncCache.get(key));
    }else if(wave==='pulse')osc.setPeriodicWave(pulseWave(this.ctx,p.pulseWidth));
    else osc.type=wave;
  }
  play(part,key,velocity,p,expression,legato=false){
    const ctx=this.ctx,now=ctx.currentTime,v=velocity/127;
    const mode=p.voiceMode||'poly',isLegato=mode==='legato'&&legato;
    const baseHz=hz(key)*2**((p.octave*12+p.semitones+p.fine/100)/12);
    const filterType=p.filterType||'lowpass';
    const tone=filter(ctx,filterType,p.cutoff,p.resonance);
    const base=clamp(p.cutoff*2**((key-60)/40)*(.6+.4*v),55,ctx.sampleRate*.45);
    const peak=clamp(base*2**(p.filterEnv*(.25+.75*v)),40,ctx.sampleRate*.46);
    tone.frequency.setValueAtTime(base,now);
    tone.frequency.exponentialRampToValueAtTime(peak,now+Math.max(.004,Math.min(p.attack,.14)));
    tone.frequency.setTargetAtTime(base,now+Math.min(p.attack,.14),Math.max(.012,p.decay*.32));
    const env=gain(ctx,0),pan=ctx.createStereoPanner();pan.pan.value=(p.pan||0)/100;
    const volume=.19*v**1.1*(p.volume||85)/85;
    const attack=isLegato?.009:p.attack;
    env.gain.setValueAtTime(0,now);env.gain.linearRampToValueAtTime(volume,now+Math.max(.003,attack));
    env.gain.setTargetAtTime(volume*p.sustain/100,now+attack,Math.max(.007,p.decay/4));
    tone.connect(env).connect(pan).connect(part.gate);part.own(tone,env,pan);
    const lfo=ctx.createOscillator(),lfoGain=gain(ctx,0);
    lfo.type='sine';lfo.frequency.value=p.lfoRate||5;lfo.connect(lfoGain);
    const controls=[],mix=p.blend/100;
    const portamento=(mode==='mono'||mode==='legato')?p.glide:0;
    const last=this.previousHz.get(expression)||baseHz;
    this.previousHz.set(expression,baseHz);
    for(const [side,wave,amount,sign] of [
      ['A',p.waveA,Math.cos(mix*Math.PI/2)*p.oscA/100,-1],
      ['B',p.waveB,Math.sin(mix*Math.PI/2)*p.oscB/100,1]
    ]){
      const voices=Number(p.unison||1);
      for(let j=0;j<voices;j++){
        const osc=ctx.createOscillator(),amp=gain(ctx,amount/Math.sqrt(voices)),sp=ctx.createStereoPanner();
        this.setWave(osc,wave,p,side);
        const width=voices===1?0:(j-(voices-1)/2)/(voices-1);
        const spread=sign*(p.spread/100)*.5+width*.24;
        sp.pan.value=clamp(spread,-1,1);
        const unisonDetune=(p.detune/2)*sign+width*14;
        osc.detune.value=unisonDetune;
        if(portamento>.005){osc.frequency.setValueAtTime(last,now);osc.frequency.exponentialRampToValueAtTime(baseHz,now+portamento)}
        else osc.frequency.value=baseHz;
        osc.connect(amp).connect(sp).connect(tone);part.own(amp,sp);part.start(osc);
        controls.push({osc,amp,sp,side,sign,width});
      }
    }
    if(p.noiseLevel>0){
      const noise=ctx.createBufferSource(),noiseAmp=gain(ctx,p.noiseLevel*.0014);
      noise.buffer=p.noiseType==='pink'?this.pink:this.white;noise.loop=true;
      noise.connect(noiseAmp).connect(tone);part.own(noiseAmp);part.start(noise,{pitch:false});
    }
    part.own(lfoGain);
    // Auxiliary oscillator is a source owned by the voice and stops with its gate.
    part.start(lfo,{pitch:false});
    let matrixGain=null;
    const pressure=expression.pressure;
    const source=(p.matrixSource==='aftertouch'&&pressure)?pressure:null;
    if(source){matrixGain=gain(ctx,0);source.connect(matrixGain);part.own(matrixGain)}
    function applyMod(next){
      const amount=(next.lfoDepth||0)/100;
      const dst=next.lfoDest||'pitch';
      try{lfoGain.disconnect()}catch{}
      if(dst==='pitch'){for(const c of controls)lfoGain.connect(c.osc.detune);smooth(lfoGain.gain,amount*75,ctx.currentTime)}
      else if(dst==='cutoff'){lfoGain.connect(tone.frequency);smooth(lfoGain.gain,amount*Math.min(2800,next.cutoff*.65),ctx.currentTime)}
      else {lfoGain.connect(env.gain);smooth(lfoGain.gain,amount*volume*.36,ctx.currentTime)}
      if(matrixGain){try{matrixGain.disconnect()}catch{}
        const dest=next.matrixDest==='pitch'?null:next.matrixDest==='amp'?env.gain:tone.frequency;
        if(next.matrixDest==='pitch')for(const c of controls)matrixGain.connect(c.osc.detune);
        else if(dest)matrixGain.connect(dest);
        const scale=next.matrixDest==='pitch'?80:next.matrixDest==='amp'?volume*.35:Math.min(2400,next.cutoff*.6);
        smooth(matrixGain.gain,(next.matrixAmount||0)/100*scale,ctx.currentTime);
      }
    }
    applyMod(p);
    // Velocity routing produces a per-note modulation independent of channel aftertouch.
    if(p.matrixSource==='velocity'&&p.matrixAmount){
      const amt=(p.matrixAmount/100)*(v-.5);
      if(p.matrixDest==='cutoff')smooth(tone.frequency,clamp(peak+amt*p.cutoff*.65,50,ctx.sampleRate*.45),now);
      else if(p.matrixDest==='amp')smooth(env.gain,Math.max(0,volume*(p.sustain/100+amt*.3)),now+attack);
      else for(const c of controls)smooth(c.osc.detune,c.osc.detune.value+amt*70,now);
    }
    part.releaseSeconds=p.release;
    part.onRelease=()=>{
      const t=ctx.currentTime;
      if(env.gain.cancelAndHoldAtTime)env.gain.cancelAndHoldAtTime(t);
      else{const current=env.gain.value;env.gain.cancelScheduledValues(t);env.gain.setValueAtTime(current,t)}
      if(this.previousHz.get(expression)===baseHz&&mode==='poly')this.previousHz.delete(expression);
    };
    part.update=(next,changed)=>{
      const t=ctx.currentTime;
      if(!changed||['cutoff','resonance','filterType','filterEnv'].includes(changed)){
        tone.type=next.filterType;
        const elapsed=Math.max(0,t-now-Math.min(next.attack,.14));
        const envOct=next.filterEnv*(.25+.75*v)*Math.exp(-elapsed/Math.max(.02,next.decay*.32));
        tone.frequency.cancelScheduledValues(t);
        smooth(tone.frequency,clamp(next.cutoff*2**((key-60)/40+envOct)*(.6+.4*v),50,ctx.sampleRate*.46),t);
        smooth(tone.Q,next.resonance,t);
      }
      for(const c of controls){
        const wave=c.side==='A'?next.waveA:next.waveB;
        this.setWave(c.osc,wave,next,c.side);
        smooth(c.osc.detune,c.sign*next.detune*.5+c.width*14,t);
        const level=c.side==='A'?Math.cos(next.blend*Math.PI/200)*next.oscA/100:Math.sin(next.blend*Math.PI/200)*next.oscB/100;
        smooth(c.amp.gain,level/Math.sqrt(Number(p.unison||1)),t);
        smooth(c.sp.pan,clamp(c.sign*next.spread/200+c.width*.24,-1,1),t);
      }
      smooth(pan.pan,next.pan/100,t);
      smooth(lfo.frequency,next.lfoRate,t);applyMod(next);
      if((!changed||changed==='sustain')&&t>=now+attack)smooth(env.gain,volume*next.sustain/100,t);
      part.releaseSeconds=next.release;
    };
  }
}
