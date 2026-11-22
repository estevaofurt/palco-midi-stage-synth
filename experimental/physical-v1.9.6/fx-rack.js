import {engines,effectsDefinition} from './patches.js';
import {gain,filter,smooth,clamp} from './voice.js';

const TWO_PI=Math.PI*2;
const GRAPHIC=[125,250,500,1000,2000,4000,8000];
const dBToGain=db=>10**(db/20);
const seeded=(state)=>{state.value=(Math.imul(state.value,1664525)+1013904223)>>>0;return state.value/2147483648-1};

// IRs originais e determinísticos. Shimmer é um brilho harmônico aproximado,
// não um pitch shifter de oitava; essa distinção permanece na documentação.
export function impulse(ctx,seconds,type='hall',seed=179,channels=2){
  const tail=clamp(seconds,.3,3.8);
  const cfg={
    hall:{factor:1.12,pre:.018,damp:.69,decay:5.7,early:.22},
    room:{factor:.47,pre:.004,damp:.42,decay:8.6,early:.55},
    plate:{factor:.89,pre:.012,damp:.28,decay:5.2,early:.17},
    spring:{factor:.76,pre:.012,damp:.43,decay:6.6,early:.14},
    church:{factor:1.6,pre:.049,damp:.80,decay:4.8,early:.24},
    shimmer:{factor:1.32,pre:.028,damp:.22,decay:5.0,early:.13}
  }[type]||{factor:1,pre:.02,damp:.6,decay:5.7,early:.2};
  const length=Math.ceil(ctx.sampleRate*(tail*cfg.factor+cfg.pre+.05));
  const buffer=ctx.createBuffer(channels,length,ctx.sampleRate),delay=Math.round(cfg.pre*ctx.sampleRate);
  const rng={value:seed>>>0};
  // Pré-cálculo recursivo do envelope: evita três Math.exp() por amostra
  // e reduz a chance de glitches durante ajustes do reverb no palco.
  const dampingRatio=Math.exp(-cfg.decay/(ctx.sampleRate*tail*cfg.factor));
  const attackRatio=Math.exp(-260/ctx.sampleRate);
  for(let ch=0;ch<channels;ch++){
    const out=buffer.getChannelData(ch);
    let low=0,ring=0,phase=0,decay=1,attack=1;
    for(let i=delay;i<length;i++){
      const t=(i-delay)/ctx.sampleRate, raw=seeded(rng);
      low=low*cfg.damp+(1-cfg.damp)*raw;
      let signal=low*.75+raw*(type==='plate'||type==='shimmer'?.48:.2);
      if(type==='spring'){
        phase+=TWO_PI*(900+540*Math.exp(-t*18)+230*Math.sin(t*23))/ctx.sampleRate;
        ring=.9*ring+.1*Math.sin(phase);
        signal=signal*.42+ring*.52*Math.sin(t*37+ch);
      }
      if(type==='shimmer'){
        signal=signal*.5+.22*Math.sin(TWO_PI*(1777+ch*47)*t)*Math.exp(-t*.5);
      }
      out[i]=clamp(signal*decay*(1-attack)*.42,-1,1);
      decay*=dampingRatio; attack*=attackRatio;
    }
    // Reflexões iniciais curtas: calculadas só em torno dos dois impulsos,
    // não em todas as dezenas de milhares de amostras da cauda.
    for(const [time,strength] of [[.015,1],[.039,.6]]){
      const centre=delay+Math.round(time*ctx.sampleRate);
      const width=Math.ceil(.012*ctx.sampleRate);
      for(let j=-width;j<=width;j++){
        const at=centre+j;
        if(at>=0&&at<length){
          const dt=j/ctx.sampleRate;
          const early=cfg.early*strength*Math.exp(-((dt/.003)**2))*.42;
          out[at]=clamp(out[at]+early*Math.exp(-cfg.decay*time/(tail*cfg.factor)),-1,1);
        }
      }
    }
  }
  return buffer;
}
function saturator(ctx,drive=0){
  const node=ctx.createWaveShaper();node.oversample='none';node.curve=curve(drive);return node;
}
function curve(drive){
  const a=new Float32Array(1025),d=1+drive;
  for(let i=0;i<a.length;i++){
    const x=2*i/(a.length-1)-1;
    a[i]=drive===0?x:Math.tanh(d*x)/Math.tanh(d);
  }
  return a;
}
function connectChain(input,nodes,output){
  let current=input;
  for(const node of nodes){current.connect(node);current=node}
  current.connect(output);
}
function makeInsert(ctx,bus,master){
  const input=gain(ctx,1),eqDry=gain(ctx,1),eqParam=gain(ctx,0),eqGraphic=gain(ctx,0);
  // O EQ tem duas redes selecionáveis e bypass. Nunca soma uma cópia extra do sinal.
  const eqOut=gain(ctx,1);
  input.connect(eqDry).connect(eqOut);
  const bands=[
    filter(ctx,'peaking',160,.8),filter(ctx,'peaking',1000,1.2),filter(ctx,'peaking',5600,.8)
  ];
  connectChain(input,bands,eqParam);eqParam.connect(eqOut);
  const graphic=GRAPHIC.map(f=>filter(ctx,'peaking',f,1.15));
  connectChain(input,graphic,eqGraphic);eqGraphic.connect(eqOut);
  const compDry=gain(ctx,1),compWet=gain(ctx,0),makeup=gain(ctx,1);
  const comp=ctx.createDynamicsCompressor();
  eqOut.connect(compDry).connect(master);
  eqOut.connect(comp).connect(makeup).connect(compWet).connect(master);
  // O bus do motor deixa de ir diretamente ao master. Toda saída passa pelo
  // caminho único de inserts, seco quando as sessões não estão habilitadas.
  bus.disconnect(master);bus.connect(input);
  return {input,eqDry,eqParam,eqGraphic,eqOut,bands,graphic,comp,compDry,compWet,makeup};
}
function makeReverb(ctx,input,wet,id,lite=false){
  const a=ctx.createConvolver(),ga=gain(ctx,1);
  a.buffer=impulse(ctx,lite?.55:1.7,'hall',id==='reverb1'?171:431,lite?1:2);
  input.connect(a).connect(ga).connect(wet);
  if(lite){
    // Uma convolução mono curta em vez de quatro convoluções estéreo simultâneas.
    return {reverbs:[a],verbGains:[ga],activeIR:0,irKey:'hall/0.6',impulseTimer:null};
  }
  const b=ctx.createConvolver(),gb=gain(ctx,0);
  b.buffer=impulse(ctx,1.7,'hall',id==='reverb1'?173:433);
  input.connect(b).connect(gb).connect(wet);
  return {reverbs:[a,b],verbGains:[ga,gb],activeIR:0,irKey:'hall/1.7',impulseTimer:null};
}

