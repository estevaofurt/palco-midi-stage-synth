import {engines,feet,fromPreset,pretty,rememberPatch,effectsDefinition,instrumentField,presetsForInstrument,presetForInstrument,instrumentName,defaultSlot} from './patches.js';
const elem=(tag,cls,text)=>{
  const node=document.createElement(tag);if(cls)node.className=cls;if(text!==undefined)node.textContent=text;return node;
};
export function addOption(select,value,text){
  const opt=elem('option','',text);opt.value=value;select.append(opt);return opt;
}
function selectField(label,options,control){
  const field=elem('label',control?'choice':'tone-field'),name=elem('span',control?'':'tone-label',label);
  const wrap=elem('span','sel-wrap'),select=elem('select');select.setAttribute('aria-label',label);
  for(const [id,text] of Object.entries(options))addOption(select,id,text);
  wrap.append(select);field.append(name,wrap);
  return {field,select};
}
function makeDial(control,initial,onChange,resetValue=control.initial){
  const {min,max,log,id,label,step}=control;
  const card=elem('label','dial'),wheel=elem('span','dial-wheel'),cap=elem('i','dial-cap');
  cap.setAttribute('aria-hidden','true');cap.append(elem('i','dial-face'),elem('i','dial-pointer'));
  const input=elem('input'), out=elem('output'),name=elem('span','dial-name',label);
  input.type='range';input.setAttribute('aria-label',label);
  // Use a uniform gesture distance for frequency and envelope time as well as linear units.
  input.min=0;input.max=1000;input.step=1;
  const fraction=value=>log?Math.log(value/min)/Math.log(max/min):(value-min)/(max-min);
  const paint=value=>{
    const turn=Math.max(0,Math.min(1,fraction(value)));
    wheel.style.setProperty('--sweep',270*turn+'deg');wheel.style.setProperty('--angle',(-135+270*turn)+'deg');
    const formatted=pretty(control,value);out.textContent=formatted;input.setAttribute('aria-valuetext',formatted);
    input.value=Math.round(turn*1000);
  };
  function set(raw){
    const t=Math.max(0,Math.min(1,raw/1000));
    const exact=log?min*(max/min)**t:min+(max-min)*t;
    const value=Math.max(min,Math.min(max,Number((min+Math.round((exact-min)/step)*step).toFixed(4))));
    paint(value);onChange(id,value);
  }
  input.oninput=()=>set(Number(input.value));
  // Duplo clique restaura apenas este controle ao valor original do preset.
  input.ondblclick=e=>{e.preventDefault();e.stopPropagation();set(fraction(resetValue)*1000)};
  card.title='Duplo clique para restaurar o valor inicial do preset';
  // Native keyboard steps must advance the physical value even when the range is quantized.
  input.onkeydown=e=>{
    const direction={ArrowUp:1,ArrowRight:1,ArrowDown:-1,ArrowLeft:-1}[e.key];if(!direction)return;
    e.preventDefault();const f=+input.value/1000;
    const val=log?min*(max/min)**f:min+(max-min)*f;
    const inc=log?Math.max(step,val*.035):Math.max(step,(max-min)/100);
    const next=Math.max(min,Math.min(max,val+direction*inc*(e.shiftKey?5:1)));
    set(fraction(next)*1000);
  };
  let drag;
  input.onpointerdown=e=>{
    if(e.button!==0||drag)return;e.preventDefault();input.focus({preventScroll:true});
    input.setPointerCapture(e.pointerId);drag={x:e.clientX,y:e.clientY,initial:+input.value,id:e.pointerId};
  };
  input.onpointermove=e=>{
    if(!drag||drag.id!==e.pointerId)return;
    const x=e.clientX-drag.x,y=drag.y-e.clientY;set(drag.initial+(Math.abs(y)>=Math.abs(x)?y:x)*(e.shiftKey?1:7));
  };
  input.onpointerup=e=>{if(drag?.id===e.pointerId)drag=null};
  input.onlostpointercapture=()=>{drag=null};
  wheel.append(elem('i','ticks'),elem('i','dial-arc'),cap,input);card.append(wheel,out,name);paint(initial);
  return card;
}
export class Panel {
  constructor(state,actions){
    this.state=state;this.actions=actions;this.cards={};this.panels={};this.soundfontInfo={name:null,programs:[],selected:0};
    this.sampleCounts={piano:{},electric:{}};
    const modules=document.getElementById('modules'),editors=document.getElementById('editors');
    for(const [id,definition] of Object.entries(engines)){
      const card=elem('div','module'),tab=elem('button','module-tab'),tone=elem('span','module-tone');
      tab.type='button';tab.id='tab-'+id;tab.setAttribute('aria-label','Editar '+definition.name.toLowerCase());
      tab.setAttribute('aria-controls','edit-'+id);tab.onclick=()=>actions.edit(id);
      tab.append(elem('span','module-name',definition.name),tone);
      const bottom=elem('div','module-bottom'), label=elem('label','mixrange'),level=elem('input');
      level.type='range';level.min=0;level.max=100;level.step=1;level.setAttribute('aria-label','Volume · '+definition.name);
      level.oninput=()=>actions.level(id,+level.value);
      level.title='Duplo clique para restaurar o volume inicial';
      level.ondblclick=e=>{e.preventDefault();level.value=definition.level;level.dispatchEvent(new Event('input',{bubbles:true}))};label.append(elem('span','','Vol.'),level);
      const toggle=elem('button','toggle'), txt=elem('span');toggle.type='button';toggle.onclick=()=>actions.toggle(id);
      toggle.append(elem('i','lamp'),txt);
      const fxToggle=elem('button','fx-toggle','FX');fxToggle.type='button';
      fxToggle.title='Atalho: ligar/desligar todos os efeitos deste instrumento, sem mudar as configurações';
      fxToggle.setAttribute('aria-label','Efeitos para '+definition.name);
      fxToggle.onclick=()=>actions.fxEnabled(id,!state.fx.enabled[id]);
      bottom.append(label,fxToggle,toggle);card.append(tab,bottom);modules.append(card);
      this.cards[id]={card,tab,tone,level,toggle,txt,fxToggle};
      const pane=elem('section','editor');pane.id='edit-'+id;pane.dataset.engine=id;
      pane.setAttribute('aria-labelledby','title-'+id);editors.append(pane);this.panels[id]=pane;
      this.drawEditor(id);
    }
    const fxCard=elem('div','module module-effects'),fxTab=elem('button','module-tab');
    fxTab.type='button';fxTab.id='tab-effects';fxTab.setAttribute('aria-controls','edit-effects');
    fxTab.append(elem('span','module-name','Efeitos'),elem('span','module-tone','8 sessões de efeitos'));
    fxTab.onclick=()=>actions.edit('effects');fxCard.append(fxTab);
    const fxBottom=elem('div','module-bottom');
    fxBottom.append(elem('span','fx-subtitle','2 Reverbs · 2 Delays · 2 Mod · EQ · Comp'));
    fxCard.append(fxBottom);modules.append(fxCard);
    this.cards.effects={card:fxCard,tab:fxTab};
    const pane=elem('section','editor fx-editor');pane.id='edit-effects';pane.dataset.engine='effects';
    pane.setAttribute('aria-labelledby','title-effects');editors.append(pane);this.panels.effects=pane;
    this.drawFXEditor();this.sync();
  }
  sync(){
    for(const [id,d] of Object.entries(engines)){
      const {card,tab,tone,level,toggle,txt,fxToggle}=this.cards[id],patch=this.state.patches[id];
      const on=Boolean(this.state.mask&d.bit),editing=this.state.editor===id;
      card.classList.toggle('editing',editing);tab.setAttribute('aria-expanded',String(editing));
      toggle.setAttribute('aria-pressed',String(on));
      toggle.setAttribute('aria-label',(on?'Desligar ':'Ligar ')+d.name.toLowerCase());
      txt.textContent=on?'Ligado':'Desligado';
      fxToggle.setAttribute('aria-pressed',String(this.state.fx.enabled[id]));
      fxToggle.textContent=this.state.fx.enabled[id]?'FX':'FX OFF';
      fxToggle.title=(this.state.fx.enabled[id]?'Desligar':'Ligar')+' todos os efeitos deste instrumento (atalho de bypass)';
      fxToggle.classList.toggle('on',this.state.fx.enabled[id]);
      level.value=patch.level;level.setAttribute('aria-valuetext',patch.level+'%');
      tone.textContent=(instrumentName(id,patch.values)||d.presets.find(p=>p.id===patch.preset).name)+(this.state.edits[id][patch.preset]?' *':'');
      this.panels[id].hidden=!editing;
    }
    this.cards.effects.card.classList.toggle('editing',this.state.editor==='effects');
    this.cards.effects.tab.setAttribute('aria-expanded',String(this.state.editor==='effects'));
    this.panels.effects.hidden=this.state.editor!=='effects';
  }
  drawEditor(id){
    const def=engines[id], patch=this.state.patches[id], pane=this.panels[id], top=elem('div','editor-top');
    const title=elem('div','editor-title'),heading=elem('h2','',def.name);heading.id='title-'+id;
    title.append(elem('span','editor-kicker','Editor de timbre'),heading);
    const relevant=presetsForInstrument(id,patch.values);
    const {field,select}=selectField('Preset',Object.fromEntries(relevant.map(x=>[x.id,x.name])),false);
    select.setAttribute('aria-label','Preset · '+def.name);
    if(!relevant.some(x=>x.id===patch.preset))addOption(select,patch.preset,'Personalizado · legado');
    select.value=patch.preset;
    field.title='Preset: configuração pronta do instrumento. Alterações manuais ficam marcadas com *.';
    select.onchange=()=>{
      rememberPatch(this.state,id);
      const p=fromPreset(id,select.value), saved=this.state.edits[id][select.value];
      if(saved)p.values=structuredClone(saved);
      p.level=patch.level;this.state.patches[id]=p;
      this.drawEditor(id);this.sync();this.actions.set(id);pane.querySelector('.tone-field select').focus({preventScroll:true});
    };
    const listen=elem('button','editor-btn');listen.type='button';listen.setAttribute('aria-label','Ouvir '+def.name.toLowerCase());
    listen.append(elem('i','play-icon'),document.createTextNode('Ouvir'));listen.onclick=()=>this.actions.listen(id);
    const restore=elem('button','editor-btn','Restaurar');
    restore.type='button';restore.setAttribute('aria-label','Restaurar este timbre de fábrica');
    restore.title='Restaurar este timbre de fábrica';
    restore.hidden=!this.state.edits[id][patch.preset];
    restore.onclick=()=>{
      const fresh=fromPreset(id,patch.preset);fresh.level=patch.level;
      this.state.patches[id]=fresh;rememberPatch(this.state,id);this.drawEditor(id);this.sync();
      this.actions.set(id);pane.querySelector('.tone-field select').focus({preventScroll:true});
    };
    top.append(title,field,listen,restore);
    const groups=elem('div','groups');
    for(const g of def.groups){
      const section=elem('div','ctrl-group'),choices=elem('div','choices'),dials=elem('div','dial-grid');
      section.append(elem('h3','',g.label));let n=0;
      const change=(name,value)=>{
        if(name===instrumentField[id] && patch.values[name]!==value){
          // A mudança do instrumento carrega o seu preset Natural, evitando
          // um modelo sonoro diferente do preset mostrado na barra superior.
          rememberPatch(this.state,id);
          const fresh=presetForInstrument(id,value),next=fromPreset(id,fresh.id);
          if(this.state.edits[id][fresh.id])next.values=structuredClone(this.state.edits[id][fresh.id]);
          next.level=patch.level;this.state.patches[id]=next;
          this.drawEditor(id);this.sync();this.actions.set(id,name);
          return;
        }
        patch.values[name]=value;rememberPatch(this.state,id);
        restore.hidden=!this.state.edits[id][patch.preset];this.sync();this.actions.set(id,name);
      };
      for(const control of g.controls){
        const val=patch.values[control.id];
        if(control.type==='select'){
          const result=selectField(control.label,control.options,true);
          result.select.value=val;result.select.onchange=()=>change(control.id,result.select.value);
          choices.append(result.field);
        }else if(control.type==='drawbars'){
          const bars=elem('div','drawbars');
          feet.forEach((foot,i)=>{
            const bar=elem('label','bar'),inp=elem('input'),out=elem('output','',String(val[i]));
            const color=['#905e4d','#905e4d','#d5ceba','#d5ceba','#464448','#d5ceba','#464448','#464448','#d5ceba'][i];
            bar.style.setProperty('--bar-color',color);inp.type='range';inp.min=0;inp.max=8;inp.step=1;inp.value=val[i];
            inp.setAttribute('aria-label','Registro '+foot);inp.title='Duplo clique para restaurar o registro';
            inp.ondblclick=e=>{e.preventDefault();const factory=fromPreset(id,patch.preset).values.bars?.[i]??control.initial[i];inp.value=factory;inp.dispatchEvent(new Event('input',{bubbles:true}))};
            inp.oninput=()=>{
              const next=patch.values.bars.slice();next[i]=+inp.value;out.textContent=inp.value;change('bars',next);
            };
            bar.append(elem('span','',foot),inp,out);bars.append(bar);
          });
          section.append(bars);
        }else if(control.type==='samplepack'){
          const picker=elem('div','sample-upload');
          const model=patch.values[instrumentField[id]];
          const count=this.sampleCounts[id]?.[model]||0;
          const input=elem('input');input.type='file';input.multiple=true;input.accept='.wav,.wave,.ogg,.mp3,audio/wav,audio/mpeg,audio/ogg';
          input.setAttribute('aria-label','Carregar amostras do '+instrumentName(id,patch.values));
          input.onchange=()=>{if(input.files?.length)this.actions.loadSamples(id,model,input.files)};
          const remove=elem('button','editor-btn','Retirar amostras');remove.type='button';
          remove.disabled=count===0;remove.onclick=()=>this.actions.clearSamples(id,model);
          const hint=elem('p','sample-hint',count
            ?`${count} amostras reais carregadas para ${instrumentName(id,patch.values)}. Permanecem apenas nesta sessão.`
            :'Para timbres mais realistas, selecione gravações WAV com nomes C4_v40.wav, C4_v100.wav, MIDI64_v100.wav. Carregamento local, sem envio de dados.');
          picker.append(input,remove,hint);section.append(picker);
        }else if(control.type==='soundfont'){
          const upload=elem('div','sf-upload');
          const file=elem('input');file.type='file';file.accept='.sf2';file.setAttribute('aria-label','Importar SoundFont SF2');
          file.onchange=()=>{if(file.files?.length)this.actions.loadSF(file.files[0])};
          const programLabel=elem('label','choice','Programa do SF2');
          const program=elem('select');program.id='sf-program';program.setAttribute('aria-label','Programa do SoundFont');
          if(!this.soundfontInfo.programs.length){program.disabled=true;addOption(program,'','Carregue um SF2')}
          else {for(const entry of this.soundfontInfo.programs)addOption(program,entry.id,entry.name);
            program.value=String(this.soundfontInfo.selected)}
          program.onchange=()=>this.actions.setProgram(+program.value);
          programLabel.append(program);
          const clear=elem('button','editor-btn','Retirar SF2');clear.type='button';
          clear.disabled=!this.soundfontInfo.programs.length;clear.onclick=()=>this.actions.clearSF();
          const hint=elem('p','sf-hint',this.soundfontInfo.name?`Em uso: ${this.soundfontInfo.name} · somente nesta sessão`:'Timbres internos prontos. Importe um SF2 PCM para usar suas amostras; arquivos SFZ e SF3 ainda não são compatíveis.');
          upload.append(file,programLabel,clear,hint);section.append(upload);
        }else{
          const factory=fromPreset(id,patch.preset).values[control.id]??control.initial;
          dials.append(makeDial(control,val,change,factory));n++
        }
      }
      if(choices.children.length)section.append(choices);
      if(n){section.append(dials)}
      section.style.setProperty('--basis',g.controls[0].type==='drawbars'?1.05:Math.max(3,n)/3);
      groups.append(section);
    }
    pane.replaceChildren(top,groups);
  }
  updateSamples(id,model,count){this.sampleCounts[id][model]=count;this.drawEditor(id);this.sync()}
  updateSoundFont(name,programs,selected=0){
    this.soundfontInfo={name,programs,selected};this.drawEditor('sf');this.sync();
  }
  drawFXEditor(){
    const pane=this.panels.effects;
    const top=elem('div','editor-top'),title=elem('div','editor-title');
    const head=elem('h2','','Efeitos');head.id='title-effects';
    title.append(elem('span','editor-kicker','Rack de efeitos · 8 sessões'),head);
    top.append(title,elem('p','fx-help','Cada efeito pode atuar em vários instrumentos ao mesmo tempo. O botão FX de cada motor desliga todos os efeitos apenas naquele instrumento, mantendo seu som seco.'));
    const rack=elem('div','fx-rack');
    const labels=Object.fromEntries(Object.entries(engines).map(([id,d])=>[id,d.name]));
    for(const def of effectsDefinition){
      const slot=this.state.fx.slots[def.id],card=elem('div','fx-slot');
      card.dataset.effect=def.id;
      const header=elem('div','fx-slot-header');
      const enabled=elem('input');enabled.type='checkbox';enabled.checked=slot.active;
      enabled.setAttribute('aria-label','Ativar '+def.label);
      enabled.onchange=()=>this.actions.fxChange(def.id,'active',enabled.checked);
      const h=elem('h3','',def.label),tog=elem('label','fx-enable');tog.append(enabled,elem('span','','Ativo'));
      header.append(h,tog);card.append(header);
      const settings=elem('div','fx-controls');
      const routing=elem('fieldset','fx-routing');
      routing.append(elem('legend','','Aplicar a estes módulos'));
      const checks=elem('div','fx-targets');
      for(const [id,name] of Object.entries(labels)){
        const label=elem('label','fx-target'),input=elem('input');input.type='checkbox';
        input.checked=slot.targets.includes(id);
        input.setAttribute('aria-label',def.label+' no '+name);
        input.onchange=()=>{
          const targets=new Set(slot.targets);
          if(input.checked)targets.add(id);else targets.delete(id);
          this.actions.fxChange(def.id,'targets',[...targets]);
        };
        label.append(input,elem('span','',name));checks.append(label);
      }
      routing.append(checks);card.append(routing);
      const controls=[['mix','Intensidade',0,100,1]];
      if(def.type==='reverb')controls.push(['time','Duração',.3,3.8,.1]);
      else if(def.type==='delay')controls.push(['time','Tempo',.04,1.5,.01],['feedback','Feedback',0,80,1]);
      else if(def.type==='mod')controls.push(['rate','Velocidade',.1,12,.1],['depth','Profundidade',0,100,1]);
      else if(def.type==='eq')controls.push(['low','Graves',-12,12,1],['mid','Médios',-12,12,1],['high','Agudos',-12,12,1]);
      else if(def.type==='comp')controls.push(['threshold','Threshold',-50,0,1],['ratio','Ratio',1,16,.5]);
      for(const [id,label,min,max,step] of controls){
        const l=elem('label','fx-control',label);const range=elem('input');range.type='range';
        range.min=min;range.max=max;range.step=step;range.value=slot[id];
        range.setAttribute('aria-label',label+' '+def.label);
        const value=elem('output','',String(slot[id]));
        range.title='Duplo clique para restaurar o valor inicial do efeito';
        range.ondblclick=e=>{e.preventDefault();range.value=defaultSlot(def.id)[id];range.dispatchEvent(new Event('input',{bubbles:true}))};
        range.oninput=()=>{value.textContent=range.value;this.actions.fxChange(def.id,id,+range.value)};
        l.append(range,value);settings.append(l);
      }
      card.append(settings);rack.append(card);
    }
    pane.replaceChildren(top,rack);
  }
}
