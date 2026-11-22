import {clamp,filter,gain,hz,smooth,noiseBuffer} from './voice.js';
import {PianoBank} from './piano-bank.js';
import {SampleLibrary} from './sample-library.js';

function stringResponse(ctx){
  const rate=ctx.sampleRate, length=Math.round(rate*.72);
  const buffer=ctx.createBuffer(1,length,rate), data=buffer.getChannelData(0);
  for(let key=40;key<88;key++){
    const tau=.22+(88-key)*.003, r=Math.exp(-1/(tau*rate));
    const phase=2*Math.PI*hz(key)/rate, a=2*r*Math.cos(phase);
    let last=0,before=-Math.sin(phase)*2/(rate*tau);
    for(let i=0;i<length;i++){
      const next=a*last-r*r*before;
      data[i]+=next;before=last;last=next;
    }
  }
  for(let i=0;i<length;i++)data[i]*=Math.min(1,i/(rate*.008),(length-i)/(rate*.08));
  return buffer;
}
function roomResponse(ctx){
  const rate=ctx.sampleRate, buffer=ctx.createBuffer(2,Math.round(rate*.64),rate);
  let seed=9133;
  for(let ch=0;ch<2;ch++){
    const a=buffer.getChannelData(ch);let low=0;
    for(let i=Math.round(rate*.014);i<a.length;i++){
      seed=(1664525*seed+1013904223)>>>0;low=.63*low+.37*(seed/2147483648-1);
      a[i]=low*Math.exp(-i/(rate*.087));
    }
    for(const [j,delay] of [.017,.027,.039,.058].entries())a[Math.round((delay+ch*.0009)*rate)]+=(j%2?-.9:1)/(1+j*.3);
  }
  return buffer;
}
// Mapeamento da intensidade MIDI consistente com o controle de toque.
export function fallbackVelocity(velocity,touch){
  return clamp((velocity/127)**(2**((50-touch)/55)),.001,1);
}
export class Acoustic {
  constructor(ctx,bus,status){
    this.ctx=ctx;this.bank=new PianoBank(ctx,status);this.samples=new SampleLibrary(ctx);this.noise=noiseBuffer(ctx,.13);this.lastPedal=0;
    this.input=filter(ctx,'highshelf',2450);this.lid=filter(ctx,'lowpass',14000);
    this.input.connect(this.lid).connect(bus);
    this.strings=ctx.createConvolver();this.strings.normalize=false;this.strings.buffer=stringResponse(ctx);
    this.res=gain(ctx,.3);this.strings.connect(this.res).connect(this.input);
    const room=ctx.createConvolver();room.buffer=roomResponse(ctx);
    this.room=gain(ctx,.10);this.lid.connect(room).connect(this.room).connect(bus);
  }
  update(p){
    const now=this.ctx.currentTime;
    smooth(this.input.gain,(p.brightness-50)*.15,now);
    smooth(this.lid.frequency,2600*2**(p.lid/37),now);
    smooth(this.res.gain,p.stringRes==='off'?0:p.resonance*.017,now);smooth(this.room.gain,p.room*.006,now);
  }
  setPedal(down,p){
    const now=this.ctx.currentTime;
    if(now-this.lastPedal<.07||!p?.pedalNoise)return;
    this.lastPedal=now;
    const src=this.ctx.createBufferSource(),eq=filter(this.ctx,'lowpass',down?330:580),vol=gain(this.ctx,p.pedalNoise*.00015);
    src.buffer=this.noise;src.connect(eq).connect(vol).connect(this.input);
    vol.gain.setTargetAtTime(0,now+.008,.018);
    src.onended=()=>{src.disconnect();eq.disconnect();vol.disconnect()};src.start();src.stop(now+.12);
  }
  play(part,key,velocity,p,expression){
    const now=this.ctx.currentTime;
    part.releaseSeconds=clamp(p.release*(.55+.75*p.damping/100)*2**((54-key)/110),.035,4);
    const send=gain(this.ctx,expression.pedal?.92:.12);
    part.gate.connect(send).connect(this.strings);part.own(send);
    part.pedal=down=>smooth(send.gain,down?.92:.12,this.ctx.currentTime,.04);
    if(p.hammerNoise){
      const click=this.ctx.createBufferSource(),eq=filter(this.ctx,'bandpass',1100+key*19,1.3),a=gain(this.ctx,.00038*p.hammerNoise*(velocity/127));
      click.buffer=this.noise;a.gain.setTargetAtTime(0,now+.002,.003);
      click.connect(eq).connect(a).connect(part.gate);part.own(eq,a);part.start(click,{pitch:false,until:now+.036});
    }
    if(this.samples.play(p.character,part,key,velocity,.42+fallbackVelocity(velocity,p.touch)*.32)){
      return;
    }
    const regions=this.bank.layers(key,velocity,p);
    if(!regions.length){
      // Apply the same touch response when the recorded piano bank is unavailable.
      // Hammer hardness changes the attack and overtone balance independently of volume.
      const force=fallbackVelocity(velocity,p.touch);
      const hardness=clamp(p.hammer/100,0,1);
      const character=p.character||'japanese';
      const model={
        japanese:{body:1.12,metal:.95,decay:1.11,inharm:.00013,strings:3},
        american:{body:1.01,metal:.77,decay:1.19,inharm:.00022,strings:3},
        felt:{body:.76,metal:.22,decay:.83,inharm:.00012,strings:2},
        upright:{body:.93,metal:.63,decay:.85,inharm:.00037,strings:2}
      }[character]||{body:1,metal:1,decay:1,inharm:.0002,strings:2};
      const strike=(.0025+.0055*(1-hardness))*(character==='felt'?2.1:1);
      const decay=2**((60-key)/105)*model.decay;
      const freq=hz(key);
      // Stretched string partials and small, slow detunings model the beating
      // of multiple strings. Unlike a pure harmonic organ tone, piano strings
      // have inharmonicity increasing with partial number and register.
      const B=model.inharm*2**((key-60)/21);
      const stretched=n=>n*Math.sqrt((1+B*n*n)/(1+B));
      const partials=[
        [1,.245*model.body,2.15],
        [2,(.048+.125*hardness*force)*model.metal,.72],
        [3,(.012+.09*hardness*force)*model.metal,.34],
        [4,(.004+.035*hardness*force)*model.metal,.20],
        [5,(.003+.014*hardness*force)*model.metal,.11]
      ];
      for(const [ratio,mix,tau] of partials){
        if(freq*ratio>=this.ctx.sampleRate*.46)continue;
        const osc=this.ctx.createOscillator(),amp=gain(this.ctx,0);
        osc.frequency.value=freq*stretched(ratio);
        amp.gain.setValueAtTime(0,now);
        amp.gain.linearRampToValueAtTime(mix*force,now+strike);
        amp.gain.setTargetAtTime(0,now+strike+.001,tau*decay);
        osc.connect(amp).connect(part.gate);part.own(amp);
        part.start(osc,{until:now+Math.min(26,tau*decay*8)});
      }
      if(model.strings>1 && key>34){
        // Two quiet unisons create natural low-rate beating without applying
        // a global chorus to the entire instrument.
        for(const cents of [-.65,.71]){
          const osc=this.ctx.createOscillator(),amp=gain(this.ctx,0);
          osc.frequency.value=freq;osc.detune.value=cents*(.65+key/100);
          amp.gain.setValueAtTime(0,now);
          amp.gain.linearRampToValueAtTime(.095*force*model.body,now+strike*.85);
          amp.gain.setTargetAtTime(0,now+strike+.001,decay*2.05);
          osc.connect(amp).connect(part.gate);part.own(amp);
          part.start(osc,{until:now+Math.min(27,decay*16)});
        }
      }
      return;
    }
    for(const {record,full,weight,rate} of regions){
      const src=this.ctx.createBufferSource(), amp=gain(this.ctx,.65*weight);
      src.buffer=full||this.bank.atlas;src.playbackRate.value=rate;
      src.connect(amp).connect(part.gate);part.own(amp);
      if(full){part.start(src,{offset:record.onset});continue}
      src.loop=true;src.loopStart=record.start+record.loopStart;src.loopEnd=record.start+record.loopEnd;
      const tau=record.tau/rate;
      amp.gain.setTargetAtTime(0,now+record.loopStart/rate,tau);
      part.start(src,{offset:record.start,until:now+Math.min(60,record.loopStart/rate+9*tau)});
    }
  }
}
