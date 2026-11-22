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
// Controle de portamento independente do modo de voz: a transição é entre
// note-ons consecutivos do mesmo teclado/canal, não um efeito de nota estática.
export const targetFrequency=(key,p)=>hz(key)*2**((p.octave*12+p.semitones+p.fine/100)/12);
export const unisonCount=p=>clamp(Number(p.unison)||1,1,3);
export class Synth{
  constructor(ctx,bus,options={}){this.ctx=ctx;this.lite=Boolean(options.lite);this.input=bus;this.previousHz=new Map();this.white=noiseBuffer(ctx,1.15);this.pink=pinkNoise(ctx);this.syncCache=new Map()}
  update(){}
  forget(expression){this.previousHz.delete(expression)}
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
    const baseHz=targetFrequency(key,p);
    const filterType=p.filterType||'lowpass';
    const tone=filter(ctx,filterType,p.cutoff,p.resonance);
    const base=clamp(p.cutoff*2**((key-60)/40)*(.6+.4*v),55,ctx.sampleRate*.45);
    const peak=clamp(base*2**(p.filterEnv*(.25+.75*v)),40,ctx.sampleRate*.46);
    tone.frequency.setValueAtTime(base,now);
    tone.frequency.exponentialRampToValueAtTime(peak,now+Math.max(.004,Math.min(p.attack,.14)));
    tone.frequency.setTargetAtTime(base,now+Math.min(p.attack,.14),Math.max(.012,p.decay*.32));
    const env=gain(ctx,0),vca=gain(ctx,(p.volume||0)/85),pan=ctx.createStereoPanner();pan.pan.value=(p.pan||0)/100;
    const volume=.19*v**1.1;
    const attack=isLegato?.009:p.attack;
    env.gain.setValueAtTime(0,now);env.gain.linearRampToValueAtTime(volume,now+Math.max(.003,attack));
    env.gain.setTargetAtTime(volume*p.sustain/100,now+attack,Math.max(.007,p.decay/4));
    tone.connect(env).connect(vca).connect(pan).connect(part.gate);part.own(tone,env,vca,pan);
    const lfo=ctx.createOscillator(),lfoGain=gain(ctx,0);
    lfo.type='sine';lfo.frequency.value=p.lfoRate||5;lfo.connect(lfoGain);
    const controls=[];
    const previous=this.previousHz.get(expression);
    const glideSeconds=Math.max(0,Number(p.glide)||0);
    // No audible glide on the first note (there is no pitch to glide from).
    const glideFrom=Number.isFinite(previous)?previous:baseHz;
    this.previousHz.set(expression,baseHz);
    const createOsc=(side,index,params,initial=false)=>{
      const osc=ctx.createOscillator(),amp=gain(ctx,0),sp=ctx.createStereoPanner();
      const wave=side==='A'?params.waveA:params.waveB;
      this.setWave(osc,wave,params,side);
      if(initial&&glideSeconds>.005&&Math.abs(glideFrom-baseHz)>.01){
        osc.frequency.setValueAtTime(Math.max(1,glideFrom),now);
        osc.frequency.exponentialRampToValueAtTime(baseHz,now+glideSeconds);
      }else osc.frequency.value=targetFrequency(key,params);
      osc.connect(amp).connect(sp).connect(tone);
      part.own(amp,sp);part.start(osc);
      const c={osc,amp,sp,side,sign:side==='A'?-1:1,index,width:0};
      controls.push(c);
      return c;
    };
    for(const side of ['A','B'])for(let j=0;j<(this.lite?1:unisonCount(p));j++)createOsc(side,j,p,true);
    const refreshOscLevels=(next,time)=>{
      const total=this.lite?1:unisonCount(next),blend=next.blend/100;
      for(const c of controls){
        c.width=total===1?0:(c.index-(total-1)/2)/((total-1)/2);
        const enabled=c.index<total;
        const level=c.side==='A'?Math.cos(blend*Math.PI/2)*next.oscA/100:Math.sin(blend*Math.PI/2)*next.oscB/100;
        smooth(c.amp.gain,enabled?level/Math.sqrt(total):0,time,.014);
        smooth(c.osc.detune,c.sign*next.detune*.5+c.width*14,time);
        smooth(c.sp.pan,clamp(c.sign*next.spread/200+c.width*.24,-1,1),time);
      }
    };
    refreshOscLevels(p,now);
    // Keep both noise colours available, so a zero-to-nonzero level change
    // or a pink/white switch works during a sustained note.
    const noiseGains={white:gain(ctx,0),pink:gain(ctx,0)};
    for(const type of ['white','pink']){
      const noise=ctx.createBufferSource();noise.buffer=type==='pink'?this.pink:this.white;noise.loop=true;
      noise.connect(noiseGains[type]).connect(tone);part.own(noiseGains[type]);part.start(noise,{pitch:false});
    }
    const setNoise=next=>{
      for(const [type,node] of Object.entries(noiseGains))smooth(node.gain,type===next.noiseType?next.noiseLevel*.0014:0,ctx.currentTime);
    };
    setNoise(p);
    part.own(lfoGain);
    // Auxiliary oscillator is a source owned by the voice and stops with its gate.
    part.start(lfo,{pitch:false});
    // Matriz de modulação dinâmica: velocity E aftertouch podem ser
    // roteados (e trocados) enquanto a nota está tocando.
    const velocitySource=ctx.createConstantSource();velocitySource.offset.value=v-.5;
    part.start(velocitySource,{pitch:false});
    const matrixGain=gain(ctx,0);part.own(matrixGain);
    let matrixSource=null;
    const applyMod=next=>{
      const amount=(next.lfoDepth||0)/100;
      const dst=next.lfoDest||'pitch';
      try{lfoGain.disconnect()}catch{}
      if(dst==='pitch'){
        for(const c of controls)lfoGain.connect(c.osc.detune);
        smooth(lfoGain.gain,amount*75,ctx.currentTime);
      }else if(dst==='cutoff'){
        lfoGain.connect(tone.frequency);
        smooth(lfoGain.gain,amount*Math.min(2800,next.cutoff*.65),ctx.currentTime);
      }else {
        lfoGain.connect(env.gain);
        smooth(lfoGain.gain,amount*volume*.36,ctx.currentTime);
      }
      const source=next.matrixSource==='aftertouch'?expression.pressure:velocitySource;
      if(matrixSource!==source){
        if(matrixSource)try{matrixSource.disconnect(matrixGain)}catch{}
        source.connect(matrixGain);matrixSource=source;
      }
      try{matrixGain.disconnect()}catch{}
      if(next.matrixDest==='pitch')for(const c of controls)matrixGain.connect(c.osc.detune);
      else if(next.matrixDest==='amp')matrixGain.connect(vca.gain);
      else matrixGain.connect(tone.frequency);
      const scale=next.matrixDest==='pitch'?90:next.matrixDest==='amp'?.30:Math.min(2400,next.cutoff*.6);
      smooth(matrixGain.gain,(next.matrixAmount||0)/100*scale,ctx.currentTime,.012);
    };
    applyMod(p);
    part.releaseSeconds=p.release;
    part.onRelease=()=>{
      const t=ctx.currentTime;
      if(env.gain.cancelAndHoldAtTime)env.gain.cancelAndHoldAtTime(t);
      else{const current=env.gain.value;env.gain.cancelScheduledValues(t);env.gain.setValueAtTime(current,t)}
      // A última altura permanece disponível para portamento na próxima nota.
      // A exclusão ocorre em disconnect()/panic(), não na soltura da tecla.
    };
    part.update=(next,changed)=>{
      const t=ctx.currentTime;
      const changedOne=(...keys)=>!changed||keys.includes(changed);
      if(changedOne('cutoff','resonance','filterType','filterEnv','attack','decay')){
        tone.type=next.filterType;
        const elapsed=Math.max(0,t-now-Math.min(next.attack,.14));
        const envOct=next.filterEnv*(.25+.75*v)*Math.exp(-elapsed/Math.max(.02,next.decay*.32));
        tone.frequency.cancelScheduledValues(t);
        smooth(tone.frequency,clamp(next.cutoff*2**((key-60)/40+envOct)*(.6+.4*v),50,ctx.sampleRate*.46),t);
        smooth(tone.Q,next.resonance,t);
      }
      const pitchKeys=['octave','semitones','fine'];
      const waveKeys=['waveA','waveB','pulseWidth','sync','syncRatio'];
      const oscKeys=['blend','oscA','oscB','detune','spread','unison'];
      const frequency=targetFrequency(key,next);
      // O uníssono aumenta/diminui os osciladores de uma voz sustentada.
      // Os novos osciladores entram com ganho zero e fazem fade-in, sem novo ADSR.
      if(changedOne('unison')&&!part.released){
        const count=this.lite?1:unisonCount(next);
        for(const side of ['A','B']){
          const allocated=controls.filter(c=>c.side===side).length;
          for(let j=allocated;j<count;j++)createOsc(side,j,next,false);
        }
      }
      for(const c of controls){
        if(changedOne(...waveKeys)){
          const wave=c.side==='A'?next.waveA:next.waveB;
          this.setWave(c.osc,wave,next,c.side);
        }
        if(changedOne(...pitchKeys)){
          // Reafinar uma nota sustentada imediatamente. Isso não cancela o
          // portamento ao ajustar apenas o tempo do glide.
          if(c.osc.frequency.cancelAndHoldAtTime)c.osc.frequency.cancelAndHoldAtTime(t);
          else {const val=c.osc.frequency.value;c.osc.frequency.cancelScheduledValues(t);c.osc.frequency.setValueAtTime(val,t)}
          smooth(c.osc.frequency,frequency,t,.014);
        }
      }
      if(changedOne(...oscKeys))refreshOscLevels(next,t);
      if(changedOne('pan'))smooth(pan.pan,next.pan/100,t);
      if(changedOne('lfoRate'))smooth(lfo.frequency,next.lfoRate,t);
      if(changedOne('lfoDest','lfoDepth','matrixSource','matrixDest','matrixAmount','cutoff','unison'))applyMod(next);
      if(changedOne('volume'))smooth(vca.gain,(next.volume||0)/85,t);
      if(changedOne('noiseLevel','noiseType'))setNoise(next);
      if(changedOne('attack','decay','sustain')&&!part.released){
        const elapsed=t-now;
        const target=elapsed<next.attack?volume:volume*next.sustain/100;
        const tau=elapsed<next.attack?Math.max(.004,(next.attack-elapsed)/3):Math.max(.008,next.decay/4);
        if(env.gain.cancelAndHoldAtTime)env.gain.cancelAndHoldAtTime(t);
        else {const prior=env.gain.value;env.gain.cancelScheduledValues(t);env.gain.setValueAtTime(prior,t)}
        env.gain.setTargetAtTime(target,t,tau);
      }
      part.releaseSeconds=next.release;
    };
  }
}
