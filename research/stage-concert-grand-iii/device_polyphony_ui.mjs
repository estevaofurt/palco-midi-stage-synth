import {STORAGE_KEY} from './polyphony_policy.mjs';
const $=id=>document.getElementById(id),fields=['engine','quality','profile','rate'];
let worker=null,result=null;
function idle(){worker?.terminate();worker=null;$('start').disabled=false;$('cancel').disabled=true;for(const k of fields)$(k).disabled=false}
function clear(){result=null;$('apply').disabled=true;$('rows').replaceChildren()}
for(const k of fields)$(k).onchange=()=>{clear();$('status').textContent='Configuração alterada; realize um novo teste.'};
$('start').onclick=()=>{
  if(worker)return;clear();const c=Object.fromEntries(fields.map(k=>[k,$(k).value]));c.rate=Number(c.rate);
  $('start').disabled=true;$('cancel').disabled=false;for(const k of fields)$(k).disabled=true;
  $('status').textContent='Avaliando capacidade local...';
  try{worker=new Worker(new URL('./device_polyphony_worker.mjs',import.meta.url),{type:'module'});
    worker.onerror=()=>{idle();$('status').textContent='Falha no teste local.'};
    worker.onmessage=({data:d})=>{
      if(d.type==='row'){
        const r=d.row,tr=document.createElement('tr');
        for(const val of [r.voices,r.trial+1,(100*r.p99).toFixed(1)+'%',r.overruns,r.pass?'Passou':'Sem margem']){
          const td=document.createElement('td');td.textContent=String(val);tr.append(td)
        }$('rows').append(tr);
      }else if(d.type==='done'){
        idle();result=d.recommended;
        $('apply').disabled=result===null;
        $('status').textContent=result===null?'Nenhuma configuração atingiu a margem. Mantenha o limite conservador.':result+' vozes sugeridas para esta configuração experimental.';
      }else if(d.type==='error'){idle();$('status').textContent='Teste interrompido: '+d.message}
    };worker.postMessage(c);
  }catch(e){idle();$('status').textContent='Não foi possível iniciar o teste.'}
};
$('cancel').onclick=()=>{idle();clear();$('status').textContent='Teste cancelado.'};
$('apply').onclick=()=>{
  if(result===null)return;
  try{localStorage.setItem(STORAGE_KEY,String(result));$('status').textContent='Preferência salva. Volte ao aplicativo para aplicá-la.'}
  catch(e){$('status').textContent='Não foi possível salvar a preferência neste navegador.'}
};
