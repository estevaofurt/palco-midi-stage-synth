const knob = (id, label, initial, min=0, max=100, unit='%', extra={}) =>
  ({type:'knob', id, label, initial, min, max, step:1, unit, ...extra});
const select = (id, label, initial, options) => ({type:'select', id, label, initial, options});
const group = (label, ...controls) => ({label, controls});
const preset = (id, name, values={}) => ({id, name, values});
const waveforms = {sawtooth:'Serra', square:'Pulso quadrado', triangle:'Triangular', sine:'Senoidal'};
export const feet = ['16′','5⅓′','8′','4′','2⅔′','2′','1⅗′','1⅓′','1′'];

export const engines = {
  piano: {
    name:'Piano acústico', short:'Acústico', bit:1, level:85,
    presets:[
      preset('concert','Cauda de concerto'),
      preset('intimate','Cauda intimista',{hammer:38,lid:31,brightness:38,resonance:53,room:18,damping:52}),
      preset('stage','Cauda de palco',{hammer:59,lid:91,brightness:65,resonance:25,room:8,touch:39})
    ],
    groups:[
      group('Martelo e toque',knob('hammer','Dureza',50),knob('touch','Curva de toque',50),knob('damping','Cauda ao soltar',37)),
      group('Corpo e espaço',knob('lid','Tampa',75),knob('brightness','Brilho',51),knob('resonance','Ressonância',45),knob('room','Ambiente',15))
    ]
  },
  electric: {
    name:'Piano elétrico',short:'Elétrico',bit:8,level:85,
    presets:[
      preset('studio','Tine de estúdio'),
      preset('suitcase','Tine com tremolo',{hammer:46,pickup:57,drive:35,cabinet:'combo',tremolo:48,speed:4.1}),
      preset('reed','Reed de palco',{model:'reed',hammer:65,pickup:63,drive:51,cabinet:'small',decay:44,damper:26})
    ],
    groups:[
      group('Mecânica',select('model','Elemento','tine',{tine:'Tine · haste',reed:'Reed · palheta'}),knob('hammer','Martelo',50),knob('pickup','Captação',45),knob('decay','Vibração',58),knob('damper','Abafador · cauda',35)),
      group('Amplificador',select('cabinet','Saída','line',{line:'Linha direta',combo:'Combo aberto',small:'Falante compacto'}),knob('drive','Saturação',19),knob('tremolo','Tremolo',0),knob('speed','Velocidade',4.4,1,9,' Hz',{step:.1}))
    ]
  },
  organ: {
    name:'Órgão',short:'Órgão',bit:2,level:72,
    presets:[
      preset('jazz','Jazz 888'),
      preset('gospel','Gospel aberto',{bars:[8,5,8,6,3,5,2,3,5],percussion:'off',click:26,drive:37,rotor:'fast',width:78}),
      preset('flute','Flauta suave',{bars:[0,0,8,4,0,2,0,0,0],percussion:'off',click:12,drive:10,rotor:'slow',width:43})
    ],
    groups:[
      group('Registros harmônicos',{type:'drawbars',id:'bars',label:'Drawbars',initial:[8,8,8,0,0,0,0,0,0]}),
      group('Contato e caixa rotativa',select('percussion','Percussão','third',{off:'Desligada',second:'2º harmônico',third:'3º harmônico'}),select('rotor','Rotação','slow',{stop:'Parada',slow:'Lenta',fast:'Rápida'}),knob('click','Clique de tecla',32),knob('drive','Saturação',22),knob('width','Abertura estéreo',66))
    ]
  },
  synth: {
    name:'Synth',short:'Synth',bit:4,level:43,
    presets:[
      preset('velvet','Pad de veludo'),
      preset('lead','Lead analógico',{waveA:'sawtooth',waveB:'square',blend:32,detune:6,attack:.012,decay:.36,sustain:70,release:.20,cutoff:1850,resonance:3.3,filterEnv:2.4,spread:22}),
      preset('bass','Baixo redondo',{waveA:'triangle',waveB:'sawtooth',blend:30,detune:2,attack:.005,decay:.23,sustain:49,release:.11,cutoff:480,resonance:2.1,filterEnv:2.7,spread:3})
    ],
    groups:[
      group('Osciladores',select('waveA','Onda A','sawtooth',waveforms),select('waveB','Onda B','triangle',waveforms),knob('blend','Mistura A/B',45),knob('detune','Desafinação',10,0,35,' ct'),knob('spread','Estéreo',62)),
      group('Filtro passa-baixas',knob('cutoff','Corte',1450,90,14000,' Hz',{log:true}),knob('resonance','Ressonância',1.0,.5,8,' Q',{step:.1}),knob('filterEnv','Envelope',1.15,0,4,' oit.',{step:.05})),
      group('Envelope de amplitude',knob('attack','Ataque',.30,.003,4,' s',{step:.001,log:true}),knob('decay','Decaimento',.78,.025,4,' s',{step:.005,log:true}),knob('sustain','Sustentação',70),knob('release','Soltura',1.15,.025,5,' s',{step:.005,log:true}))
    ]
  }
};

