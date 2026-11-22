import {engines,maskForChannel} from './patches.js';
import {gain,Part,smooth} from './voice.js';
import {Acoustic} from './acoustic.js';
import {Electric} from './electric.js';
import {Organ} from './organ.js';
import {Synth} from './synth.js';
import {SoundFontEngine} from './sf-engine.js';
import {FXRack} from './fx-rack.js';
import {installOutputProtection} from './antclip.js';
import {profilePolyphony} from './audio-profile.js';

export const MAX_POLYPHONY=64;

export class Stage {
  constructor(ctx,state,{bank=()=>{},note=()=>{},pedal=()=>{}}={},options={}){
    this.ctx=ctx;this.state=state;this.noteChanged=note;this.pedalChanged=pedal;
    this.lite=options.profile==='lite';this.voiceLimit=profilePolyphony(options.profile);
    this.voices=new Map();this.groups=new Map();this.serial=0;
    this.master=ctx.createDynamicsCompressor();
    this.master.threshold.value=-9;this.master.knee.value=9;
    this.master.ratio.value=5;this.master.attack.value=.004;this.master.release.value=.14;
    // Nunca enviar a soma dos motores e FX diretamente à placa de som.
    // O limitador final protege picos de transientes e múltiplos retornos FX.
    this.output=installOutputProtection(ctx,this.master,ctx.destination,{lite:this.lite});
    this.meter=ctx.createAnalyser();this.meter.fftSize=256;this.output.limiter.connect(this.meter);
    this.buses={};
    for(const name of Object.keys(engines)){
      const bus=gain(ctx,this.state.patches[name].level/100);bus.connect(this.master);this.buses[name]=bus;
    }
    this.instruments={
      piano:new Acoustic(ctx,this.buses.piano,bank,{lite:this.lite}),
      electric:new Electric(ctx,this.buses.electric,{lite:this.lite}),
      organ:new Organ(ctx,this.buses.organ,{lite:this.lite}),
      synth:new Synth(ctx,this.buses.synth,{lite:this.lite}),
      sf:new SoundFontEngine(ctx,this.buses.sf,{lite:this.lite})
    };
    this.fx=new FXRack(ctx,this.master,this.state,this.buses,{lite:this.lite});
    for(const name of Object.keys(engines))this.update(name);
  }
  activeVoiceLimit(_mask=this.state.mask){
    // 32 playable MIDI notes is a floor, even for mobile and layered scenes.
    // Engine-specific quality (waveguides/unison/FX) is adapted independently.
    return this.voiceLimit;
  }
  update(name,changed){
    const patch=this.state.patches[name];
    smooth(this.buses[name].gain,patch.level/100,this.ctx.currentTime);
    if(changed==='level')return;
    this.instruments[name].update(patch.values,changed);
    for(const v of this.voices.values()){
      const part=v.parts.get(name);
      if(part&&!part.ended)part.update?.(patch.values,changed);
    }
    if(name==='synth'&&changed==='voiceMode'&&patch.values.voiceMode!=='poly'){
      // Alternar de poli para mono/legato também deve limitar as vozes já ativas.
      const byGroup=new Map();
      for(const v of this.voices.values()){
        if(!v.held||!v.parts.has('synth'))continue;
        const prior=byGroup.get(v.group);
        if(prior){
          const old=prior.parts.get('synth');old?.release(true);
          if(prior.parts.size===1)prior.held=false;
        }
        byGroup.set(v.group,v);
      }
    }
  }
  updateEffects(){this.fx.update()}
  group(source,channel){
    const id=source+'/'+channel;
    if(!this.groups.has(id)){
      const pitch=this.ctx.createConstantSource(),vibr=this.ctx.createOscillator();
      const depth=gain(this.ctx,0),signal=gain(this.ctx,1),pressure=this.ctx.createConstantSource();
      pitch.offset.value=0;vibr.frequency.value=5.5;
      pitch.connect(signal);vibr.connect(depth).connect(signal);pitch.start();vibr.start();pressure.offset.value=0;pressure.start();
      this.groups.set(id,{source,pitch,vibr,depth,signal,pressure,pedal:false,channel});
    }
    return this.groups.get(id);
  }
  startNote(source,channel,key,velocity,forced){
    if(this.ctx.state!=='running'||!Number.isInteger(key)||key<0||key>127||!Number.isFinite(velocity)||velocity<=0)return;
    const mask=forced??maskForChannel(this.state,channel);
    if(!mask)return;
    const group=this.group(source,channel);
    const playing=[...this.voices.values()];
    if(playing.length>=this.activeVoiceLimit(mask)){
      const steal=playing.find(v=>!v.held) || playing[0];
      this.stopVoice(steal,true);this.voices.delete(steal.id);
    }
    const legato=playing.some(v=>v.group===group&&v.held&&v.parts.has('synth')&&!v.parts.get('synth').released);
    if((mask&engines.synth.bit)&&this.state.patches.synth.values.voiceMode!=='poly'){
      for(const prior of playing)if(prior.group===group&&prior.parts.has('synth')){
        prior.parts.get('synth').release(true);
        if(!prior.parts.has('organ')&&!prior.parts.has('piano')&&!prior.parts.has('electric')&&!prior.parts.has('sf'))prior.held=false;
      }
    }
    const v={id:++this.serial,group,key,held:true,parts:new Map()};
    this.voices.set(v.id,v);
    for(const [name,{bit}] of Object.entries(engines)){
      if(!(mask&bit))continue;
      const instrument=this.instruments[name], p=this.state.patches[name].values;
      const part=new Part(this.ctx,instrument.input,group,()=>{
        v.parts.delete(name);
        if(!v.parts.size){this.voices.delete(v.id);this.noteChanged()}
      });
      v.parts.set(name,part);
      try{
        instrument.play(part,key,velocity,p,group,legato);
      }catch(error){
        // A faulty voice must never leave a stuck MIDI note or take down the app.
        part.release(true);v.parts.delete(name);
        console.error('Falha no instrumento '+name,error);
      }
      if(!part.sources.size){
        part.gate.disconnect();v.parts.delete(name);
      }
    }
    if(!v.parts.size){this.voices.delete(v.id);this.noteChanged();return;}
    this.noteChanged();
    return v.id;
  }
  stopVoice(v,fast=false){
    if(!v)return;
    v.held=false;
    for(const [name,part] of v.parts){
      if(fast||!v.group.pedal||name==='organ')part.release(fast);
    }
    this.noteChanged();
  }
  releaseId(id){this.stopVoice(this.voices.get(id))}
  voiceStats(){
    let held=0;for(const v of this.voices.values())if(v.held)held++;
    return {active:this.voices.size,held,limit:this.activeVoiceLimit()};
  }
  setPedal(group,down){
    if(group.pedal===down)return;
    group.pedal=down;
    for(const id of ['piano','electric'])if(this.state.mask&engines[id].bit){
      this.instruments[id].setPedal?.(down,this.state.patches[id].values);
    }
    for(const v of this.voices.values())if(v.group===group){
      for(const part of v.parts.values())part.pedal?.(down);
      if(!down&&!v.held)this.stopVoice(v);
    }
    this.pedalChanged();
  }
  applyRouting(){
    for(const v of this.voices.values()){
      if(v.group.source==='preview')continue;
      const mask=maskForChannel(this.state,v.group.channel);
      for(const [name,part] of v.parts)if(!(mask&engines[name].bit))part.release(true);
    }
  }
  message(source,data){
    if(!data||data.length<2)return;
    const [status,a,b=0]=data,ch=status&15,op=status&240;
    if(!Number.isInteger(status)||status<128||status>239||a>127||b>127)return;
    if(op===208){const g=this.group(source,ch);smooth(g.pressure.offset,a/127,this.ctx.currentTime,.012);return}
    if(op===144&&b>0)return this.startNote(source,ch,a,b);
    if(op!==128&&op!==144&&op!==176&&op!==224)return;
    const group=this.group(source,ch);
    if(op===128||op===144){
      for(const v of this.voices.values())if(v.group===group&&v.key===a&&v.held){this.stopVoice(v);break}
    }else if(op===224){
      const delta=((b<<7)|a)-8192;
      smooth(group.pitch.offset,200*delta/(delta<0?8192:8191),this.ctx.currentTime,.008);
    }else if(a===1)smooth(group.depth.gain,50*b/127,this.ctx.currentTime,.012);
    else if(a===64)this.setPedal(group,b>=64);
    else if(a===121){
      smooth(group.pitch.offset,0,this.ctx.currentTime,.008);
      smooth(group.depth.gain,0,this.ctx.currentTime,.008);this.setPedal(group,false);
    }else if(a===120||a===123){
      for(const v of this.voices.values())if(v.group===group)this.stopVoice(v,a===120);
    }
  }
  disconnect(source){
    for(const v of this.voices.values())if(v.group.source===source)this.stopVoice(v,true);
    for(const [key,g] of this.groups)if(g.source===source){
      this.instruments.synth?.forget(g);
      g.pitch.stop();g.vibr.stop();g.pressure.stop();g.pitch.disconnect();g.vibr.disconnect();g.depth.disconnect();g.pressure.disconnect();
      // Part cleanup disconnects its individual detune destination after its release ramp.
      this.groups.delete(key);
    }
    this.pedalChanged();
  }
  panic(){
    for(const g of new Set([...this.groups.values()].map(v=>v.source)))this.disconnect(g);
    this.noteChanged();
  }
}
