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
    for name in ('polyphony_policy.mjs','polyphony_preview.mjs'):shutil.copy2(Path(__file__).with_name(name),out/name)
    def patch(name,fn):
        f=out/name;f.write_text(fn(f.read_text()))
    patch('index.html',lambda s:replace(s,'<option value="full">Completo · computador</option></select></label>','<option value="full">Completo · computador</option></select></label><label class="profile-selector">Polifonia experimental <select id="polyphony-limit" aria-label="Polifonia máxima"><option value="auto">Automática</option><option value="32">32</option><option value="64">64</option><option value="88">88</option><option value="96">96</option><option value="128">128</option><option value="192">192</option><option value="256">256 (teste, limitada)</option></select></label>').replace('Stage Synth · Palco MIDI v1.12.10','Stage Synth · PROTÓTIPO DE POLIFONIA').replace('v1.12.10</span>','G3.12m · experimental</span>'))
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
        s=replace(s,"import {profilePolyphony} from './audio-profile.js';","import {profilePolyphony} from './audio-profile.js';\nimport {candidateModalCapacity,candidateVoiceLimit} from './polyphony_preview.mjs';")
        s=replace(s,"this.voiceLimit=profilePolyphony(options.profile);","this.voiceLimit=profilePolyphony(options.profile);this.polyphony=options.polyphony??'auto';this.modalCapacity=candidateModalCapacity(this.polyphony,options.profile,ctx.sampleRate);")
        s=replace(s,"piano:new Acoustic(ctx,this.buses.piano,bank,{lite:this.lite}),","piano:new Acoustic(ctx,this.buses.piano,bank,{lite:this.lite,modalCapacity:this.modalCapacity}),")
        s=replace(s,"    return this.voiceLimit;","    return candidateVoiceLimit(this.polyphony,this.voiceLimit,this.modalCapacity,_mask===engines.piano.bit&&this.state.patches.piano.values.soundEngine==='modal'&&Boolean(this.instruments.piano.modal)&&[...this.voices.values()].every(v=>v.parts.size===1&&v.parts.has('piano')));")
        s=replace(s,"    if(playing.length>=this.activeVoiceLimit(mask)){\n      const steal=playing.find(v=>!v.held) || playing[0];\n      this.stopVoice(steal,true);this.voices.delete(steal.id);\n    }","    const limit=this.activeVoiceLimit(mask);\n    while(playing.length>=limit){\n      const steal=playing.find(v=>!v.held) || playing[0];\n      this.stopVoice(steal,true);this.voices.delete(steal.id);playing.splice(playing.indexOf(steal),1);\n    }")
        return s
    patch('stage.js',stage)
    def acoustic(s):
        s=replace(s,"this.ctx=ctx;this.bus=bus;this.lite=Boolean(options.lite);","this.ctx=ctx;this.bus=bus;this.lite=Boolean(options.lite);this.modalCapacity=options.modalCapacity??32;")
        s=replace(s,"await this.ctx.audioWorklet.addModule('./piano-worklet.js?build=1.12.9');","await this.ctx.audioWorklet.addModule('./piano-worklet.js?build=G3-polyphony-preview');")
        s=replace(s,"const node=new AudioWorkletNode(this.ctx,'palco-piano',{\n          numberOfInputs:0,numberOfOutputs:2,outputChannelCount:[2,1]","const node=new AudioWorkletNode(this.ctx,'palco-piano',{\n          processorOptions:{voices:this.modalCapacity},numberOfInputs:0,numberOfOutputs:2,outputChannelCount:[2,1]")
        return s
    patch('acoustic.js',acoustic)
    def worklet(s):
        s=replace(s,"constructor(sampleRate) {","constructor(sampleRate,capacity=MAX_VOICES) {\n    if(![32,64,88,96,128,192].includes(capacity))capacity=MAX_VOICES;")
        s=replace(s,"length: MAX_VOICES","length: capacity")
        s=replace(s,"constructor() {\n      super();\n      this.engine = new PianoEngine(sampleRate);","constructor(options) {\n      super();\n      this.engine = new PianoEngine(sampleRate,options?.processorOptions?.voices);")
        s=replace(s,"else if (m.type === 'stop') this.engine.stopAll();","else if (m.type === 'stop') this.engine.stopAll();\n        else if(m.type==='polyphony-probe')this.port.postMessage({type:'polyphony-probe',capacity:this.engine.voices.length,active:this.engine.voices.filter(v=>v.active).length,ids:this.engine.voices.filter(v=>v.active).map(v=>v.id)});")
        return s
    patch('piano-worklet.js',worklet)
    # Preview must run on an isolated localhost origin; no deployment.
    (out/'PREVIEW.txt').write_text('Protótipo G3.12m, não certificado. Execute python -m http.server 8765 nesta pasta e abra http://localhost:8765. Use origem separada do aplicativo estável. Motor A sozinho; 256 limitado. Sem integração do novo G3 físico.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);build(p.parse_args().out)
