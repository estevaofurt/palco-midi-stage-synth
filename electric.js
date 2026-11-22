import {clamp,filter,gain,hz,saturation,smooth,noiseBuffer} from './voice.js';
import {SampleLibrary} from './sample-library.js';
export class Electric{
  constructor(ctx,bus){
    this.ctx=ctx;this.input=filter(ctx,'highpass',34);
    this.amp=ctx.createWaveShaper();this.amp.oversample='2x';
    this.speaker=filter(ctx,'lowpass',16000);this.presence=filter(ctx,'peaking',1700,.8);
    this.chop=gain(ctx,1);this.pan=ctx.createStereoPanner();
    this.autoPanOsc=ctx.createOscillator();this.autoPanDepth=gain(ctx,0);
    this.autoPanOsc.type='sine';this.autoPanOsc.frequency.value=2.5;
    this.autoPanOsc.connect(this.autoPanDepth).connect(this.pan.pan);this.autoPanOsc.start();
    this.input.connect(this.amp).connect(this.speaker).connect(this.presence).connect(this.chop).connect(this.pan).connect(bus);
    this.trem=ctx.createOscillator();this.depth=gain(ctx,0);
    this.trem.connect(this.depth).connect(this.chop.gain);this.trem.start();
    this.noise=noiseBuffer(ctx,.12);this.lastPedal=0;this.samples=new SampleLibrary(ctx);
  }
  update(p){
    const now=this.ctx.currentTime;
    if(this.drive!==p.preamp||this.model!==p.model){
      this.amp.curve=saturation(p.preamp,p.model.startsWith('wurly')?.06:.025);this.drive=p.preamp;this.model=p.model;
    }
    const cabinet={line:[17000,0,32],combo:[5200,2.4,58],small:[3050,4.7,115]}[p.cabinet]||[17000,0,32];
    const mic=p.mic==='room'?.60:p.mic==='di'?1.25:1;
    smooth(this.speaker.frequency,cabinet[0]*mic,now);
    smooth(this.presence.gain,cabinet[1]+(p.mic==='close'?1.4:0),now);
    smooth(this.input.frequency,cabinet[2],now);
    const depth=p.tremolo/200;
    smooth(this.chop.gain,1-depth,now);smooth(this.depth.gain,depth,now);
    smooth(this.trem.frequency,p.speed,now);
    smooth(this.pan.pan,0,now);smooth(this.autoPanDepth.gain,Math.min(.95,p.autoPan/100),now);
    smooth(this.autoPanOsc.frequency,p.autoPanRate,now);
  }
  setPedal(down,p){
    const now=this.ctx.currentTime;if(!p?.pedalNoise||now-this.lastPedal<.07)return;
    this.lastPedal=now;const src=this.ctx.createBufferSource(),a=gain(this.ctx,p.pedalNoise*.00018);
    src.buffer=this.noise;src.connect(a).connect(this.input);a.gain.setTargetAtTime(0,now+.003,.014);
    src.onended=()=>{src.disconnect();a.disconnect()};src.start();src.stop(now+.08);
  }
  play(part,key,velocity,p){
    const ctx=this.ctx,now=ctx.currentTime,v=velocity/127;
    const reed=p.model.startsWith('wurly'),fm=p.model.startsWith('fm'),clav=p.model==='clav',cp=p.model==='cp80';
    const hard=p.hammer/100,pick=p.pickup/100;
    const body=(.65+p.decay*.045)*2**((60-key)/65)*(clav?.28:1);
    const force=v**(1.55-hard*.4),frequency=hz(key);
    let modes;
    if(fm)modes=[[1,.3,body],[2,.17*pick+(.08*hard),body*.58],[3.5,.08*v,body*.31],[8.2,.025*v,body*.12]];
    else if(clav)modes=[[1,.23,body],[2.015,.15,body*.34],[3.02,.12,body*.18],[4.03,.07,body*.1]];
    else if(cp)modes=[[1,.31,body],[2.005,.13,body*.65],[3.01,.065,body*.31]];
    else modes=[[1,.28,body],[reed?2:2.002,(.018+.14*pick)*v,body*.60],[reed?3:7.02+(key-60)*.0022,(.014+.23*hard)*v*v,body*(reed?.35:.085)],[reed?5:1.0035,(reed?.094:.051)*(reed?v:1),body*(reed?.17:.80)]];
    const pickup=ctx.createWaveShaper();const shapeKey=p.model+'/'+p.pickup;
    if(this.pickupKey!==shapeKey){this.pickupCurve=saturation(15+pick*62,reed?.09:.035+pick*.07);this.pickupKey=shapeKey}
    pickup.curve=this.pickupCurve;pickup.connect(part.gate);part.own(pickup);
    const sampled=this.samples.choose(p.model,key,velocity);
    if(sampled){
      const src=ctx.createBufferSource(),amp=gain(ctx,Math.min(.8,.34*force));
      src.buffer=sampled.buffer;src.playbackRate.value=2**((key-sampled.root)/12);
      src.connect(amp).connect(pickup);part.own(amp);part.start(src);
    }
    if(!sampled)for(const [ratio,level,tau] of modes){
      if(frequency*ratio>=ctx.sampleRate*.46)continue;
      const osc=ctx.createOscillator(),amp=gain(ctx,0);osc.frequency.value=frequency*ratio;
      amp.gain.setValueAtTime(0,now);
      amp.gain.linearRampToValueAtTime(level*force,now+.0025+(1-hard)*.003);
      amp.gain.setTargetAtTime(0,now+.006,tau);
      osc.connect(amp).connect(pickup);part.own(amp);part.start(osc,{until:now+Math.min(42,8*tau+.04)});
    }
    if(p.hammerNoise){
      const click=ctx.createBufferSource(),eq=filter(ctx,'bandpass',1200+key*17,1),a=gain(ctx,p.hammerNoise*.00023*v);
      click.buffer=this.noise;a.gain.setTargetAtTime(0,now,.006);
      click.connect(eq).connect(a).connect(part.gate);part.own(eq,a);part.start(click,{pitch:false,until:now+.045});
    }
    part.releaseSeconds=.06+p.damper*.009;
  }
}
