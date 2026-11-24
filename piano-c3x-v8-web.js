/**
 * C3X V8 Web — EXPERIMENTAL BROWSER PORT, NOT THE PYTHON V8 REFERENCE.
 *
 * This is an independent physical-model sketch implementing the known V8
 * design constraints (dry output, no PCM samples, real-time hammer/strings,
 * passive decay, CC64 damping and precomputed integrator coefficients).
 *
 * The separate Python C3X V8 source/bundle has not been supplied here:
 * no bit-exact equivalence or acoustic calibration is claimed.
 */
const PI=Math.PI,TAU=2*PI;
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export const V8_QUALITY=Object.freeze({
  eco:{voices:32,partials:6},
  balanced:{voices:48,partials:8},
  studio:{voices:64,partials:10}
});
export const midiHz=key=>440*2**((key-69)/12);

export function c3xV8Config(key,sampleRate=48000,quality='eco'){
  if(!Number.isInteger(key)||key<21||key>108)throw RangeError('C3X is an 88-key A0-C8 piano');
  if(!Number.isFinite(sampleRate)||sampleRate<22050||sampleRate>192000)throw RangeError('sample rate');
  const spec=V8_QUALITY[quality]||V8_QUALITY.eco;
  const fundamental=midiHz(key),unisons=key<40?1:key<53?2:3;
  const B=clamp(.00015*2**((key-56)/25),.000055,.0055);
  const maxHarmonics=Math.min(spec.partials,Math.floor(sampleRate*.43/fundamental));
  const count=Math.max(1,maxHarmonics)*unisons;
  const cos=new Float64Array(count),sin=new Float64Array(count),
    decay=new Float64Array(count),weights=new Float64Array(count),
    strike=new Float64Array(count),left=new Float64Array(count),
    right=new Float64Array(count);
  let idx=0;
  for(let s=0;s<unisons;s++){
    const cents=unisons===1?0:(s-(unisons-1)/2)*.94;
    const spatial=clamp((key-63)/70+(s-(unisons-1)/2)*.16,-.72,.72);
    for(let n=1;n<=maxHarmonics;n++){
      const ratio=n*Math.sqrt((1+B*n*n)/(1+B));
      const freq=fundamental*ratio*2**(cents/1200);
      const theta=TAU*freq/sampleRate;
      cos[idx]=Math.cos(theta);sin[idx]=Math.sin(theta);
      const tau=(key<48?5.5:3.9)*2**((61-key)/112)/(1+.29*(n-1));
      decay[idx]=Math.exp(-1/(tau*sampleRate));
      const hitPosition=key<44?.125:.117;
      const scale=Math.sin(n*PI*hitPosition);
      strike[idx]=scale/((n**1.04)*unisons);
      weights[idx]=(1/(n**.46))*1.16;
      left[idx]=Math.sqrt((1-spatial)/2);right[idx]=Math.sqrt((1+spatial)/2);
      idx++;
    }
  }
  return {key,fundamental,unisons,B,partials:maxHarmonics,count,
    cos,sin,decay,weights,strike,left,right};
}
export class C3XV8Engine{
  constructor(sr=48000,quality='eco'){
    this.sr=sr;this.quality=V8_QUALITY[quality]?quality:'eco';
    this.maxVoices=V8_QUALITY[this.quality].voices;
    this.voices=[];this.done=[];this.banks=new Map();
    this.pedal=false;this.resonance=.46;this.damping=.38;
    this.brightness=.53;this.lid=.8;
    this.body=this.createBody();
    this.bodyReaction=0;
  }
  createBody(){
    // Dry soundboard/bridge radiation, not a room-reverb impulse response.
    const spec=[[89,.14,.43],[132,.17,.37],[202,.10,.27],
      [274,.086,.25],[390,.068,.17],[585,.051,.12],
      [830,.043,.095],[1270,.032,.068]];
    return spec.map(([freq,tau,weight],i)=>{
      const a=TAU*freq/this.sr;
      return {c:Math.cos(a),s:Math.sin(a),
        r:Math.exp(-1/(tau*this.sr)),weight,lr:0,li:0,rr:0,ri:0,
        pan:(i%2?-.12:.12)};
    });
  }
  config(key){
    const id=key+':'+this.quality+':'+this.sr;
    if(!this.banks.has(id))this.banks.set(id,c3xV8Config(key,this.sr,this.quality));
    return this.banks.get(id);
  }
  setQuality(quality){
    if(!V8_QUALITY[quality])return;
    this.quality=quality;this.maxVoices=V8_QUALITY[quality].voices;
    while(this.voices.length>this.maxVoices){
      const v=this.voices.shift();this.done.push(v.id);
    }
  }
  setControls({resonance,damping,brightness,lid}={}){
    if(Number.isFinite(resonance))this.resonance=clamp(resonance,0,1);
    if(Number.isFinite(damping))this.damping=clamp(damping,0,1);
    if(Number.isFinite(brightness))this.brightness=clamp(brightness,0,1);
    if(Number.isFinite(lid))this.lid=clamp(lid,0,1);
  }
  setSustain(value){
    const old=this.pedal;this.pedal=Number(value)>=64;
    if(old&&!this.pedal)for(const v of this.voices)if(v.released)v.damped=true;
  }
  noteOn({id,key,speed=.7,hardness=.5,brightness=.5}={}){
    if(!Number.isInteger(id)||!Number.isInteger(key)||key<21||key>108)return false;
    if(this.voices.some(v=>v.id===id))this.noteOff(id,true,.02);
    if(this.voices.length>=this.maxVoices){
      const ix=this.voices.findIndex(v=>v.released);
      const [old]=this.voices.splice(ix>=0?ix:0,1);
      this.done.push(old.id);
    }
    const cfg=this.config(key),v=clamp(Number(speed)||.001,.001,1);
    const hard=clamp(Number(hardness)||0,0,1);
    const m={
      id,key,cfg,real:new Float64Array(cfg.count),imag:new Float64Array(cfg.count),
      speed:v,hardness:hard,brightness:clamp(Number(brightness)||0,0,1),
      released:false,damped:false,fast:false,age:0,
      contact:Math.max(18,Math.round(this.sr*(.0011+.0024*(1-hard))*(1.1-.3*v))),
      energy:0,silence:0,release:.24,dampGain:1
    };
    this.voices.push(m);return true;
  }
  noteOff(id,fast=false,release=.24){
    const v=this.voices.find(x=>x.id===id);if(!v)return;
    v.released=true;v.fast=Boolean(fast);
    v.release=clamp(Number(release)||.24,.02,3);
    v.damped=fast||!this.pedal;
  }
  updateVoice(id,{brightness,damping,release}={}){
    const v=this.voices.find(x=>x.id===id);if(!v)return;
    if(Number.isFinite(brightness))v.brightness=clamp(brightness,0,1);
    if(Number.isFinite(release))v.release=clamp(release,.02,3);
    if(Number.isFinite(damping))v.localDamping=clamp(damping,0,1);
  }
  stopAll(){
    for(const v of this.voices)this.done.push(v.id);
    this.voices.length=0;this.bodyReaction=0;
    for(const b of this.body){b.lr=b.li=b.rr=b.ri=0}
  }
  find(id){return this.voices.find(v=>v.id===id)||null}
  render(L,R,count=L.length){
    const sr=this.sr;
    for(let frame=0;frame<count;frame++){
      let sumL=0,sumR=0;
      const reaction=this.bodyReaction;
      for(let vi=this.voices.length-1;vi>=0;vi--){
        const v=this.voices[vi],cfg=v.cfg;
        const t=v.age++;
        let hammer=0;
        if(t<v.contact){
          const x=(t+.5)/v.contact;
          const pulse=Math.sin(PI*x);
          // Finite positive hammer force approximates progressive felt contact.
          hammer=Math.pow(Math.max(0,pulse),1.6+.65*v.hardness)*
            (.023*v.speed**1.75/v.contact*100);
        }
        const released=v.released&&v.damped;
        const damperRate=released
          ? Math.exp(-1/(sr*(v.fast?.020:Math.max(.04,v.release*(.38+.72*(1-this.damping))))))
          :1;
        const bodyCoupling=clamp(this.resonance*.000008,0,.000008);
        const harmonics=cfg.partials;
        let currentL=0,currentR=0,abs=0;
        for(let i=0;i<cfg.count;i++){
          const n=i%harmonics+1;
          const filteredHammer=Math.exp(-.015*n*n*(1-v.hardness))*
            (.52+.75*(.5*v.brightness+.5*this.brightness));
          const forcing=hammer*cfg.strike[i]*filteredHammer+
            reaction*cfg.strike[i]*bodyCoupling;
          const real=v.real[i],imag=v.imag[i];
          const attenuation=cfg.decay[i]*damperRate*
            (1-(v.localDamping??this.damping)*.000002*(n-1));
          const nextR=attenuation*(real*cfg.cos[i]-imag*cfg.sin[i])+forcing;
          const nextI=attenuation*(real*cfg.sin[i]+imag*cfg.cos[i]);
          v.real[i]=nextR;v.imag[i]=nextI;
          const radiated=nextI*cfg.weights[i];
          currentL+=radiated*cfg.left[i];
          currentR+=radiated*cfg.right[i];
          abs+=Math.abs(nextR)+Math.abs(nextI);
        }
        sumL+=currentL;sumR+=currentR;
        // Release preserves energy until the physical damper dissipates it.
        v.energy=abs/cfg.count;
        if(t>sr*.28&&v.released&&v.energy<1e-7){
          this.done.push(v.id);this.voices.splice(vi,1);
        }else if(t>sr*32){
          this.done.push(v.id);this.voices.splice(vi,1);
        }
      }
      const bodyInL=sumL*.021,bodyInR=sumR*.021;
      let boardL=0,boardR=0;
      for(const b of this.body){
        const lr=b.r*(b.lr*b.c-b.li*b.s)+bodyInL*b.weight,
          li=b.r*(b.lr*b.s+b.li*b.c);
        const rr=b.r*(b.rr*b.c-b.ri*b.s)+bodyInR*b.weight,
          ri=b.r*(b.rr*b.s+b.ri*b.c);
        b.lr=lr;b.li=li;b.rr=rr;b.ri=ri;
        boardL+=li*b.weight;boardR+=ri*b.weight;
      }
      this.bodyReaction=(boardL+boardR)*.5;
      const dryGain=.19*(.6+.4*this.lid);
      const boardGain=.13*this.resonance*(this.pedal?1.18:1);
      // Soft output protection; physical dynamics upstream are preserved.
      L[frame]=Math.tanh(dryGain*sumL+boardGain*boardL);
      R[frame]=Math.tanh(dryGain*sumR+boardGain*boardR);
    }
  }
}
if(typeof registerProcessor==='function'&&typeof AudioWorkletProcessor!=='undefined'){
  class C3XV8Worklet extends AudioWorkletProcessor{
    constructor(){
      super();this.engine=new C3XV8Engine(sampleRate,'eco');
      this.port.onmessage=({data})=>{
        if(!data)return;
        switch(data.type){
          case 'on':this.engine.noteOn(data);break;
          case 'off':this.engine.noteOff(data.id,data.fast,data.release);break;
          case 'param':this.engine.updateVoice(data.id,data);break;
          case 'pedal':this.engine.setSustain(data.value);break;
          case 'quality':this.engine.setQuality(data.quality);break;
          case 'controls':this.engine.setControls(data);break;
          case 'panic':this.engine.stopAll();break;
        }
      };
    }
    process(_inputs,outputs){
      const out=outputs[0]||[],L=out[0],R=out[1]||out[0];
      if(L&&R)this.engine.render(L,R,L.length);
      if(this.engine.done.length)this.port.postMessage({
        type:'done',ids:this.engine.done.splice(0)
      });
      return true;
    }
  }
  registerProcessor('stage-c3x-v8-web',C3XV8Worklet);
}
