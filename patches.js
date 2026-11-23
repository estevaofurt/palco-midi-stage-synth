const knob=(id,label,initial,min=0,max=100,unit='%',extra={})=>({type:'knob',id,label,initial,min,max,step:1,unit,...extra});
const select=(id,label,initial,options)=>({type:'select',id,label,initial,options});
const group=(label,...controls)=>({label,controls});
const preset=(id,name,values={})=>({id,name,values});
export const feet=['16′','5⅓′','8′','4′','2⅔′','2′','1⅗′','1⅓′','1′'];
const waves={sine:'Senoidal',triangle:'Triangular',sawtooth:'Dente de serra',square:'Quadrada',pulse:'Pulso ajustável'};
const models={mark1:'Rhodes Tine · Mark I',mark2:'Rhodes Tine · Mark II',wurly200:'Wurly Reed · 200A',wurly140:'Wurly Reed · 140B',cp70:'CP70',clav:'Clavinet',fmfull:'E. Piano 1 · Full Tines',fmdino:'E. Piano 2 · Dino EP',fmballad:'E. Piano 3 · Ballad Keys'};
export const engines={
  piano:{name:'Piano acústico',short:'Acústico',bit:1,level:85,
    presets:[
      preset('japanese','Japanese Grand',{character:'japanese',lid:87,brightness:63,hammer:57,resonance:57}),
      preset('american','American Grand',{character:'american',lid:75,brightness:50,hammer:44,resonance:66,release:.58}),
      preset('felt','Felt Piano',{character:'felt',hammer:18,brightness:23,lid:28,resonance:38,room:17,hammerNoise:7,release:.85}),
      preset('upright','Piano Upright',{character:'upright',hammer:52,brightness:45,lid:45,resonance:31,room:10,release:.32})
    ],
    groups:[
      group('Identidade e dinâmica',select('soundEngine','Motor do piano','physical',{modal:'A · Claude (modal)',physicalLegacy:'B · Stage físico anterior (v1.9.5)',physical:'C · Novo Stage mecânico',hybrid:'D · Stage híbrido · experimental',sampled:'E · Piano sampleado · WAV local',classic:'Clássico · compatibilidade'}),select('physicalQuality','Detalhe físico','eco',{eco:'Econômico · 32 notas',balanced:'Equilibrado · 48 notas',studio:'Estúdio · 64 notas'}),select('character','Instrumento','japanese',{japanese:'Japanese Grand',american:'American Grand',felt:'Felt Piano',upright:'Piano Upright'}),knob('touch','Dinâmica',50),knob('hammer','Dureza de martelo',50),knob('release','Release',.42,.06,3,' s',{step:.01,log:true})),
      group('Mecânica e ressonância',knob('hammerNoise','Hammer noise',26),knob('pedalNoise','Pedal noise',24),select('stringRes','String resonance','on',{on:'Ativada',off:'Desativada'}),select('mechanicalModel','Acoplamento mecânico','on',{on:'Ponte, tampo e cordas simpáticas',off:'Som anterior · comparar'}),knob('resonance','Intensidade',45)),
      group('Corpo do piano',knob('lid','Tampa',75),knob('brightness','Brilho',51),knob('room','Ambiente',15),knob('damping','Abafamento',37)),
      group('Banco de amostras · motor E',{type:'samplepack',id:'sampledPianoFiles',label:'Notas WAV do banco local'})
    ]
  },
  electric:{name:'Pianos elétricos',short:'Elétricos',bit:8,level:82,
    presets:[
      preset('mark1','Rhodes · Mark I',{model:'mark1',hammer:42,decay:65,preamp:27}),
      preset('mark2','Rhodes · Mark II',{model:'mark2',hammer:54,pickup:57,decay:58}),
      preset('wurly200','Wurly · 200A',{model:'wurly200',hammer:66,pickup:61,preamp:36,cabinet:'combo'}),
      preset('wurly140','Wurly · 140B',{model:'wurly140',hammer:58,preamp:49,cabinet:'small'}),
      preset('cp70','CP70',{model:'cp70',hammer:69,decay:42,preamp:18}),
      preset('clav','Clav',{model:'clav',hammer:75,decay:32,damper:18}),
      preset('fmfull','E. Piano 1 · Full Tines',{model:'fmfull',hammer:53,preamp:13,decay:59}),
      preset('fmdino','E. Piano 2 · Dino EP',{model:'fmdino',hammer:60,pickup:69,preamp:23}),
      preset('fmballad','E. Piano 3 · Ballad Keys',{model:'fmballad',hammer:32,decay:76,damper:60})
    ],
    groups:[
      group('Instrumento e toque',select('model','Instrumento','mark1',models),knob('hammer','Dureza',50),knob('pickup','Captação',45),knob('decay','Decaimento',58),knob('damper','Release',35)),
      group('Amplificador e microfonação',select('cabinet','Amplificador','line',{line:'Direto',combo:'Combo',small:'Vintage pequeno'}),select('mic','Microfone','close',{close:'Próximo',room:'Ambiente',di:'DI direta'}),knob('preamp','Preamp',19),knob('autoPan','Auto-Pan',0),knob('autoPanRate','Velocidade Auto-Pan',2.5,.1,8,' Hz',{step:.1}),knob('tremolo','Tremolo',0),knob('speed','Velocidade Tremolo',4.4,1,9,' Hz',{step:.1})),
      group('Ruídos mecânicos',knob('pedalNoise','Pedal noise',18),knob('hammerNoise','Hammer noise',20))
    ]
  },
  organ:{name:'Órgão',short:'Órgão',bit:2,level:72,
    presets:[
      preset('jazz','B3 · Jazz',{registration:'jazz',rotor:'slow',bars:[8,8,8,0,0,0,0,0,0]}),
      preset('gospel','B3 · Gospel',{registration:'gospel',bars:[8,5,8,6,3,5,2,3,5],percussion:'off',click:32,drive:37,rotor:'fast',width:78}),
      preset('church','Church · Tubos',{registration:'church',bars:[8,6,8,5,3,4,2,1,1],percussion:'off',rotor:'off',click:0,drive:0,vibrato:7,width:44})
    ],
    groups:[
      group('Instrumento',select('registration','Tipo de órgão','jazz',{jazz:'B3 · Jazz',gospel:'B3 · Gospel',church:'Church · Tubos'}),{type:'drawbars',id:'bars',label:'Registros',initial:[8,8,8,0,0,0,0,0,0]}),
      group('Leslie e articulação',select('rotor','Leslie','slow',{off:'Desligada',slow:'Lenta',fast:'Rápida'}),select('percussion','Percussão','third',{off:'Desligada',second:'2º harmônico',third:'3º harmônico'}),knob('vibrato','Vibrato',18),knob('click','Key click',32),knob('drive','Saturação',22),knob('width','Estéreo',66))
    ]
  },
  synth:{name:'Synth',short:'Synth',bit:4,level:43,
    presets:[
      preset('velvet','Pad de veludo'),
      preset('lead','Lead analógico',{waveA:'sawtooth',waveB:'square',blend:32,detune:6,attack:.012,decay:.36,sustain:70,release:.20,cutoff:1850,resonance:3.3,filterEnv:2.4,spread:22}),
      preset('bass','Baixo redondo',{waveA:'triangle',waveB:'sawtooth',blend:30,detune:2,attack:.005,decay:.23,sustain:49,release:.11,cutoff:480,resonance:2.1,filterEnv:2.7,spread:3,voiceMode:'mono'}),
      preset('pulse','Pulse Lead',{waveA:'pulse',waveB:'pulse',pulseWidth:35,attack:.01,release:.16,cutoff:2400})
    ],
    groups:[
      group('Osciladores / Mixer',select('waveA','Onda A','sawtooth',waves),select('waveB','Onda B','triangle',waves),knob('oscA','OSC A',88),knob('oscB','OSC B',65),knob('noiseLevel','Ruído',0),select('noiseType','Ruído tipo','white',{white:'Branco',pink:'Rosa'}),knob('pulseWidth','Pulse width',50,5,95,'%'),select('sync','Sincronia','off',{off:'Desligada',on:'Hard sync · aproximado'}),knob('syncRatio','Sync ratio',2.3,1,4,' x',{step:.1}),select('unison','Uníssono','1',{'1':'1 voz','2':'2 vozes','3':'3 vozes'})),
      group('Pitch e panorama',knob('octave','Oitava',0,-2,2,' oit'),knob('semitones','Semitons',0,-12,12,' st'),knob('fine','Fine tune',0,-100,100,' ct'),knob('detune','Detune',10,0,35,' ct'),knob('blend','Mistura A/B',45),knob('spread','Estéreo',62),knob('volume','Volume VCA',85),knob('pan','Pan',0,-100,100,' %')),
      group('VCF',select('filterType','Tipo','lowpass',{lowpass:'Low-pass',highpass:'High-pass',bandpass:'Band-pass',notch:'Notch'}),knob('cutoff','Cutoff',1450,90,14000,' Hz',{log:true}),knob('resonance','Resonance',1,.5,8,' Q',{step:.1}),knob('filterEnv','Env depth',1.15,-4,4,' oit',{step:.05})),
      group('Envelope ADSR',knob('attack','Attack',.30,.003,4,' s',{step:.001,log:true}),knob('decay','Decay',.78,.025,4,' s',{step:.005,log:true}),knob('sustain','Sustain',70),knob('release','Release',1.15,.025,5,' s',{step:.005,log:true})),
      group('Modulação / LFO',select('lfoDest','Destino LFO','pitch',{pitch:'Pitch',cutoff:'Cutoff',amp:'Amplitude'}),knob('lfoRate','Rate',5,.1,18,' Hz',{step:.1}),knob('lfoDepth','Depth',0),select('matrixSource','Matriz · origem','velocity',{velocity:'Velocity',aftertouch:'Aftertouch'}),select('matrixDest','Matriz · destino','cutoff',{cutoff:'Cutoff',pitch:'Pitch',amp:'Amplitude'}),knob('matrixAmount','Matriz · intensidade',0,-100,100,' %')),
      group('VCA e vozes',select('voiceMode','Modo','poly',{poly:'Polifônico',mono:'Monofônico',legato:'Legato'}),knob('glide','Portamento',0,0,2,' s',{step:.01}))
    ]
  },
  sf:{name:'Leitor SF',short:'Leitor SF',bit:16,level:75,
    presets:[
      preset('strings','Cordas',{native:'strings'}),preset('bells','Bells',{native:'bells'}),
      preset('winds','Sopros',{native:'winds'}),preset('brass','Metais',{native:'brass'}),
      preset('choir','Coral',{native:'choir'})
    ],
    groups:[
      group('Banco de instrumentos',select('native','Timbre interno','strings',{strings:'Cordas',bells:'Bells',winds:'Sopros',brass:'Metais',choir:'Coral'}),{type:'soundfont',id:'soundfont',label:'Importar arquivo SF2'}),
      group('Expressão',knob('attack','Ataque',.12,.005,2,' s',{step:.005,log:true}),knob('release','Release',.48,.05,4,' s',{step:.01,log:true}),knob('brightness','Brilho',55),knob('pan','Pan',0,-100,100,' %'))
    ]
  }
};
// O menu Preset representa uma configuração de fábrica distinta do instrumento escolhido.
// IDs originais permanecem válidos para não perder configurações de versões anteriores.
export const instrumentField={piano:'character',electric:'model',organ:'registration',sf:'native'};
export const instrumentName=(engine,values)=>{
  const field=instrumentField[engine];if(!field)return '';
  for(const g of engines[engine].groups)for(const c of g.controls){
    if(c.id===field)return c.options?.[values[field]]||'';
  }
  return '';
};
for(const engine of ['piano','electric','organ','sf']){
  const def=engines[engine],base=[...def.presets];
  for(const entry of base){
    entry.name=entry.name+' · Natural';
    const soft={...entry.values},bright={...entry.values};
    if(engine==='piano'){
      soft.brightness=Math.max(15,(soft.brightness??51)-17);soft.hammer=Math.max(10,(soft.hammer??50)-15);soft.room=10;
      bright.brightness=Math.min(90,(bright.brightness??51)+18);bright.hammer=Math.min(90,(bright.hammer??50)+14);bright.room=18;
    }else if(engine==='electric'){
      soft.hammer=Math.max(10,(soft.hammer??50)-18);soft.pickup=Math.max(20,(soft.pickup??45)-12);soft.preamp=10;soft.tremolo=8;
      bright.hammer=Math.min(92,(bright.hammer??50)+17);bright.pickup=Math.min(87,(bright.pickup??45)+14);bright.preamp=34;bright.tremolo=23;
    }else if(engine==='organ'){
      soft.drive=5;soft.vibrato=8;soft.click=7;
      bright.drive=39;bright.vibrato=26;bright.click=35;
    }else{
      soft.brightness=30;soft.attack=.22;bright.brightness=79;bright.attack=.035;
    }
    def.presets.push(preset(entry.id+'-soft',entry.name.replace(' · Natural',' · Suave'),soft));
    def.presets.push(preset(entry.id+'-bright',entry.name.replace(' · Natural',' · Brilhante'),bright));
  }
}
export const presetsForInstrument=(engine,values)=>{
  const field=instrumentField[engine],items=engines[engine].presets;
  return field?items.filter(p=>(p.values[field]??fromPreset(engine,p.id).values[field])===values[field]):items;
};
export function presetForInstrument(engine,choice){
  const field=instrumentField[engine];
  return engines[engine].presets.find(p=>p.values[field]===choice)||engines[engine].presets[0];
}

