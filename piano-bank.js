import {clamp} from './voice.js';

const layers=[3,8,14];
const nominal=[30,70,113];
const cacheLimit=44*1024*1024;
const base=new URL('./piano/',import.meta.url);
export class PianoBank {
  constructor(ctx,status){
    this.ctx=ctx;this.status=status;this.records=new Map();this.full=new Map();
    this.pending=new Set();this.failed=new Map();this.queue=[];this.active=0;this.bytes=0;
  }
  async load(){
    if(this.atlas||this.unavailable)return;
    if(this.loading)return this.loading;
    this.status('Carregando as gravações do piano…');
    this.loading=(async()=>{
      try{
        const options=typeof AbortSignal.timeout==='function'?{signal:AbortSignal.timeout(20000)}:{};
        const manifest=await fetch(new URL('banco.json',base),options);
        if(!manifest.ok)throw Error('banco indisponível');
        const audio=await fetch(new URL('ataques.ogg',base),options);
        if(!audio.ok)throw Error('áudio do banco indisponível');
        const [index,encoded]=await Promise.all([manifest.json(),audio.arrayBuffer()]);
        const Offline=window.OfflineAudioContext||window.webkitOfflineAudioContext;
        this.decoder=Offline?new Offline(2,1,32000):this.ctx;
        const buffer=await this.decoder.decodeAudioData(encoded);
        if(index.length!==90||buffer.duration<index.at(-1).start+index.at(-1).loopEnd-.015)throw Error('banco incompleto');
        for(const record of index)this.records.set(record.file,record);
        this.atlas=buffer;
        this.status('Cauda estéreo · 3 camadas de toque');
      }catch{
        // A publicação pode não incluir as gravações licenciadas.
        // Neste caso, usar o gerador de piano existente sem requisições repetidas.
        this.unavailable=true;
        this.status('Piano de síntese ativo · gravações não incluídas nesta versão');
      }
      finally{this.loading=null}
    })();
    return this.loading;
  }
  layers(key,velocity,p){
    if(!this.atlas)return [];
    const root=clamp(21+3*Math.round((key-21)/3),21,108);
    const dynamic=127*(velocity/127)**(2**((p.touch-50)/72));
    const color=clamp(dynamic+(p.hammer-50)*.39,1,127);
    const high=color<70?1:2, low=high-1;
    const blend=clamp((color-(nominal[low]+nominal[high])/2+14)/28,0,1);
    const result=[];
    for(const [i,weight] of [[low,Math.cos(blend*Math.PI/2)],[high,Math.sin(blend*Math.PI/2)]]){
      if(weight<.01)continue;
      const file='n'+root+'v'+layers[i]+'.mp3';
      const record=this.records.get(file);
      const full=this.full.get(file);
      if(full){this.full.delete(file);this.full.set(file,full)}
      else this.request(file);
      result.push({record,full,weight:weight*clamp((dynamic/nominal[i])**.85,.015,1.8),rate:2**((key-root)/12)});
    }
    return result;
  }
  request(file){
    if(this.pending.has(file)||Date.now()<(this.failed.get(file)||0))return;
    if(this.queue.length>=10)this.pending.delete(this.queue.shift());
    this.pending.add(file);this.queue.push(file);this.pump();
  }
  pump(){
    while(this.active<2&&this.queue.length){
      const file=this.queue.shift();this.active++;
      this.loadTail(file).finally(()=>{this.pending.delete(file);this.active--;this.pump()});
    }
  }
  async loadTail(file){
    try{
      const options=typeof AbortSignal.timeout==='function'?{signal:AbortSignal.timeout(15000)}:{};
      const res=await fetch(new URL(file,base),options);if(!res.ok)throw Error('sample');
      const audio=await this.decoder.decodeAudioData(await res.arrayBuffer());
      this.full.set(file,audio);this.bytes+=audio.length*audio.numberOfChannels*4;
      while(this.bytes>cacheLimit&&this.full.size>1){
        const [name,old]=this.full.entries().next().value;
        this.bytes-=old.length*old.numberOfChannels*4;this.full.delete(name);
      }
    }catch{this.failed.set(file,Date.now()+30000)}
  }
}
