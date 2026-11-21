import {filter,gain,hz,noiseBuffer,saturation,smooth} from './voice.js';

function rotorBand(ctx,input,output,bass){
  const type=bass?'lowpass':'highpass';
  const band=filter(ctx,type,790), slope=filter(ctx,type,790);
  const lfo=ctx.createOscillator(), merge=ctx.createChannelMerger(2);
  lfo.frequency.value=bass?.57:.78;input.connect(band).connect(slope);
  const gains=[];
  for(let ch=0;ch<2;ch++){
    const delay=ctx.createDelay(.03), mic=gain(ctx,.72), sign=ch===0?1:-1;
    delay.delayTime.value=bass?.004:.0028;
    const doppler=gain(ctx,0), amplitude=gain(ctx,0);
    lfo.connect(doppler).connect(delay.delayTime);lfo.connect(amplitude).connect(mic.gain);
    slope.connect(delay).connect(mic).connect(merge,0,ch);
    gains.push({doppler,amplitude,sign});
  }
  merge.connect(output);lfo.start();
  return (mode,width)=>{
    const now=ctx.currentTime, strength=mode==='stop'?0:width/100;
    smooth(lfo.frequency,{stop:0,slow:bass?.63:.83,fast:bass?5.1:6.7}[mode],now,bass?1.6:.48);
    for(const {doppler,amplitude,sign} of gains){
      smooth(doppler.gain,sign*strength*(bass?.00068:.00105),now,.09);
      smooth(amplitude.gain,sign*strength*(bass?.16:.30),now,.09);
    }
  };
}
export class Organ {
  constructor(ctx,bus){
    this.ctx=ctx;this.input=ctx.createWaveShaper();this.input.oversample='2x';
    const cabinet=filter(ctx,'lowpass',7300);this.input.connect(cabinet);
    this.bass=rotorBand(ctx,cabinet,bus,true);this.horn=rotorBand(ctx,cabinet,bus,false);
    this.noise=noiseBuffer(ctx,.02);this.live=new Set();
  }
  update(p){
    const bars=p.bars.join('');
    if(bars!==this.registration){
      const real=new Float32Array(17),imag=new Float32Array(17);
      [1,3,2,4,6,8,10,12,16].forEach((harmonic,i)=>{
        const position=p.bars[i];
        imag[harmonic]=position===0?0:10**((position-8)*3/20);
      });
      this.wave=this.ctx.createPeriodicWave(real,imag,{disableNormalization:true});
      for(const osc of this.live)osc.setPeriodicWave(this.wave);
      this.registration=bars;
    }
    if(this.drive!==p.drive){this.input.curve=saturation(p.drive,.018);this.drive=p.drive}
    this.bass(p.rotor,p.width);this.horn(p.rotor,p.width);
  }
  play(part,key,velocity,p,_expression,legato){
    const ctx=this.ctx,now=ctx.currentTime,f=hz(key);
    const osc=ctx.createOscillator(), draw=gain(ctx,0);
    osc.setPeriodicWave(this.wave);osc.frequency.value=f*.5;
    draw.gain.setValueAtTime(0,now);draw.gain.linearRampToValueAtTime(.073*(.8+.2*velocity/127),now+.006);
    osc.connect(draw).connect(part.gate);part.own(draw);part.start(osc);
    this.live.add(osc);const cleanup=osc.onended;
    osc.onended=()=>{this.live.delete(osc);cleanup()};
    const ratio=p.percussion==='third'?3:2;
    if(!legato&&p.percussion!=='off'&&f*ratio<ctx.sampleRate*.48){
      const perc=ctx.createOscillator(), amp=gain(ctx,.108);
      perc.frequency.value=f*ratio;amp.gain.setTargetAtTime(0,now,.092);
      perc.connect(amp).connect(part.gate);part.own(amp);part.start(perc,{until:now+.72});
    }
    if(p.click){
      const click=ctx.createBufferSource(), amp=gain(ctx,p.click*.00055*(.4+.6*velocity/127));
      const contact=filter(ctx,'bandpass',1700+key*12,.8);
      click.buffer=this.noise;amp.gain.setTargetAtTime(0,now,.0028);
      click.connect(contact).connect(amp).connect(part.gate);part.own(contact,amp);part.start(click,{pitch:false});
    }
    part.releaseSeconds=.042;
  }
}
