from playwright.sync_api import sync_playwright
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
 for name,settings in [('desktop',dict(viewport={'width':1280,'height':800})),('mobile',dict(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,user_agent='Mozilla/5.0 (Linux; Android 14; moto g04s) AppleWebKit/537.36 Chrome/131 Mobile Safari/537.36'))]:
  ctx=browser.new_context(**settings)
  page=ctx.new_page();errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def route(request):
   file=ROOT/request.request.url.split('://',1)[-1].split('/',1)[-1].split('?',1)[0]
   if file.is_file():request.fulfill(status=200,body=file.read_bytes(),content_type={'.js':'text/javascript','.css':'text/css','.html':'text/html'}.get(file.suffix,'application/octet-stream'),headers={'Access-Control-Allow-Origin':'*'})
   else:request.fulfill(status=404,body='not found')
  page.route('**/*',route)
  page.set_content((ROOT/'index.html').read_text().replace('<head>','<head><base href="https://stage-synth.test/">'),wait_until='load')
  page.wait_for_function('window.__palcoTest!==undefined',timeout=12000)
  selector=page.locator('select[aria-label="Motor do piano"]')
  assert selector.is_visible(), 'selector must be in piano module'
  options=selector.locator('option').all_text_contents()
  assert options==['A · Claude (modal)','B · Stage físico anterior (v1.9.5)','C · Novo Stage mecânico','Clássico · compatibilidade'],options
  assert page.locator('#modules .module').count()==6
  assert page.locator('#enable-mechanical-piano,.stage-mechanics-link,a[href*="acesso-motor"]').count()==0
  assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+2')
  assert selector.input_value()=='physical',selector.input_value()
  assert page.locator('select[aria-label="Acoplamento mecânico"]').input_value()=='on'
  # Check that UI choices are saved and can switch back without leaving Piano Acústico.
  selector.select_option('modal');page.wait_for_timeout(250)
  mode=page.evaluate('window.__palcoTest.state.patches.piano.values.soundEngine')
  assert mode=='modal'
  # Opaque browser-test origin blocks localStorage; persistence tested with Node loadState.
  selector.select_option('physicalLegacy');page.wait_for_timeout(250)
  assert page.evaluate('window.__palcoTest.state.patches.piano.values.soundEngine')=='physicalLegacy'
  selector.select_option('physical');page.wait_for_timeout(250)
  assert page.evaluate('window.__palcoTest.state.patches.piano.values.soundEngine')=='physical'
  # Turn extra mechanics on/off while C remains selected.
  mechanics=page.locator('select[aria-label="Acoplamento mecânico"]')
  mechanics.select_option('off');assert mechanics.input_value()=='off'
  mechanics.select_option('on');assert mechanics.input_value()=='on'
  assert not errors, errors
  print(name,json.dumps({'options':options,'engine':selector.input_value(),'mechanics':mechanics.input_value(),'profile':page.locator('#audio-profile').input_value(),'noNewCategory':True,'errors':errors},ensure_ascii=False),flush=True)
  ctx.close()
 browser.close()
