import {engines,feet,fromPreset,pretty,rememberPatch} from './patches.js';
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
function makeDial(control,initial,onChange){
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
    this.state=state;this.actions=actions;this.cards={};this.panels={};
    const modules=document.getElementById('modules'),editors=document.getElementById('editors');
    for(const [id,definition] of Object.entries(engines)){
      const card=elem('div','module'),tab=elem('button','module-tab'),tone=elem('span','module-tone');
      tab.type='button';tab.id='tab-'+id;tab.setAttribute('aria-label','Editar '+definition.name.toLowerCase());
      tab.setAttribute('aria-controls','edit-'+id);tab.onclick=()=>actions.edit(id);
      tab.append(elem('span','module-name',definition.name),tone);
      const bottom=elem('div','module-bottom'), label=elem('label','mixrange'),level=elem('input');
      level.type='range';level.min=0;level.max=100;level.step=1;level.setAttribute('aria-label','Volume · '+definition.name);
      level.oninput=()=>actions.level(id,+level.value);label.append(elem('span','','Vol.'),level);
      const toggle=elem('button','toggle'), txt=elem('span');toggle.type='button';toggle.onclick=()=>actions.toggle(id);
      toggle.append(elem('i','lamp'),txt);bottom.append(label,toggle);card.append(tab,bottom);modules.append(card);
      this.cards[id]={card,tab,tone,level,toggle,txt};
      const pane=elem('section','editor');pane.id='edit-'+id;pane.dataset.engine=id;
      pane.setAttribute('aria-labelledby','title-'+id);editors.append(pane);this.panels[id]=pane;
      this.drawEditor(id);
    }
    this.sync();
  }
  sync(){
    for(const [id,d] of Object.entries(engines)){
      const {card,tab,tone,level,toggle,txt}=this.cards[id],patch=this.state.patches[id];
      const on=Boolean(this.state.mask&d.bit),editing=this.state.editor===id;
      card.classList.toggle('editing',editing);tab.setAttribute('aria-expanded',String(editing));
      toggle.setAttribute('aria-pressed',String(on));
      toggle.setAttribute('aria-label',(on?'Desligar ':'Ligar ')+d.name.toLowerCase());
      txt.textContent=on?'Ligado':'Desligado';level.value=patch.level;level.setAttribute('aria-valuetext',patch.level+'%');
      tone.textContent=d.presets.find(p=>p.id===patch.preset).name+(this.state.edits[id][patch.preset]?' *':'');
      this.panels[id].hidden=!editing;
    }
  }
  drawEditor(id){
    const def=engines[id], patch=this.state.patches[id], pane=this.panels[id], top=elem('div','editor-top');
    const title=elem('div','editor-title'),heading=elem('h2','',def.name);heading.id='title-'+id;
    title.append(elem('span','editor-kicker','Editor de timbre'),heading);
    const {field,select}=selectField('Timbre',Object.fromEntries(def.presets.map(x=>[x.id,x.name])),false);
    select.setAttribute('aria-label','Timbre · '+def.name);select.value=patch.preset;
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
            inp.setAttribute('aria-label','Registro '+foot);inp.oninput=()=>{
              const next=patch.values.bars.slice();next[i]=+inp.value;out.textContent=inp.value;change('bars',next);
            };
            bar.append(elem('span','',foot),inp,out);bars.append(bar);
          });
          section.append(bars);
        }else{dials.append(makeDial(control,val,change));n++}
      }
      if(choices.children.length)section.append(choices);
      if(n){dials.style.setProperty('--cols',n);section.append(dials)}
      section.style.setProperty('--basis',g.controls[0].type==='drawbars'?1.05:Math.max(3,n)/3);
      groups.append(section);
    }
    pane.replaceChildren(top,groups);
  }
}
