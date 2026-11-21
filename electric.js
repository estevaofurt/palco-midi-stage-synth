import {filter,gain,hz,saturation,smooth} from './voice.js';

export class Electric {
  constructor(ctx,bus){
    this.ctx=ctx;this.input=filter(ctx,'highpass',34);
    this.amp=ctx.createWaveShaper();this.amp.oversample='2x';
    this.speaker=filter(ctx,'lowpass',16000);
    this.presence=filter(ctx,'peaking',1700,.8);
    this.chop=gain(ctx,1);this.pan=ctx.createStereoPanner();
    this.input.connect(this.amp).connect(this.speaker).connect(this.presence).connect(this.chop).connect(this.pan).connect(bus);
    this.trem=ctx.createOscillator();this.depth=gain(ctx,0);this.width=gain(ctx,0);
    this.trem.connect(this.depth).connect(this.chop.gain);this.trem.connect(this.width).connect(this.pan.pan);this.trem.start();
  }
  update(p){
    const now=this.ctx.currentTime;
    if(this.drive!==p.drive||this.model!==p.model){
      this.amp.curve=saturation(p.drive,p.model==='reed'?.06:.025);this.drive=p.drive;this.model=p.model;
    }
    const cabinet={line:[17000,0,32],combo:[5200,2.4,58],small:[3050,4.7,115]}[p.cabinet];
    smooth(this.speaker.frequency,cabinet[0],now);smooth(this.presence.gain,cabinet[1],now);smooth(this.input.frequency,cabinet[2],now);
    const depth=p.tremolo/200;
    smooth(this.chop.gain,1-depth,now);smooth(this.depth.gain,depth,now);
    smooth(this.width.gain,depth*(p.model==='tine'?1.55:.22),now);smooth(this.trem.frequency,p.speed,now);
  }
  play(part,key,velocity,p){
    const ctx=this.ctx,now=ctx.currentTime,v=velocity/127,reed=p.model==='reed';
    const hard=p.hammer/100,pick=p.pickup/100,body=(.65+p.decay*.045)*2**((60-key)/65);
    const force=v**(1.55-hard*.4),frequency=hz(key);
    const modes=[
      [1,.28*force,body],
      [reed?2:2.002,(.018+.14*pick)*force*v,body*.60],
      [reed?3:7.02+(key-60)*.0022,(.014+.23*hard)*force*v*v,body*(reed?.35:.085)],
      [reed?5:1.0035,(reed?.094:.051)*force*(reed?v:1),body*(reed?.17:.80)]
    ];
    const pickup=ctx.createWaveShaper();
    // Bias and compression couple strike intensity to new even/odd partials.
    const shapeKey=p.model+'/'+p.pickup;
    if(this.pickupKey!==shapeKey){
      this.pickupCurve=saturation(15+pick*62,reed?.09:.035+pick*.07);
      this.pickupKey=shapeKey;
    }
    pickup.curve=this.pickupCurve;pickup.connect(part.gate);part.own(pickup);
    for(const [ratio,level,tau] of modes){
      if(frequency*ratio>=ctx.sampleRate*.46)continue;
      const osc=ctx.createOscillator(),amp=gain(ctx,0);
      osc.frequency.value=frequency*ratio;
      amp.gain.setValueAtTime(0,now);amp.gain.linearRampToValueAtTime(level,now+.0025+(1-hard)*.003);
      amp.gain.setTargetAtTime(0,now+.006,tau);osc.connect(amp).connect(pickup);part.own(amp);
      part.start(osc,{until:now+Math.min(42,8*tau+.04)});
    }
    part.releaseSeconds=.08+p.damper*.009;
  }
}