export const effectsDefinition=[
  {id:'reverb1',label:'Reverb 1',type:'reverb'}, {id:'reverb2',label:'Reverb 2',type:'reverb'},
  {id:'delay1',label:'Delay 1',type:'delay'},{id:'delay2',label:'Delay 2',type:'delay'},
  {id:'mod1',label:'Modulação 1',type:'mod'},{id:'mod2',label:'Modulação 2',type:'mod'},
  {id:'eq',label:'Equalizador',type:'eq'},{id:'comp',label:'Compressor',type:'comp'}
];
export const reverbTypes={hall:'Hall',room:'Room',plate:'Plate',spring:'Spring',church:'Church',shimmer:'Shimmer'};
export const delayTypes={tape:'Tape',analog:'Analog',digital:'Digital'};
export const modulationTypes={chorus:'Chorus',flanger:'Flanger',phaser:'Phaser',wah:'Wah-Wah'};
export const eqTypes={parametric:'Paramétrico',graphic:'Gráfico · 7 bandas'};
export const defaultSlot=id=>({
  active:false,targets:['piano'],mix:id==='eq'||id==='comp'?100:25,depth:50,
  time:id.startsWith('reverb')?1.7:.28,feedback:25,rate:2.1,
  reverbType:id==='reverb2'?'room':'hall',
  delayType:id==='delay2'?'tape':'digital',
  modType:id==='mod2'?'flanger':'chorus',eqType:'parametric',
  low:0,mid:0,high:0,lowFreq:160,midFreq:1000,highFreq:5600,lowQ:.8,midQ:1.2,highQ:.8,
  eq125:0,eq250:0,eq500:0,eq1000:0,eq2000:0,eq4000:0,eq8000:0,
  threshold:-18,ratio:3,attack:.01,release:.2,knee:6,makeup:0
});
export const scenes=[
  {id:'piano-pad',name:'Piano + pad',mask:5},{id:'piano',name:'Piano acústico',mask:1},
  {id:'electric',name:'Piano elétrico',mask:8},{id:'electric-pad',name:'Elétrico + pad',mask:12},
  {id:'organ',name:'Órgão',mask:2},{id:'synth',name:'Synth',mask:4},
  {id:'sf',name:'Leitor SF',mask:16},{id:'piano-strings',name:'Piano + cordas',mask:17},
  {id:'duo',name:'Duo · órgão no canal 2',mask:7,duo:true}
];
const safeClone=val=>Array.isArray(val)?val.slice():val;
export function fromPreset(engine,id){
  const def=engines[engine],item=def.presets.find(x=>x.id===id)||def.presets[0],values={};
  for(const {controls} of def.groups)for(const c of controls)if(c.type!=='soundfont'&&c.type!=='samplepack')values[c.id]=safeClone(item.values[c.id]??c.initial);
  return {preset:item.id,values,level:def.level};
}
export function normalise(c,value,fallback){
  if(c.type==='soundfont'||c.type==='samplepack')return fallback;
  if(c.type==='select')return Object.hasOwn(c.options,value)?value:fallback;
  if(c.type==='drawbars')return Array.isArray(value)&&value.length===9&&value.every(Number.isInteger)?value.map(x=>Math.max(0,Math.min(8,x))):safeClone(fallback);
  return Number.isFinite(value)?Math.max(c.min,Math.min(c.max,value)):fallback;
}
export function pretty(c,v){
  if(c.unit===' s'&&v<1)return Math.round(v*1000)+' ms';
  if(c.id==='cutoff'&&v>=1000)return (v/1000).toFixed(2).replace('.',',')+' kHz';
  const dec=c.step<1?(c.step<=.005?3:c.step<=.05?2:1):0;
  return v.toFixed(dec).replace('.',',')+c.unit;
}
const key='palco-stage-panel-v1';
export function loadState(storage){
  let saved={},legacy={};
  try{saved=JSON.parse(storage?.getItem(key))||{}}catch{}
  try{legacy=JSON.parse(storage?.getItem('palco-electric-v1'))||{}}catch{}
  const state={editor:Object.hasOwn(engines,saved.editor)||saved.editor==='effects'?saved.editor:'piano',mask:Number.isInteger(saved.mask)&&saved.mask>=0&&saved.mask<=31?saved.mask:1,duo:saved.duo===true,patches:{},edits:{},
    fx:{enabled:{},slots:{}},performance:{bpm:120,arp:false,rate:'1/8',chord:'off',loopBars:'2'}};
  for(const [id,def] of Object.entries(engines)){
    const stored=saved.patches?.[id];
    const migratePreset=original=>id==='electric'&&typeof original==='string'
      ?original.replace(/^cp80(?=-|$)/,'cp70'):original;
    const p=fromPreset(id,migratePreset(stored?.preset));
    let values=stored?.values||{};
    if(id==='electric'&&values.model==='cp80')values={...values,model:'cp70'};
    if(id==='electric'&&!stored){values={...legacy};if(values.model==='cp80')values.model='cp70'}
    // Migração v1.6: os dois B3 usavam 'type=b3', que não identifica Jazz/Gospel.
    // Reconstrói o modelo pelo preset gravado; Church selecionado à parte tem precedência.
    if(id==='organ'&&!Object.hasOwn(values,'registration')){
      const prior=stored?.preset||'';
      values={...values,registration:values.type==='church'?'church':prior.startsWith('gospel')?'gospel':prior.startsWith('church')?'church':'jazz'};
    }
    for(const {controls} of def.groups)for(const c of controls)if(c.type!=='soundfont'&&c.type!=='samplepack')p.values[c.id]=normalise(c,values[c.id],p.values[c.id]);
    if(Number.isFinite(stored?.level))p.level=Math.max(0,Math.min(100,stored.level));
    if(instrumentField[id]&&p.values[instrumentField[id]]!==fromPreset(id,p.preset).values[instrumentField[id]]){
      const chosen=presetForInstrument(id,p.values[instrumentField[id]]);
      p.preset=chosen.id;
    }
    state.patches[id]=p;state.edits[id]={};
    for(const item of def.presets){
      // Keep old CP80 edited presets (Natural/Suave/Brilhante) under CP70.
      const legacyPreset=id==='electric'?item.id.replace(/^cp70(?=-|$)/,'cp80'):item.id;
      const prev=saved.edits?.[id]?.[item.id]??saved.edits?.[id]?.[legacyPreset];if(!prev)continue;
      const copy=fromPreset(id,item.id);
      const savedPresetValues=id==='electric'&&prev.model==='cp80'?{...prev,model:'cp70'}:prev;
      for(const {controls} of def.groups)for(const c of controls)if(c.type!=='soundfont'&&c.type!=='samplepack')copy.values[c.id]=normalise(c,savedPresetValues[c.id],copy.values[c.id]);
      state.edits[id][item.id]=copy.values;
    }
    rememberPatch(state,id);
    state.fx.enabled[id]=saved.fx?.enabled?.[id]===true;
  }
  for(const {id} of effectsDefinition){
    const defaults=defaultSlot(id), old=saved.fx?.slots?.[id]||{};
    const numeric=Object.fromEntries(Object.entries(old).filter(([k,v])=>
      Object.hasOwn(defaults,k)&&k!=='targets' && typeof v===typeof defaults[k]));
    // Migração: v1.4 salvava somente 'target'. A lista nova aceita vários motores.
    const source=Array.isArray(old.targets)?old.targets:(typeof old.target==='string'?[old.target]:defaults.targets);
    const targets=[...new Set(source.filter(x=>Object.hasOwn(engines,x)))];
    state.fx.slots[id]={...defaults,...numeric,targets};
    // Valores desconhecidos não podem quebrar o rack ao restaurar sessões antigas.
    if(!Object.hasOwn(reverbTypes,state.fx.slots[id].reverbType))state.fx.slots[id].reverbType=defaults.reverbType;
    if(!Object.hasOwn(delayTypes,state.fx.slots[id].delayType))state.fx.slots[id].delayType=defaults.delayType;
    if(!Object.hasOwn(modulationTypes,state.fx.slots[id].modType))state.fx.slots[id].modType=defaults.modType;
    if(!Object.hasOwn(eqTypes,state.fx.slots[id].eqType))state.fx.slots[id].eqType=defaults.eqType;
  }
  const perf=saved.performance||{};
  if(Number.isFinite(perf.bpm))state.performance.bpm=Math.max(40,Math.min(240,Math.round(perf.bpm)));
  if(['1/4','1/8','1/16'].includes(perf.rate))state.performance.rate=perf.rate;
  if(['off','major','minor','sus2','sus4','fifth'].includes(perf.chord))state.performance.chord=perf.chord;
  if(['1','2','4'].includes(perf.loopBars))state.performance.loopBars=perf.loopBars;
  state.performance.arp=perf.arp===true;
  return state;
}
export function rememberPatch(state,id){
  const patch=state.patches[id],original=fromPreset(id,patch.preset);
  if(JSON.stringify(original.values)===JSON.stringify(patch.values))delete state.edits[id][patch.preset];
  else state.edits[id][patch.preset]=structuredClone(patch.values);
}
export function saveState(storage,state){try{storage?.setItem(key,JSON.stringify(state))}catch{}}
export function maskForChannel(state,channel){return state.mask&(state.duo?(channel===1?2:29):31)}