export const scenes = [
  {id:'piano-pad',name:'Piano + pad',mask:5},
  {id:'piano',name:'Piano acústico',mask:1},
  {id:'electric',name:'Piano elétrico',mask:8},
  {id:'electric-pad',name:'Elétrico + pad',mask:12},
  {id:'organ',name:'Órgão',mask:2},
  {id:'synth',name:'Synth',mask:4},
  {id:'duo',name:'Duo · órgão no canal 2',mask:7,duo:true}
];
export function fromPreset(engine, id) {
  const definition=engines[engine];
  const patch=definition.presets.find(item=>item.id===id) || definition.presets[0];
  const values={};
  for(const {controls} of definition.groups) for(const control of controls){
    const value=patch.values[control.id] ?? control.initial;
    values[control.id]=Array.isArray(value)?[...value]:value;
  }
  return {preset:patch.id,values,level:definition.level};
}
export function normalise(control,value,fallback){
  if(control.type==='select') return Object.hasOwn(control.options,value)?value:fallback;
  if(control.type==='drawbars'){
    return Array.isArray(value)&&value.length===9&&value.every(Number.isInteger)
      ? value.map(v=>Math.max(0,Math.min(8,v))) : [...fallback];
  }
  return Number.isFinite(value)?Math.max(control.min,Math.min(control.max,value)):fallback;
}
export function pretty(control,value){
  if(control.unit===' s' && value<1)return Math.round(value*1000)+' ms';
  if(control.id==='cutoff' && value>=1000)return (value/1000).toFixed(2).replace('.',',')+' kHz';
  const digits=(control.step<1)?(control.unit===' s'||control.step===.05?2:1):0;
  return value.toFixed(digits).replace('.',',')+control.unit;
}

const storageKey='palco-stage-panel-v1';
export function loadState(storage) {
  let saved={}, legacy={};
  try{saved=JSON.parse(storage.getItem(storageKey))||{}}catch{}
  try{legacy=JSON.parse(storage.getItem('palco-electric-v1'))||{}}catch{}
  const state={editor:Object.hasOwn(engines,saved.editor)?saved.editor:'piano',
    mask:Number.isInteger(saved.mask)&&saved.mask>=0&&saved.mask<=15?saved.mask:5,
    duo:saved.duo===true, patches:{}, edits:{}};
  for(const [key,definition] of Object.entries(engines)){
    const stored=saved.patches?.[key];
    const patch=fromPreset(key,stored?.preset);
    let values=stored?.values||{};
    if(key==='electric'&&!stored){
      values={...legacy};
      if(Number.isFinite(values.speed))values.speed=Math.round((1+values.speed*.08)*10)/10;
    }
    for(const {controls} of definition.groups)for(const control of controls){
      patch.values[control.id]=normalise(control,values[control.id],patch.values[control.id]);
    }
    if(Number.isFinite(stored?.level))patch.level=Math.min(100,Math.max(0,stored.level));
    state.patches[key]=patch;
    state.edits[key]={};
    for(const entry of definition.presets){
      const previous=saved.edits?.[key]?.[entry.id];if(!previous)continue;
      const copy=fromPreset(key,entry.id);
      for(const {controls} of definition.groups)for(const control of controls){
        copy.values[control.id]=normalise(control,previous[control.id],copy.values[control.id]);
      }
      state.edits[key][entry.id]=copy.values;
    }
    rememberPatch(state,key);
  }
  return state;
}
export function rememberPatch(state,key){
  const patch=state.patches[key], original=fromPreset(key,patch.preset);
  if(JSON.stringify(original.values)===JSON.stringify(patch.values))delete state.edits[key][patch.preset];
  else state.edits[key][patch.preset]=structuredClone(patch.values);
}
export function saveState(storage,state){try{storage.setItem(storageKey,JSON.stringify(state))}catch{}}
export function maskForChannel(state,channel){
  return state.mask & (state.duo ? (channel===1?2:13) : 15);
}
