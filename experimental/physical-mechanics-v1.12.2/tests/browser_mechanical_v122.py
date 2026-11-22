"""Validate mechanical toggle in UI on mobile and desktop; NOT a real AudioWorklet test."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    for name,settings in [('desktop',dict(viewport={'width':1280,'height':780})),('mobile',dict(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,user_agent='Mozilla/5.0 (Linux; Android 14; moto g04s) AppleWebKit/537.36 Chrome/131 Mobile Safari/537.36'))]:
        ctx=browser.new_context(**settings);page=ctx.new_page();errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        def route(request):
            f=ROOT/request.request.url.split('://',1)[-1].split('/',1)[-1].split('?',1)[0]
            if f.is_file():request.fulfill(status=200,body=f.read_bytes(),content_type={'.js':'text/javascript','.css':'text/css','.html':'text/html'}.get(f.suffix,'application/octet-stream'))
            else:request.fulfill(status=404,body='not found')
        page.route('**/*',route)
        page.set_content((ROOT/'index.html').read_text().replace('<head>','<head><base href="https://stage-synth.test/">'),wait_until='load')
        page.wait_for_function('window.__palcoTest!==undefined')
        page.locator('#tab-piano').click()
        select=page.locator('select[aria-label="Acoplamento mecânico"]')
        assert select.count()==1,(name,'missing selector')
        assert select.input_value()=='on'
        assert select.locator('option').all_text_contents()==['Ponte, tampo e cordas simpáticas','Som anterior · comparar']
        select.select_option('off')
        assert page.evaluate('window.__palcoTest.state.patches.piano.values.mechanicalModel')=='off'
        select.select_option('on')
        assert page.evaluate('window.__palcoTest.state.patches.piano.values.mechanicalModel')=='on'
        assert page.locator('.module').count()==6
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth+2')
        assert not errors,errors
        print('PASS',name,'mechanical selector ON/OFF, six modules, no horizontal overflow',flush=True)
        ctx.close()
    browser.close()
