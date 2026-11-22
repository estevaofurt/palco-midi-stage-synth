import {clamp,filter,gain,hz,smooth,noiseBuffer,redirect} from './voice.js';
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
// Resposta modal curta do tampo harmônico: reforça regiões de corpo e
// madeira sem transformar o piano em um sintetizador com chorus.
function soundboardResponse(ctx){
  const rate=ctx.sampleRate,length=Math.round(rate*.23);
  const buffer=ctx.createBuffer(2,length,rate);
  const modes=[[87,.14],[132,.13],[196,.095],[274,.078],[367,.065],[512,.055],[748,.046],[1090,.037]];
  for(let ch=0;ch<2;ch++){
    const data=buffer.getChannelData(ch);
    for(const [j,[hz,tau]] of modes.entries()){
      const f=hz*(1+(ch?-.0015:.0015)),decay=Math.exp(-1/(rate*tau)),w=2*Math.PI*f/rate;
      let a=0,b=1;
      for(let i=0;i<length;i++){
        const next=2*Math.cos(w)*decay*a-decay*decay*b;
        b=a;a=next;
        data[i]+=next*(.00021/(1+j*.22))*(1-Math.exp(-i/(rate*.0015)));
      }
    }
  }
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
  constructor(ctx,bus,status,options={}){
    this.ctx=ctx;this.bus=bus;this.lite=Boolean(options.lite);this.bank=new PianoBank(ctx,status);this.samples=new SampleLibrary(ctx);this.noise=noiseBuffer(ctx,.13);this.lastPedal=0;
    this.input=filter(ctx,'highshelf',2450);this.lid=filter(ctx,'lowpass',14000);
    this.hammerTone=filter(ctx,'highshelf',2800);this.damperTone=filter(ctx,'lowpass',18000);
    this.input.connect(this.hammerTone).connect(this.damperTone).connect(this.lid).connect(bus);
    // Não montar três ConvolverNodes nem IRs ao inicializar o piano físico.
    // O próprio AudioWorklet já modela a ponte/tampo. Reverberação da sala
    // deve ser opt-in via rack, nunca um segundo tampo harmônico em série.
    this.strings=gain(ctx,0);this.res=gain(ctx,0);
    this.strings.connect(this.res).connect(this.input);
    this.room=gain(ctx,0);this.body=gain(ctx,0);
    this.classicSpaceReady=false;
    this.modal=null;this.modalPromise=null;this.modalParts=new Map();this.modalSerial=0;
    this.physical=null;this.physicalPromise=null;this.physicalParts=new Map();this.physicalSerial=0;this.physicalQuality=null;this.physicalMechanical=null;
    // Motor histórico v1.9.5: DSP e AudioWorklet separados. Nunca
    // substituir o original por um seletor que apenas desligue a mecânica.
    this.legacyPhysical=null;this.legacyPhysicalPromise=null;this.legacyPhysicalParts=new Map();
    this.legacyPhysicalSerial=0;this.legacyPhysicalQuality=null;
  }
  ensureClassicSpace(){
    if(this.lite||this.classicSpaceReady)return;
    this.classicSpaceReady=true;
    const ctx=this.ctx,bus=this.bus;
    this.strings.disconnect();this.res.disconnect();
    this.strings=ctx.createConvolver();this.strings.normalize=false;
    this.strings.buffer=stringResponse(ctx);
    this.res=gain(ctx,0);this.strings.connect(this.res).connect(this.input);
    const room=ctx.createConvolver();room.buffer=roomResponse(ctx);
    this.room=gain(ctx,0);this.lid.connect(room).connect(this.room).connect(bus);
    const board=ctx.createConvolver();board.normalize=false;
    board.buffer=soundboardResponse(ctx);
    this.body=gain(ctx,0);this.input.connect(board).connect(this.body).connect(bus);
  }
  async preparePhysical(quality='eco'){
    if(this.physical){this.setPhysicalQuality(quality);return true;}
    if(!this.ctx.audioWorklet||typeof AudioWorkletNode==='undefined')return false;
    if(!this.physicalPromise){
      this.physicalPromise=(async()=>{
        await this.ctx.audioWorklet.addModule('./physical-piano.js?build=1.12.4');
        const node=new AudioWorkletNode(this.ctx,'palco-physical-piano',{
          numberOfInputs:0,numberOfOutputs:2,outputChannelCount:[2,1]
        });
        node.connect(this.input,0,0);
        // Não roteamos a saída auxiliar a um Convolver de cordas duplicado.
        // A ressonância física compartilhada já é calculada pelo AudioWorklet.
        node.port.onmessage=({data})=>{
          if(data?.type!=='done')return;
          for(const id of data.ids||[]){
            const marker=this.physicalParts.get(id);
            this.physicalParts.delete(id);
            if(marker){try{marker.stop()}catch{}}
          }
        };
        node.onprocessorerror=()=>{
          console.error('Motor físico interrompido; síntese clássica permanece disponível');
          for(const marker of this.physicalParts.values())try{marker.stop()}catch{}
          this.physicalParts.clear();this.physical=null;this.physicalPromise=null;this.physicalQuality=null;this.physicalMechanical=null;
        };
        this.physical=node;
        this.setPhysicalQuality(quality);
        this.setMechanicalModel(this.current);
        if(this.lastPedalState)node.port.postMessage({type:'pedal',value:127});
        return true;
      })().catch(error=>{
        this.physicalPromise=null;
        console.warn('Motor físico indisponível; permanecendo na síntese clássica',error);
        return false;
      });
    }
    return this.physicalPromise;
  }
  async prepareLegacyPhysical(quality='eco'){
    if(this.legacyPhysical){this.setLegacyPhysicalQuality(quality);return true;}
    if(!this.ctx.audioWorklet||typeof AudioWorkletNode==='undefined')return false;
    if(!this.legacyPhysicalPromise){
      this.legacyPhysicalPromise=(async()=>{
        await this.ctx.audioWorklet.addModule('./physical-piano-legacy.js?build=1.12.4');
        const node=new AudioWorkletNode(this.ctx,'palco-physical-piano-legacy',{
          numberOfInputs:0,numberOfOutputs:2,outputChannelCount:[2,1]
        });
        node.connect(this.input,0,0);
        node.port.onmessage=({data})=>{
          if(data?.type!=='done')return;
          for(const id of data.ids||[]){
            const marker=this.legacyPhysicalParts.get(id);
            this.legacyPhysicalParts.delete(id);
            if(marker){try{marker.stop()}catch{}}
          }
        };
        node.onprocessorerror=()=>{
          console.error('Motor histórico v1.9.5 interrompido');
          for(const marker of this.legacyPhysicalParts.values())try{marker.stop()}catch{}
          this.legacyPhysicalParts.clear();this.legacyPhysical=null;
          this.legacyPhysicalPromise=null;this.legacyPhysicalQuality=null;
        };
        this.legacyPhysical=node;
        this.setLegacyPhysicalQuality(quality);
        return true;
      })().catch(error=>{
        this.legacyPhysicalPromise=null;
        console.warn('Motor anterior v1.9.5 indisponível',error);
        return false;
      });
    }
    return this.legacyPhysicalPromise;
  }
  setLegacyPhysicalQuality(quality){
    if(!this.legacyPhysical||this.legacyPhysicalQuality===quality)return;
    this.legacyPhysicalQuality=quality;
    this.legacyPhysical.port.postMessage({type:'quality',quality});
  }
  setPhysicalQuality(quality){
    if(!this.physical||this.physicalQuality===quality)return;
    this.physicalQuality=quality;
    this.physical.port.postMessage({type:'quality',quality});
  }
  setMechanicalModel(p){
    if(!this.physical)return;
    const options={type:'mechanics',enabled:p?.mechanicalModel!=='off',
      amount:clamp((p?.resonance??45)/100,0,1),sympathy:p?.stringRes!=='off'};
    const signature=JSON.stringify(options);
    if(this.physicalMechanical===signature)return;
    this.physicalMechanical=signature;
    this.physical.port.postMessage(options);
  }
  playPhysical(part,key,velocity,p,expression,useLegacy=false){
    if(!useLegacy)this.setMechanicalModel(p);
    const node=useLegacy?this.legacyPhysical:this.physical;
    const activeParts=useLegacy?this.legacyPhysicalParts:this.physicalParts;
    const id=useLegacy?++this.legacyPhysicalSerial:++this.physicalSerial,now=this.ctx.currentTime;
    const marker=this.ctx.createConstantSource(),silence=gain(this.ctx,0);
    marker.connect(silence).connect(part.gate);part.own(silence);
    part.releaseSeconds=clamp(p.release*(.55+.75*p.damping/100),.035,3);
    activeParts.set(id,marker);part.physicalId=id;
    part.start(marker,{pitch:false,until:now+65});
    const send=p.stringRes==='off'?0:(expression.pedal?.55:.08)*p.resonance/55;
    part.pedal=down=>node?.port.postMessage({type:'send',id,
      value:this.current?.stringRes==='off'?0:(down?.55:.08)*(this.current?.resonance??p.resonance)/55});
    part.update=next=>{
      part.releaseSeconds=clamp(next.release*(.55+.75*next.damping/100),.035,3);
      node?.port.postMessage({type:'param',id,
        decayScale:1.1-next.damping/160,damping:next.damping/100,
        brightness:next.brightness/100,release:part.releaseSeconds,
        send:next.stringRes==='off'?0:(expression.pedal?.55:.08)*next.resonance/55});
    };
    const release=part.release.bind(part);
    part.release=(fast=false)=>{
      if(!part.released)node?.port.postMessage({type:'off',id,fast,release:part.releaseSeconds});
      release(fast);
    };
    node.port.postMessage({type:'on',id,key,
      speed:fallbackVelocity(velocity,p.touch),hardness:clamp(p.hammer/100,0,1),
      character:p.character,decayScale:1.1-p.damping/160,
      brightness:clamp(p.brightness/100,0,1),send});
  }
  async prepareModal(){
    if(!this.lite)this.ensureClassicSpace();
    if(this.modal)return true;
    if(!this.ctx.audioWorklet||typeof AudioWorkletNode==='undefined')return false;
    if(!this.modalPromise){
      this.modalPromise=(async()=>{
        await this.ctx.audioWorklet.addModule('./piano-worklet.js?build=1.12.4');
        const node=new AudioWorkletNode(this.ctx,'palco-piano',{
          numberOfInputs:0,numberOfOutputs:2,outputChannelCount:[2,1]
        });
        node.connect(this.input,0,0);
        node.connect(this.strings,1,0);
        node.port.onmessage=({data})=>{
          if(data?.type!=='done')return;
          for(const id of data.ids||[]){
            const marker=this.modalParts.get(id);
            this.modalParts.delete(id);
            if(marker){try{marker.stop()}catch{}}
          }
        };
        node.port.onmessageerror=()=>console.warn('Falha de mensagem no motor modal');
        this.modal=node;return true;
      })().catch(e=>{this.modalPromise=null;console.warn('Motor modal indisponível',e);return false});
    }
    return this.modalPromise;
  }
  playModal(part,key,velocity,p,expression){
    const now=this.ctx.currentTime,id=++this.modalSerial;
    // A voz de controle utiliza uma fonte silenciosa; o áudio real sai do
    // AudioWorklet compartilhado. Isso preserva o ciclo de vida do Stage.
    const marker=this.ctx.createConstantSource(),silent=gain(this.ctx,0);
    marker.connect(silent).connect(part.gate);part.own(silent);
    part.releaseSeconds=clamp(p.release*(.55+.75*p.damping/100),.035,3);
    this.modalParts.set(id,marker);
    part.modalId=id;
    part.start(marker,{pitch:false,until:now+85});
    const send=p.stringRes==='off'?0:(expression.pedal?.55:.08)*p.resonance/55;
    part.pedal=down=>this.modal?.port.postMessage({type:'send',id,value:this.current?.stringRes==='off'?0:(down?.6:.08)*(this.current?.resonance??p.resonance)/55});
    part.update=(next)=>{
      part.releaseSeconds=clamp(next.release*(.55+.75*next.damping/100),.035,3);
      const send=next.stringRes==='off'?0:(expression.pedal?.55:.08)*next.resonance/55;
      this.modal?.port.postMessage({type:'send',id,value:send});
      this.modal?.port.postMessage({type:'param',id,decayScale:1.1-next.damping/160});
    };
    const release=part.release.bind(part);
    part.release=(fast=false)=>{
      if(!part.released)this.modal?.port.postMessage({type:'off',id,fast,release:part.releaseSeconds});
      release(fast);
    };
    this.modal.port.postMessage({type:'on',id,key,
      speed:fallbackVelocity(velocity,p.touch),hardness:clamp(p.hammer/100,0,1),
      character:p.character,decayScale:1.1-p.damping/160,
      brightness:clamp(p.brightness/100,0,1),send
    });
  }
  update(p){
    const now=this.ctx.currentTime;
    this.current=p;
    if(p.soundEngine==='physical'){this.setPhysicalQuality(p.physicalQuality||'eco');this.setMechanicalModel(p);}
    if(p.soundEngine==='physicalLegacy')this.setLegacyPhysicalQuality(p.physicalQuality||'eco');
    const classic=p.soundEngine==='classic'||p.soundEngine==='modal';
    if(classic)this.ensureClassicSpace();
    smooth(this.input.gain,(p.brightness-50)*.15,now);
    smooth(this.hammerTone.gain,(p.hammer-50)*.16,now);
    smooth(this.damperTone.frequency,Math.max(1900,18000-140*p.damping),now);
    smooth(this.lid.frequency,2600*2**(p.lid/37),now);
    smooth(this.res.gain,!classic||this.lite?0:(p.stringRes==='off'?0:p.resonance*.017),now);smooth(this.room.gain,!classic||this.lite?0:p.room*.006,now);smooth(this.body.gain,!classic||this.lite?0:(p.character==='felt'?.12:.19)*(.5+p.resonance/100),now);
  }
  setPedal(down,p){
    this.lastPedalState=Boolean(down);
    if(this.physical)this.physical.port.postMessage({type:'pedal',value:down?127:0});
    // O motor legado recebe sustain por mensagens 'send' de cada parte MIDI.
    // Sua API v1.9.5 não possuía o tipo de mensagem 'pedal'.
    const now=this.ctx.currentTime;
    if(now-this.lastPedal<.07||!p?.pedalNoise)return;
    this.lastPedal=now;
    const src=this.ctx.createBufferSource(),eq=filter(this.ctx,'lowpass',down?330:580),vol=gain(this.ctx,p.pedalNoise*.00015);
    src.buffer=this.noise;src.connect(eq).connect(vol).connect(this.input);
    vol.gain.setTargetAtTime(0,now+.008,.018);
    src.onended=()=>{src.disconnect();eq.disconnect();vol.disconnect()};src.start();src.stop(now+.12);
  }
  play(part,key,velocity,p,expression){
    if(p.soundEngine==='physical'&&this.physical)return this.playPhysical(part,key,velocity,p,expression);
    if(p.soundEngine==='physicalLegacy'&&this.legacyPhysical)return this.playPhysical(part,key,velocity,p,expression,true);
    if(p.soundEngine==='modal'&&this.modal)return this.playModal(part,key,velocity,p,expression);
    const now=this.ctx.currentTime;
    part.releaseSeconds=clamp(p.release*(.55+.75*p.damping/100)*2**((54-key)/110),.035,4);
    const send=gain(this.ctx,expression.pedal?.92:.12);
    part.gate.connect(send).connect(this.strings);part.own(send);
    part.pedal=down=>smooth(send.gain,down?.92:.12,this.ctx.currentTime,.04);
    const decayers=[];
    part.update=(next,changed)=>{
      part.releaseSeconds=clamp(next.release*(.55+.75*next.damping/100)*2**((54-key)/110),.035,4);
      if(!changed||changed==='stringRes'||changed==='resonance')smooth(send.gain,next.stringRes==='off'?0:(expression.pedal?.92:.12),this.ctx.currentTime,.035);
      if((!changed||changed==='damping')&&!part.released){
        const t=this.ctx.currentTime;
        for(const [amp,tau] of decayers)redirect(amp.gain,0,t,tau*Math.max(.18,1.2-next.damping/100));
      }
    };
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
      for(const [ratio,mix,tau] of (this.lite?partials.slice(0,2):partials)){
        if(freq*ratio>=this.ctx.sampleRate*.46)continue;
        const osc=this.ctx.createOscillator(),amp=gain(this.ctx,0);
        osc.frequency.value=freq*stretched(ratio);
        amp.gain.setValueAtTime(0,now);
        amp.gain.linearRampToValueAtTime(mix*force,now+strike);
        amp.gain.setTargetAtTime(0,now+strike+.001,tau*decay);decayers.push([amp,tau*decay]);
        osc.connect(amp).connect(part.gate);part.own(amp);
        part.start(osc,{until:now+Math.min(26,tau*decay*8)});
      }
      if(model.strings>1 && key>34){
        // Two quiet unisons create natural low-rate beating without applying
        // a global chorus to the entire instrument.
        for(const cents of (this.lite?[-.65]:[-.65,.71])){
          const osc=this.ctx.createOscillator(),amp=gain(this.ctx,0);
          osc.frequency.value=freq;osc.detune.value=cents*(.65+key/100);
          amp.gain.setValueAtTime(0,now);
          amp.gain.linearRampToValueAtTime(.095*force*model.body,now+strike*.85);
          amp.gain.setTargetAtTime(0,now+strike+.001,decay*2.05);decayers.push([amp,decay*2.05]);
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