function makeDelay(ctx,input,wet){
  const delay=ctx.createDelay(2.5),loop=gain(ctx,.25),tone=filter(ctx,'lowpass',16000),drive=saturator(ctx,0);
  input.connect(delay).connect(tone).connect(drive).connect(wet);
  drive.connect(loop).connect(delay);
  const flutter=ctx.createOscillator(),flutterDepth=gain(ctx,0);
  flutter.frequency.value=4.8;flutter.connect(flutterDepth).connect(delay.delayTime);flutter.start();
  return {delay,loop,tone,drive,flutter,flutterDepth,delayType:null};
}
function makeModulation(ctx,input,wet){
  const chorus=ctx.createDelay(.08),chorusGain=gain(ctx,0);
  chorus.delayTime.value=.021;input.connect(chorus).connect(chorusGain).connect(wet);
  const flanger=ctx.createDelay(.04),flangerGain=gain(ctx,0),feedback=gain(ctx,.28);
  flanger.delayTime.value=.004;input.connect(flanger).connect(flangerGain).connect(wet);
  flanger.connect(feedback).connect(flanger);
  const phaser=[350,650,1000,1550].map(f=>filter(ctx,'allpass',f,.8)),phaserGain=gain(ctx,0);
  connectChain(input,phaser,phaserGain);phaserGain.connect(wet);
  const wah=filter(ctx,'bandpass',850,3.5),wahGain=gain(ctx,0);
  input.connect(wah).connect(wahGain).connect(wet);
  const lfo=ctx.createOscillator(),chorusDepth=gain(ctx,0),flangerDepth=gain(ctx,0),phaserDepth=gain(ctx,0),wahDepth=gain(ctx,0);
  lfo.frequency.value=1;
  lfo.connect(chorusDepth).connect(chorus.delayTime);
  lfo.connect(flangerDepth).connect(flanger.delayTime);
  lfo.connect(phaserDepth);for(const f of phaser)phaserDepth.connect(f.frequency);
  lfo.connect(wahDepth).connect(wah.frequency);lfo.start();
  return {lfo,chorusGain,flangerGain,phaserGain,wahGain,chorusDepth,flangerDepth,phaserDepth,wahDepth,feedback,chorus,flanger,phaser,wah};
}
export class FXRack {
  constructor(ctx,master,state,buses,options={}){
    this.ctx=ctx;this.state=state;this.nodes={};this.sends={};this.inserts={};
    this.master=master;this.buses=buses;this.lite=Boolean(options.lite);
    // No modo leve, nem convolver, nem FX de modulação, nem EQ/Comp são
    // criados até que o usuário habilite o efeito num motor com FX ligado.
    for(const name of Object.keys(engines))this.inserts[name]=null;
    for(const {id,type} of effectsDefinition){
      this.sends[id]={};
      if(type==='eq'||type==='comp'){this.nodes[id]={type};continue}
      this.nodes[id]=null;
      // Todos os FX, inclusive no desktop, são criados apenas quando necessários.
    }
    this.update();
  }
  createSlot(id,type){
    if(this.nodes[id])return this.nodes[id];
    const {ctx,master,buses}=this,input=gain(ctx,1),wet=gain(ctx,0),slot={input,wet,type};
    this.nodes[id]=slot;wet.connect(master);
    for(const module of Object.keys(engines)){
      const send=gain(ctx,0);buses[module].connect(send).connect(input);this.sends[id][module]=send;
    }
    if(type==='reverb')Object.assign(slot,makeReverb(ctx,input,wet,id,this.lite));
    else if(type==='delay')Object.assign(slot,makeDelay(ctx,input,wet));
    else if(type==='mod')Object.assign(slot,makeModulation(ctx,input,wet));
    return slot;
  }
  update(){
    const now=this.ctx.currentTime;
    for(const {id,type} of effectsDefinition){
      const p=this.state.fx.slots[id];
      if(type==='eq'||type==='comp')continue;
      if(!this.nodes[id] && p.active && p.targets.some(module=>this.state.fx.enabled[module]))this.createSlot(id,type);
      const slot=this.nodes[id];if(!slot)continue;
      const amount=clamp(p.mix,0,100)/100;
      for(const [module,send] of Object.entries(this.sends[id])){
        const enabled=p.active&&p.targets.includes(module)&&this.state.fx.enabled[module];
        smooth(send.gain,enabled?1:0,now,.018);
      }
      smooth(slot.wet.gain,p.active?amount*(type==='mod'?.50:.60):0,now,.02);
      if(type==='reverb'){
        const seconds=Math.round(clamp(p.time,.3,this.lite?.65:3.8)*10)/10,key=p.reverbType+'/'+seconds.toFixed(1);
        if(slot.irKey!==key){
          clearTimeout(slot.impulseTimer);
          slot.impulseTimer=setTimeout(()=>{
            if(this.lite){
              slot.reverbs[0].buffer=impulse(this.ctx,seconds,p.reverbType,id==='reverb1'?171:431,1);
            }else{
              const next=1-slot.activeIR;
              slot.reverbs[next].buffer=impulse(this.ctx,seconds,p.reverbType,id==='reverb1'?171:431);
              smooth(slot.verbGains[next].gain,1,this.ctx.currentTime,.08);
              smooth(slot.verbGains[slot.activeIR].gain,0,this.ctx.currentTime,.08);
              slot.activeIR=next;
            }
            slot.irKey=key;
          },160);
        }
      }else if(type==='delay'){
        const kind=p.delayType||'digital';
        smooth(slot.delay.delayTime,clamp(p.time,.04,1.5),now,.025);
        smooth(slot.loop.gain,clamp(p.feedback,0,80)/100,now,.03);
        const freq=kind==='analog'?3000:kind==='tape'?5500:17500;
        smooth(slot.tone.frequency,freq,now,.04);
        smooth(slot.flutterDepth.gain,kind==='tape'?.0014:0,now,.04);
        smooth(slot.flutter.frequency,kind==='tape'?4.8:1,now,.04);
        if(slot.delayType!==kind){slot.drive.curve=curve(kind==='analog'?.7:kind==='tape'?1.3:0);slot.delayType=kind}
      }else if(type==='mod'){
        const kind=p.modType||'chorus',depth=clamp(p.depth,0,100)/100;
        smooth(slot.lfo.frequency,clamp(p.rate,.1,12),now,.04);
        for(const [name,node] of [['chorus',slot.chorusGain],['flanger',slot.flangerGain],['phaser',slot.phaserGain],['wah',slot.wahGain]]){
          smooth(node.gain,name===kind?1:0,now,.035);
        }
        smooth(slot.chorusDepth.gain,.005*depth,now,.035);
        smooth(slot.flangerDepth.gain,.003*depth,now,.035);
        smooth(slot.phaserDepth.gain,650*depth,now,.035);
        smooth(slot.wahDepth.gain,1000*depth,now,.035);
      }
    }
    // EQ e compressor são inserts reais, não efeitos paralelos que apenas elevam o volume.
    const eq=this.state.fx.slots.eq,comp=this.state.fx.slots.comp;
    for(const [module,existing] of Object.entries(this.inserts)){
      const fxOn=Boolean(this.state.fx.enabled[module]);
      const wantInsert=fxOn&&((eq.active&&eq.targets.includes(module))||(comp.active&&comp.targets.includes(module)));
      if(!existing&&wantInsert)this.inserts[module]=makeInsert(this.ctx,this.buses[module],this.master);
      const n=this.inserts[module];if(!n)continue;
      const eqOn=fxOn&&eq.active&&eq.targets.includes(module);
      const eqMix=eqOn?clamp(eq.mix,0,100)/100:0;
      smooth(n.eqDry.gain,1-eqMix,now,.025);
      smooth(n.eqParam.gain,eq.eqType==='parametric'?eqMix:0,now,.025);
      smooth(n.eqGraphic.gain,eq.eqType==='graphic'?eqMix:0,now,.025);
      for(let i=0;i<3;i++){
        const key=['low','mid','high'][i],f=n.bands[i];
        smooth(f.frequency,clamp(eq[key+'Freq'],30,16000),now,.03);
        smooth(f.Q,clamp(eq[key+'Q'],.3,8),now,.03);
        smooth(f.gain,clamp(eq[key],-15,15),now,.03);
      }
      GRAPHIC.forEach((freq,i)=>smooth(n.graphic[i].gain,clamp(eq['eq'+freq],-15,15),now,.03));
      const compOn=fxOn&&comp.active&&comp.targets.includes(module);
      const compMix=compOn?clamp(comp.mix,0,100)/100:0;
      smooth(n.compDry.gain,1-compMix,now,.025);
      smooth(n.compWet.gain,compMix,now,.025);
      smooth(n.comp.threshold,clamp(comp.threshold,-50,0),now,.03);
      smooth(n.comp.ratio,clamp(comp.ratio,1,16),now,.03);
      smooth(n.comp.attack,clamp(comp.attack,.001,.2),now,.03);
      smooth(n.comp.release,clamp(comp.release,.02,1),now,.03);
      smooth(n.comp.knee,clamp(comp.knee,0,30),now,.03);
      smooth(n.makeup.gain,dBToGain(clamp(comp.makeup,-12,18)),now,.03);
    }
  }
  // Redução de ganho negativa em dB, destinada a futuros indicadores do painel.
  reduction(module){return this.inserts[module]?.comp.reduction??0}
}
