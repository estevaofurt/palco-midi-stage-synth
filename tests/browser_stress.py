"""Testes de estresse Web Audio + teclado físico simulado (Chromium/Playwright)."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parents[1]
ORIGIN='https://palco-midi.test/'
with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
  page=browser.new_page(viewport={'width':1366,'height':900});errors=[];missing=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def serve(route):
    name=route.request.url.split('://',1)[-1].split('/',1)[-1].split('?',1)[0]
    f=ROOT/name
    if f.is_file():route.fulfill(status=200,body=f.read_bytes(),content_type={'.js':'text/javascript','.css':'text/css','.html':'text/html'}.get(f.suffix,'text/plain'))
    else:missing.append(name);route.fulfill(status=404,body='missing')
  page.route('**/*',serve)
  html=(ROOT/'index.html').read_text().replace('<script src="./app.js" type="module"></script>','')
  page.set_content(html)
  page.add_style_tag(content=(ROOT/'panel.css').read_text())
  page.add_script_tag(url=ORIGIN+'app.js',type='module')
  page.wait_for_timeout(500)
  page.locator('#power').click()
  page.wait_for_timeout(450)
  # Teclado do computador e eventos de repetição de tecla
  page.locator('body').click(position={'x':10,'y':20})
  page.keyboard.down('a')
  page.wait_for_timeout(55)
  assert page.locator('#keys button.key.down').count()==1, 'tecla A nao acionou o piano'
  page.keyboard.down('a')
  page.wait_for_timeout(30)
  assert page.locator('#keys button.key.down').count()==1, 'keydown repetido iniciou duas notas'
  page.keyboard.up('a')
  page.wait_for_timeout(80)
  assert page.locator('#keys button.key.down').count()==0, 'nota presa apos soltar tecla fisica'
  # Enter e espaço no teclado virtual não devem produzir uma nota adicional após keyup.
  b=page.locator('#keys button.key').first
  b.focus()
  page.keyboard.down('Space');page.wait_for_timeout(35)
  assert page.locator('#keys button.key.down').count()==1
  page.keyboard.up('Space');page.wait_for_timeout(60)
  assert page.locator('#keys button.key.down').count()==0
  # Modos de edição não devem reagir a atalho musical quando alguém digita.
  page.locator('#scene').focus();page.keyboard.down('a');page.wait_for_timeout(50)
  assert page.locator('#keys button.key.down').count()==0
  page.keyboard.up('a')
  # Ciclo MIDI: 60 notas e capacidade <=32, sustain, modo DUO, pânico e desconexão.
  result=page.evaluate('''async (origin) => {
    const [{Stage},{loadState}]=await Promise.all([import(origin+'stage.js'),import(origin+'patches.js')]);
    const ctx=new AudioContext({latencyHint:'interactive'});await ctx.resume();
    const state=loadState({getItem(){return null},setItem(){}});state.mask=4;
    let updates=0;const stage=new Stage(ctx,state,{note:()=>updates++});
    for(let n=0;n<60;n++)stage.message('deviceA',[0x90,40+n,100]);
    const peak=stage.voiceStats();
    for(let n=0;n<60;n++)stage.message('deviceA',[0x80,40+n,0]);
    stage.message('deviceA',[0xb0,64,127]);
    stage.message('deviceA',[0x90,64,100]);
    stage.message('deviceA',[0x80,64,0]);
    const sustained=stage.voiceStats();
    stage.message('deviceA',[0xb0,64,0]);
    state.mask=7;state.duo=true;
    const organId=stage.startNote('deviceA',1,60,96);
    const organParts=[...stage.voices.get(organId).parts.keys()];
    stage.applyRouting();
    stage.disconnect('deviceA');
    await new Promise(r=>setTimeout(r,210));
    const after=stage.voiceStats();
    stage.message('deviceB',[0x90,62,100]);stage.panic();
    await new Promise(r=>setTimeout(r,100));
    const final=stage.voiceStats();
    await ctx.close();
    return {peak,sustained,organParts,after,final,groups:stage.groups.size,updates};
  }''',ORIGIN)
  print(json.dumps({'result':result,'errors':errors,'missing':missing},ensure_ascii=False,indent=2))
  assert result['peak']['active']<=32 and result['peak']['held']<=32
  assert result['sustained']['held']==0 and result['sustained']['active']>=1
  assert result['organParts']==['organ']
  assert result['after']['active']==0 and result['final']['active']==0
  assert result['groups']==0
  assert not errors,errors
  assert set(missing)<= {'piano/banco.json'},missing
  browser.close()
