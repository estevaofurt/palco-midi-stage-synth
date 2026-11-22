import {clamp,filter,gain,hz,noiseBuffer,smooth,redirect} from './voice.js';
import {SF2Reader} from './sf2-reader.js';
export class SoundFontEngine{
  constructor(ctx,bus){
    this.ctx=ctx;this.input=filter(ctx,'lowpass',8500);this.pan=ctx.createStereoPanner();
    this.input.connect(this.pan).connect(bus);
    this.noise=noiseBuffer(ctx,.2);this.reader=null;this.program=0;
  }
  update(p){
    smooth(this.input.frequency,1100*2**(p.brightness/21),this.ctx.currentTime);
    smooth(this.pan.pan,p.pan/100,this.ctx.currentTime);
  }
  async load(file){
    if(!file||(!/\.sf2$/i.test(file.name)&&file.type!=='application/octet-stream'))throw Error('Selecione um arquivo .sf2.');
    if(file.size>100*1024*1024)throw Error('Arquivo SF2 maior que o limite de 100 MB.');
    const buf=await file.arrayBuffer();const parsed=new SF2Reader(buf);
    if(!parsed.programs.length)throw Error('Este SoundFont não contém programas.');
    this.reader=parsed;this.program=0;
    return parsed.programs;
  }
  unload(){this.reader=null;this.program=0}
  play(part,key,velocity,p){
    const ctx=this.ctx,now=ctx.currentTime,v=velocity/127;
    const activeAmps=[];
    part.update=(next,changed)=>{
      part.releaseSeconds=next.release;
      const t=ctx.currentTime;
      if((!changed||changed==='attack')&&!part.released){
        for(const {amp,level,start} of activeAmps){
          const left=Math.max(.004,next.attack-(t-start));
          if(t-start<next.attack)redirect(amp.gain,level,t,left/3);
        }
      }
    };
    if(this.reader){
      const zones=this.reader.getZones(this.program,key,velocity);
      if(zones.length){
        for(const {sample:s,gen,index,sampleIndex} of zones){
          const src=ctx.createBufferSource(),a=gain(ctx,0),pan=ctx.createStereoPanner();
          try{src.buffer=this.reader.audioBuffer(ctx,sampleIndex)}catch(e){console.warn(e);continue}
          const root=gen[58]!==undefined?gen[58]:s.pitch;
          const tune=(gen[51]||0)+(gen[52]||0)/100-s.correction/100;
          src.playbackRate.value=2**((key-root+tune)/12);
          const db=Math.max(0,gen[48]||0)/10;const level=.52*v**1.15*10**(-db/20)/Math.sqrt(zones.length);
          const attack=clamp(2**((gen[34]??-9000)/1200),.003,2.5);
          const release=clamp(2**((gen[38]??-2500)/1200),.045,4);
          a.gain.setValueAtTime(0,now);a.gain.linearRampToValueAtTime(level,now+attack);activeAmps.push({amp:a,level,start:now});
          pan.pan.value=clamp((gen[17]||0)/500,-1,1);
          if((gen[54]||0)&1){
            const lo=Math.max(0,(s.loopStart-s.start)/s.rate),hi=Math.min(src.buffer.duration,(s.loopEnd-s.start)/s.rate);
            if(hi>lo+.01){src.loop=true;src.loopStart=lo;src.loopEnd=hi}
          }
          src.connect(a).connect(pan).connect(part.gate);part.own(a,pan);part.start(src);
          part.releaseSeconds=Math.max(part.releaseSeconds,release);
        }
        return;
      }
    }
    const type=p.native,frequency=hz(key),attack=p.attack,release=p.release;
    part.releaseSeconds=release;
    const filterNode=filter(ctx,'lowpass',clamp(2000+p.brightness*110,500,18000));
    filterNode.connect(part.gate);part.own(filterNode);
    const profiles={
      strings:[[1,.32,4.3,'sawtooth'],[2,.11,2.8,'triangle'],[1.005,.11,4,'sawtooth']],
      bells:[[1,.32,3.6,'sine'],[2.75,.19,2.4,'sine'],[5.37,.11,1.5,'sine']],
      winds:[[1,.44,1.6,'triangle'],[2,.06,1.4,'sine'],[3,.028,1.0,'sine']],
      brass:[[1,.29,1.5,'sawtooth'],[2,.13,1,'triangle'],[3,.046,.75,'sawtooth']],
      choir:[[1,.28,3,'sine'],[1.99,.09,3.1,'triangle'],[3.01,.04,2.8,'sine']]
    };
    for(const [ratio,base,tau,typeWave] of profiles[type]||profiles.strings){
      if(frequency*ratio>ctx.sampleRate*.46)continue;
      const osc=ctx.createOscillator(),amp=gain(ctx,0);
      osc.type=typeWave;osc.frequency.value=frequency*ratio;
      const volume=base*v**1.2;
      amp.gain.setValueAtTime(0,now);
      amp.gain.linearRampToValueAtTime(volume,now+(type==='bells'?.003:attack));activeAmps.push({amp,level:volume,start:now});
      if(type==='bells')amp.gain.setTargetAtTime(0,now+.012,tau);
      else if(type==='winds'||type==='brass')amp.gain.setTargetAtTime(volume*.7,now+attack,.17);
      osc.connect(amp).connect(filterNode);part.own(amp);part.start(osc,{until:now+(type==='bells'?Math.max(3,tau*9):45)});
    }
  }
}
