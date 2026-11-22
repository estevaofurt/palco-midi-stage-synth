from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    for name,kwargs in [('desktop',dict(viewport={'width':1280,'height':780})),('mobile',dict(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,user_agent='Mozilla/5.0 (Linux; Android 14; moto g04s) AppleWebKit/537.36 Chrome/131 Mobile Safari/537.36'))]:
        context=browser.new_context(**kwargs)
        page=context.new_page()
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        def route(route):
            path=ROOT / route.request.url.split('://',1)[-1].split('/',1)[-1].split('?',1)[0]
            if path.is_file():route.fulfill(status=200,body=path.read_bytes(),content_type={'.js':'text/javascript','.css':'text/css','.html':'text/html'}.get(path.suffix,'application/octet-stream'))
            else:route.fulfill(status=404,body='not found')
        page.route('**/*',route)
        page.set_content((ROOT/'index.html').read_text().replace('<head>','<head><base href="https://stage-synth.test/">'),wait_until='load')
        page.wait_for_function('window.__palcoTest!==undefined')
        page.locator('#tab-piano').click()
        selector=page.locator('select[aria-label="Motor do piano"]')
        assert selector.count()==1
        assert selector.locator('option').all_text_contents()==['A · Claude (modal)','B · Stage físico anterior (v1.9.5)','C · Novo Stage mecânico','Clássico · compatibilidade']
        for option in ['physicalLegacy','modal','physical']:
            selector.select_option(option)
            assert page.evaluate('window.__palcoTest.state.patches.piano.values.soundEngine')==option
        assert page.locator('.module').count()==6
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+2')
        assert not errors,errors
        print('PASS',name,'seletor A/B/C, 6 módulos, sem erros de JS',flush=True)
        context.close()
    browser.close()
