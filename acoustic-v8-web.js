/**
 * V8 Web PREVIEW, original Python V8 is not present in the web repository.
 * Acoustic is intentionally independent of the A/B/C/D/Classic/sample engines.
 */
import {clamp,filter,gain,smooth} from './voice.js';
export const c3xTouch=(velocity,touch=50)=>
  clamp((velocity/127)**(2**((50-touch)/55)),.001,1);
export class Acoustic{
  constructor(ctx,bus,_status,options={}){
    this.ctx=ctx;this.bus=bus;this.lite=Boolean(options.lite);
    this.input=gain(ctx,1);
    this.lid=filter(ctx,'lowpass',12500);
    this.input.connect(this.lid).connect(bus);
    this.current=null;this.node=null;this.nodePromise=null;this.quality='eco';
    this.parts=new Map();this.serial=0;this.pedalDown=false;
  }
  async prepareV8(quality='eco'){
    if(!this.ctx.audioWorklet||typeof AudioWorkletNode==='undefined')return false;
    if(this.node){this.setV8Quality(quality);return true;}
    if(!this.nodePromise){
      this.nodePromise=(async()=>{
        await this.ctx.audioWorklet.addModule('./piano-c3x-v8-web.js?build=1.13.2');
        const node=new AudioWorkletNode(this.ctx,'stage-c3x-v8-web',{
          numberOfInputs:0,numberOfOutputs:1,outputChannelCount:[2]
        });
        node.connect(this.input);
        node.port.onmessage=({data})=>{
          if(data?.type!=='done')return;
          for(const id of data.ids||[]){
            const marker=this.parts.get(id);this.parts.delete(id);
            if(marker){try{marker.stop()}catch{}}
          }
        };
        node.onprocessorerror=()=>{
          console.error('O motor V8 Web encerrou inesperadamente');
          this.node=null;this.nodePromise=null;
          for(const marker of this.parts.values())try{marker.stop()}catch{}
          this.parts.clear();
        };
        this.node=node;this.quality=null;
        this.setV8Quality(quality);
        this.sendControls(this.current);
        if(this.pedalDown)node.port.postMessage({type:'pedal',value:127});
        return true;
      })().catch(e=>{
        console.warn('Não foi possível preparar o motor físico V8 Web',e);
        this.nodePromise=null;this.node=null;return false;
      });
    }
    return this.nodePromise;
  }
  setV8Quality(quality){
    const q=['eco','balanced','studio'].includes(quality)?quality:'eco';
    if(!this.node||this.quality===q)return;
    this.quality=q;this.node.port.postMessage({type:'quality',quality:q});
  }
  sendControls(p){
    if(!this.node||!p)return;
    this.node.port.postMessage({type:'controls',
      resonance:clamp(p.resonance/100,0,1),
      damping:clamp(p.damping/100,0,1),
      brightness:clamp(p.brightness/100,0,1),
      lid:clamp(p.lid/100,0,1)});
  }
  update(p){
    this.current=p;
    this.setV8Quality(p?.physicalQuality||'eco');this.sendControls(p);
    smooth(this.lid.frequency,1900*2**((p?.lid??80)/30),this.ctx.currentTime);
  }
  setPedal(down){
    this.pedalDown=Boolean(down);
    this.node?.port.postMessage({type:'pedal',value:down?127:0});
  }
  play(part,key,velocity,p,_expression){
    if(!this.node)throw Error('Motor V8 Web não carregado. Toque em Ativar áudio.');
    if(key<21||key>108)return;
    const id=++this.serial,marker=this.ctx.createConstantSource();
    const silent=gain(this.ctx,0);
    marker.connect(silent).connect(part.gate);part.own(silent);
    const rel=clamp(p.release*(.55+.75*p.damping/100),.05,2.8);
    part.releaseSeconds=rel;
    this.parts.set(id,marker);
    part.start(marker,{pitch:false,until:this.ctx.currentTime+35});
    part.update=next=>{
      part.releaseSeconds=clamp(next.release*(.55+.75*next.damping/100),.05,2.8);
      this.node?.port.postMessage({type:'param',id,
        brightness:clamp(next.brightness/100,0,1),
        damping:clamp(next.damping/100,0,1),
        release:part.releaseSeconds});
    };
    const release=part.release.bind(part);
    part.release=(fast=false)=>{
      if(!part.released)this.node?.port.postMessage({type:'off',id,fast,release:part.releaseSeconds});
      release(fast);
    };
    this.node.port.postMessage({type:'on',id,key,
      speed:c3xTouch(velocity,p.touch),hardness:clamp(p.hammer/100,0,1),
      brightness:clamp(p.brightness/100,0,1)});
  }
}
