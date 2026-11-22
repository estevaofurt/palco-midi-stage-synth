import {engines,scenes,loadState,saveState} from './patches.js';
import {Stage} from './stage.js';
import {Panel,addOption} from './panel.js';
const byId=id=>document.getElementById(id);
let storage;try{storage=localStorage}catch{storage=null}
const state=loadState(storage);
let ctx,stage,access,panel,saveTimer,previewTimer,previewToken=0;
let frame=0,lastMeter=0;
const midiPorts=new Map(),activePointers=new Map(), keyboardButtons=new Map();
const noteNames=['Dó','Dó♯','Ré','Mi♭','Mi','Fá','Fá♯','Sol','Sol♯','Lá','Si♭','Si'];
// Teclado do computador: duas oitavas cromáticas a partir da oitava selecionada.
const computerOffsets={KeyA:0,KeyW:1,KeyS:2,KeyE:3,KeyD:4,KeyF:5,KeyT:6,KeyG:7,KeyY:8,KeyH:9,KeyU:10,KeyJ:11,KeyK:12,KeyO:13,KeyL:14,KeyP:15,Semicolon:16,BracketLeft:17,Quote:18,BracketRight:19};
const activeComputerKeys=new Set();
const midiLabel=(key)=>noteNames[key%12]+(Math.floor(key/12)-1);
function save(){
  clearTimeout(saveTimer);saveTimer=setTimeout(()=>saveState(storage,state),140);
}
function report(text){const s=byId('status');s.textContent=text;s.hidden=!text}
function syncScene(){
  const selected=scenes.find(s=>s.mask===state.mask&&Boolean(s.duo)===state.duo);
  byId('custom').textContent=state.duo?'Duo personalizado':'Camadas livres';
  byId('scene').value=selected?.id||'custom';
  const count=Object.values(engines).filter(d=>state.mask&d.bit).length;
  byId('layer-count').textContent=count+(count===1?' motor ligado':' motores ligados');
  panel.sync();
}
for(const s of scenes)addOption(byId('scene'),s.id,s.name);
const custom=addOption(byId('scene'),'custom','Camadas livres');custom.id='custom';custom.disabled=true;
byId('scene').onchange=e=>{
  const s=scenes.find(item=>item.id===e.target.value);if(!s)return;
  state.mask=s.mask;state.duo=Boolean(s.duo);
  if(!(state.mask&engines[state.editor].bit))state.editor=Object.keys(engines).find(id=>engines[id].bit&state.mask);
  stage?.applyRouting();syncScene();save();
};
function edit(id){state.editor=id;panel.sync();save()}
function toggle(id){state.mask^=engines[id].bit;stage?.applyRouting();syncScene();save()}
panel=new Panel(state,{
  edit,toggle,
  level(id,level){state.patches[id].level=level;stage?.update(id,'level');panel.sync();save()},
  set(id,key){stage?.update(id,key);save()},listen
});
syncScene();
const meterBars=[];
for(let i=0;i<24;i++){const mark=document.createElement('i');byId('meter').append(mark);meterBars.push(mark)}
const meterData=new Float32Array(256);
function updateMeter(time){
  frame=0;if(document.hidden||ctx?.state!=='running')return;
  if(time-lastMeter>80){
    lastMeter=time;stage.meter.getFloatTimeDomainData(meterData);
    let peak=0;for(const v of meterData)peak=Math.max(peak,Math.abs(v));
    const db=20*Math.log10(Math.max(.00001,peak)),bars=Math.max(0,Math.round((db+48)/2));
    for(let i=0;i<24;i++)meterBars[i].classList.toggle('lit',i<bars);
    byId('peak').textContent=db< -59?'−∞ dB':Math.round(db)+' dB';
  }
  frame=requestAnimationFrame(updateMeter);
}
function resetMeter(){
  if(frame)cancelAnimationFrame(frame);frame=0;meterBars.forEach(b=>b.classList.remove('lit'));byId('peak').textContent='−∞ dB';
}
function displayAudio(){
  const on=ctx?.state==='running';
  byId('power').classList.toggle('on',on);
  byId('power').querySelector('span:last-child').textContent=on?'Áudio ativo':'Ativar áudio';
  if(on&&!frame&&!document.hidden)frame=requestAnimationFrame(updateMeter);else if(!on)resetMeter();
}
async function startAudio(){
  if(!ctx){
    const Audio=window.AudioContext||window.webkitAudioContext;
    if(!Audio)throw Error('Áudio indisponível neste navegador.');
    ctx=new Audio({latencyHint:'interactive'});
    const resume=ctx.resume();
    try{
      stage=new Stage(ctx,state,{bank:text=>byId('bank').textContent=text,note:paintKeys,pedal:paintPedal});
    }catch(e){
      resume.catch(()=>{});ctx.close().catch(()=>{});ctx=null;stage=null;throw e;
    }
    ctx.addEventListener('statechange',displayAudio);
    await resume;
  }else if(ctx.state!=='running')await ctx.resume();
  displayAudio();if(ctx.state!=='running')throw Error('Toque em Ativar áudio para liberar o som.');
  stage.instruments.piano.bank.load();
}
byId('power').onclick=()=>startAudio().then(()=>report('')).catch(e=>report(e.message));
function stopPreview(){previewToken++;clearTimeout(previewTimer);if(stage)stage.disconnect('preview')}
async function listen(id){
  stopPreview();const token=previewToken;
  try{
    await startAudio();
    if(id==='piano'&&!stage.instruments.piano.bank.atlas)await stage.instruments.piano.bank.load();
    if(token!==previewToken)return;
    const mask=engines[id].bit;
    const play=(key,velocity,duration)=>{
      const voice=stage.startNote('preview',0,key,velocity,mask);
      setTimeout(()=>stage?.releaseId(voice),duration);
    };
    play(60,49,300);
    previewTimer=setTimeout(()=>{if(token===previewToken)play(60,112,680)},420);
  }catch(e){report(e.message)}
}
function paintKeys(){
  const stats=stage?.voiceStats();
  byId('voice-status').textContent=stats?`${stats.active}/${stats.limit} vozes · ${stats.held} teclas`:'0/32 vozes';
  const held=new Set();
  if(stage)for(const v of stage.voices.values())if(v.held)held.add(v.key);
  for(const [key,button] of keyboardButtons)button.classList.toggle('down',held.has(key));
}
function paintPedal(){
  const touch=Boolean(stage?.groups.get('touch/0')?.pedal);
  const any=stage&&[...stage.groups.values()].some(g=>g.pedal);
  byId('pedal').setAttribute('aria-pressed',String(touch));byId('pedal').classList.toggle('on',Boolean(any));
}
function cut(){
  stopPreview();stage?.panic();activePointers.clear();activeComputerKeys.clear();paintPedal();paintKeys();
}
byId('panic').onclick=cut;
byId('pedal').onclick=async()=>{try{
  await startAudio();const g=stage.group('touch',0);stage.setPedal(g,!g.pedal);
}catch(e){report(e.message)}};
let octave=4;
const narrow=matchMedia('(max-width:640px)');
function setKeys(){
  if(stage)stage.disconnect('touch');activePointers.clear();keyboardButtons.clear();
  const board=byId('keys');board.replaceChildren();
  const octaves=narrow.matches?1:2,whites=octaves*7+1,base=12*(octave+1);
  board.style.setProperty('--whites',whites);byId('octave').textContent=octave;
  byId('oct-down').disabled=octave<=0;byId('oct-up').disabled=octave>=6;
  let whiteIndex=0;
  for(let j=0;j<=octaves*12;j++){
    const pitch=j%12,black=[1,3,6,8,10].includes(pitch),key=base+j;
    const button=document.createElement('button');button.type='button';button.className=black?'key black':'key';
    button.dataset.note=key;button.setAttribute('aria-label',midiLabel(key));
    if(black)button.style.left=(whiteIndex-.29)*100/whites+'%';
    else{whiteIndex++;if(pitch===0)button.textContent='Dó'+(Math.floor(key/12)-1)}
    let lastKeyboardActivation=-Infinity;
    button.onkeydown=e=>{
      if((e.key===' '||e.key==='Enter')&&!e.repeat){
        lastKeyboardActivation=performance.now();
        e.preventDefault();press('kbd-'+key,button,90);
      }
    };
    button.onkeyup=e=>{if(e.key===' '||e.key==='Enter'){e.preventDefault();lift('kbd-'+key)}};
    button.onblur=()=>lift('kbd-'+key);
    button.onclick=e=>{
      // Enter emits click on keydown; Space emits it on keyup. Do not sound twice.
      if(e.detail===0 && performance.now()-lastKeyboardActivation>350 && !activePointers.has('kbd-'+key)){
        const a='assist-'+key;press(a,button,94);setTimeout(()=>lift(a),220);
      }
    };
    board.append(button);keyboardButtons.set(key,button);
  }
  paintKeys();
}
async function press(pointer,button,velocity){
  const key=Number(button.dataset.note);
  if(!Number.isInteger(key))return;
  lift(pointer);
  const slot={key,id:null};
  activePointers.set(pointer,slot);
  try{
    if(!stage||ctx?.state!=='running')await startAudio();
    if(activePointers.get(pointer)!==slot)return;
    slot.id=stage.startNote('touch',0,key,velocity);
  }catch(e){activePointers.delete(pointer);report(e.message)}
}
function lift(pointer){
  const slot=activePointers.get(pointer);if(!slot)return;
  activePointers.delete(pointer);stage?.releaseId(slot.id);
}
byId('oct-down').onclick=()=>{if(octave>0)octave--;setKeys()};
byId('oct-up').onclick=()=>{if(octave<6)octave++;setKeys()};
const keys=byId('keys');
keys.onpointerdown=e=>{
  const k=e.target.closest('button.key');if(!k||e.button!==0)return;
  e.preventDefault();
  try{keys.setPointerCapture(e.pointerId)}catch{}
  press(e.pointerId,k,94);
};
keys.onpointermove=e=>{
  const slot=activePointers.get(e.pointerId);if(!slot)return;
  const at=document.elementFromPoint(e.clientX,e.clientY)?.closest('#keys .key');
  if(at&&+at.dataset.note!==slot.key){lift(e.pointerId);press(e.pointerId,at,94)}
};
keys.onpointerup=keys.onpointercancel=keys.onlostpointercapture=e=>lift(e.pointerId);
narrow.addEventListener('change',setKeys);setKeys();
const computerTargetIsEditable=target=>Boolean(target?.closest?.('input,select,textarea,[contenteditable="true"],button:not(.key)'));
document.addEventListener('keydown',e=>{
  if(e.repeat||e.altKey||e.metaKey||e.ctrlKey||e.isComposing||computerTargetIsEditable(e.target))return;
  const offset=computerOffsets[e.code];if(offset===undefined)return;
  e.preventDefault();
  if(activeComputerKeys.has(e.code))return;
  activeComputerKeys.add(e.code);
  const key=12*(octave+1)+offset;
  press('pc-'+e.code,keyboardButtons.get(key)||{dataset:{note:key}},e.shiftKey?110:94);
});
document.addEventListener('keyup',e=>{
  if(!activeComputerKeys.has(e.code))return;
  activeComputerKeys.delete(e.code);lift('pc-'+e.code);
});
window.addEventListener('blur',()=>{
  for(const code of activeComputerKeys)lift('pc-'+code);
  activeComputerKeys.clear();
});
function bindMIDI(){
  const names=[];
  for(const port of access.inputs.values())if(port.state==='connected'){
    names.push(port.name||'Controlador MIDI');
    if(midiPorts.get(port.id)!==port){
      midiPorts.set(port.id,port);port.onmidimessage=e=>stage?.message(port.id,e.data);
    }
  }
  byId('midi-status').textContent=names.length?names.join(' · '):'Permissão concedida. Aguardando um controlador MIDI.';
  byId('midi').classList.toggle('on',names.length>0);
  byId('midi').lastChild.textContent=names.length?'MIDI ligado':'Conectar MIDI';
}
byId('midi').onclick=async()=>{try{
  if(!navigator.requestMIDIAccess)throw Error('MIDI indisponível neste navegador. Abra a versão HTTPS no Chrome para computador.');
  const [allowed]=await Promise.all([navigator.requestMIDIAccess({sysex:false}),startAudio()]);
  access=allowed;access.onstatechange=e=>{
    if(e.port.type==='input'&&e.port.state==='disconnected'){
      e.port.onmidimessage=null;midiPorts.delete(e.port.id);stage.disconnect(e.port.id);
    }
    bindMIDI();
  };bindMIDI();report('');
}catch(e){
  const denied=['NotAllowedError','SecurityError'].includes(e.name)||/permission/i.test(e.message);
  report(denied?'O navegador recusou o acesso MIDI. Permita dispositivos MIDI nas permissões desta página e toque em Conectar MIDI.':e.message);
}};
document.addEventListener('visibilitychange',()=>{if(document.hidden){cut();resetMeter()}else displayAudio()});
window.addEventListener('pagehide',()=>{cut();saveState(storage,state)});
