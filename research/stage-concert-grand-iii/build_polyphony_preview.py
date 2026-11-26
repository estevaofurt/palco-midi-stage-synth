"""Build a self-contained experimental app overlay; never edit root sources."""
import argparse,shutil,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def replace(s,old,new):
    if s.count(old)!=1:raise ValueError(f'overlay anchor count {s.count(old)}: {old[:80]}')
    return s.replace(old,new,1)
def build(out):
    out=out.resolve()
    if out==ROOT or ROOT in out.parents:raise ValueError('output must be outside repository')
    out.mkdir(parents=True,exist_ok=False)
    for f in ROOT.iterdir():
        if f.is_file() and f.suffix in ('.js','.mjs','.html','.css','.txt'):shutil.copy2(f,out/f.name)
    shutil.copy2(ROOT/'package.json',out/'package.json')
    for name in ('polyphony_policy.mjs','polyphony_preview.mjs','device_polyphony_logic.mjs','device_polyphony_worker.mjs','device_polyphony_ui.mjs','device_polyphony.html'):shutil.copy2(Path(__file__).with_name(name),out/name)
    def patch(name,fn):
        f=out/name;f.write_text(fn(f.read_text()))
    patch('index.html',lambda s:replace(s,'<option value="full">Completo · computador</option></select></label>','<option value="full">Completo · computador</option></select></label><label class="profile-selector">Polifonia experimental <select id="polyphony-limit" aria-label="Polifonia máxima"><option value="auto">Automática</option><option value="32">32</option><option value="64">64</option><option value="88">88</option><option value="96">96</option><option value="128">128</option><option value="192">192</option><option value="256">256 (teste, limitada)</option></select></label>').replace('Stage Synth · Palco MIDI v1.12.10','Stage Synth · PROTÓTIPO DE POLIFONIA').replace('v1.12.10</span>','G3.12m · experimental</span>'))
    patch('index.html',lambda s:replace(s,'<p id="profile-note" class="profile-note" role="status"></p>','<p id="profile-note" class="profile-note" role="status"></p><p class="profile-note"><a href="./device_polyphony.html">Avaliar capacidade de polifonia do dispositivo</a></p>'))
    def app(s):
        s=replace(s,"import {getProfile,PROFILE_STORAGE_KEY} from './audio-profile.js';","import {getProfile,PROFILE_STORAGE_KEY} from './audio-profile.js';\nimport {parsePolyphony,STORAGE_KEY} from './polyphony_policy.mjs';")
        s=replace(s,'const mobileLite=profile===\'lite\';',"""const mobileLite=profile==='lite';
let polyphony='auto';try{polyphony=parsePolyphony(storage?.getItem(STORAGE_KEY))}catch{}
const polySelect=byId('polyphony-limit');polySelect.value=String(polyphony);
polySelect.onchange=()=>{try{storage?.setItem(STORAGE_KEY,polySelect.value)}catch{}window.location.reload();};""")
        s=replace(s,"(mobileLite?'Leve · 32 notas':'Completo · 64 notas')+' · Piano: '+label+'. Os FX são opcionais.'","(mobileLite?'Leve':'Completo')+' · polifonia solicitada: '+polyphony+' · Piano: '+label+'. Experimental; limite efetivo no contador. Camadas mantêm o limite anterior.'")
        s=replace(s,"pedal:paintPedal},{profile});","pedal:paintPedal},{profile,polyphony});")
        return s
    patch('app.js',app)
    def stage(s):
        s=replace(s,"import {profilePolyphony} from './audio-profile.js';","import {profilePolyphony} from './audio-profile.js';\nimport {candidateModalCapacity,candidateVoiceLimit,physicalOverride,physicalLimit} from './polyphony_preview.mjs';")
        s=replace(s,"this.voiceLimit=profilePolyphony(options.profile);","this.voiceLimit=profilePolyphony(options.profile);this.polyphony=options.polyphony??'auto';this.modalCapacity=candidateModalCapacity(this.polyphony,options.profile,ctx.sampleRate);this.physicalOverride=physicalOverride(this.polyphony,options.profile,ctx.sampleRate);")
        s=replace(s,"piano:new Acoustic(ctx,this.buses.piano,bank,{lite:this.lite}),","piano:new Acoustic(ctx,this.buses.piano,bank,{lite:this.lite,modalCapacity:this.modalCapacity,physicalOverride:this.physicalOverride}),")
        s=replace(s,"    return this.voiceLimit;","""    const piano=this.state.patches.piano.values,inst=this.instruments.piano;
    const node={modal:inst.modal,physical:inst.physical,physicalLegacy:inst.legacyPhysical,hybrid:inst.hybrid}[piano.soundEngine];
    const solo=_mask===engines.piano.bit&&Boolean(node)&&[...this.voices.values()].every(v=>v.parts.size===1&&v.parts.has('piano'));
    const physical=['physical','physicalLegacy','hybrid'].includes(piano.soundEngine);
    const cap=physical?physicalLimit(this.physicalOverride,piano.physicalQuality):this.modalCapacity;
    return candidateVoiceLimit(this.polyphony,this.voiceLimit,cap,solo);""")
        s=replace(s,"    if(playing.length>=this.activeVoiceLimit(mask)){\n      const steal=playing.find(v=>!v.held) || playing[0];\n      this.stopVoice(steal,true);this.voices.delete(steal.id);\n    }","    const limit=this.activeVoiceLimit(mask);\n    while(playing.length>=limit){\n      const steal=playing.find(v=>!v.held) || playing[0];\n      this.stopVoice(steal,true);this.voices.delete(steal.id);playing.splice(playing.indexOf(steal),1);\n    }")
        return s
    patch('stage.js',stage)
    def acoustic(s):
        s=replace(s,"this.ctx=ctx;this.bus=bus;this.lite=Boolean(options.lite);","this.ctx=ctx;this.bus=bus;this.lite=Boolean(options.lite);this.modalCapacity=options.modalCapacity??32;this.physicalOverride=options.physicalOverride??null;")
        s=replace(s,"await this.ctx.audioWorklet.addModule('./piano-worklet.js?build=1.12.9');","await this.ctx.audioWorklet.addModule('./piano-worklet.js?build=G3-polyphony-preview');")
        s=replace(s,"const node=new AudioWorkletNode(this.ctx,'palco-piano',{\n          numberOfInputs:0,numberOfOutputs:2,outputChannelCount:[2,1]","const node=new AudioWorkletNode(this.ctx,'palco-piano',{\n          processorOptions:{voices:this.modalCapacity},numberOfInputs:0,numberOfOutputs:2,outputChannelCount:[2,1]")
        for processor in ('palco-physical-piano','palco-physical-piano-legacy','palco-piano-hybrid'):
            anchor=f"const node=new AudioWorkletNode(this.ctx,'{processor}',{{"
            s=replace(s,anchor,anchor+"\n          processorOptions:{voices:this.physicalOverride},")
        return s
    patch('acoustic.js',acoustic)
    def worklet(s):
        s=replace(s,"constructor(sampleRate) {","constructor(sampleRate,capacity=MAX_VOICES) {\n    if(![32,64,88,96,128,192].includes(capacity))capacity=MAX_VOICES;")
        s=replace(s,"length: MAX_VOICES","length: capacity")
        s=replace(s,"constructor() {\n      super();\n      this.engine = new PianoEngine(sampleRate);","constructor(options) {\n      super();\n      this.engine = new PianoEngine(sampleRate,options?.processorOptions?.voices);")
        s=replace(s,"else if (m.type === 'stop') this.engine.stopAll();","else if (m.type === 'stop') this.engine.stopAll();\n        else if(m.type==='polyphony-probe')this.port.postMessage({type:'polyphony-probe',capacity:this.engine.voices.length,active:this.engine.voices.filter(v=>v.active).length,ids:this.engine.voices.filter(v=>v.active).map(v=>v.id)});")
        return s
    patch('piano-worklet.js',worklet)
    def physical_worklet(s,hybrid):
        if hybrid:
            s=replace(s,"constructor(sampleRate=SRATE,quality='eco'){","constructor(sampleRate=SRATE,quality='eco',override=null){")
            s=replace(s,"this.voices=Array.from({length:MAX_VOICES},()=>new Voice());","this.override=[32,64,88,96,128].includes(override)?override:null;this.voices=Array.from({length:Math.max(MAX_VOICES,this.override??0)},()=>new Voice());")
            s=replace(s,"this.maxVoices=q.voices;","this.maxVoices=this.override===null?q.voices:(this.quality==='eco'?Math.min(32,this.override):this.override);")
            s=replace(s,"constructor(){\n      super();\n      this.engine=new HybridPianoEngine(sampleRate,'eco');","constructor(options){\n      super();\n      this.engine=new HybridPianoEngine(sampleRate,'eco',options?.processorOptions?.voices);")
        else:
            s=replace(s,"constructor(sr=48000,quality='eco'){","constructor(sr=48000,quality='eco',override=null){")
            s=replace(s,"this.sr=sr;this.voices=Array.from({length:PHYSICAL_PRESETS.studio.voices},()=>new StringVoice());","this.sr=sr;this.override=[32,64,88,96,128].includes(override)?override:null;this.voices=Array.from({length:Math.max(PHYSICAL_PRESETS.studio.voices,this.override??0)},()=>new StringVoice());")
            s=replace(s,"this.blockVoices=new Array(PHYSICAL_PRESETS.studio.voices);","this.blockVoices=new Array(this.voices.length);")
            s=replace(s,"this.maxVoices=m.voices;","this.maxVoices=this.override===null?m.voices:(this.mode==='eco'?Math.min(32,this.override):this.override);")
            s=replace(s,"constructor(){super();this.engine=new PhysicalPianoEngine(sampleRate,'eco');","constructor(options){super();this.engine=new PhysicalPianoEngine(sampleRate,'eco',options?.processorOptions?.voices);")
        s=replace(s,"else if(m.type==='stop')this.engine.stopAll();","else if(m.type==='stop')this.engine.stopAll();else if(m.type==='polyphony-probe')this.port.postMessage({type:'polyphony-probe',capacity:this.engine.maxVoices,active:this.engine.voices.filter(v=>v.active).length,ids:this.engine.voices.filter(v=>v.active).map(v=>v.id)});")
        return s
    for name in ('physical-piano.js','physical-piano-legacy.js','physical-piano-hybrid.js'):
        patch(name,lambda s:physical_worklet(s,'hybrid' in name))
    # Preview must run on an isolated localhost origin; no deployment.
    (out/'PREVIEW.txt').write_text('Protótipo G3.12m, não certificado. Execute python -m http.server 8765 nesta pasta e abra http://localhost:8765. Use origem separada do aplicativo estável. Motor A até 192; B/C/D até 128 em Balanced/Studio; 256 limitado. Sem integração do novo G3 físico.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);build(p.parse_args().out)
