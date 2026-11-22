"""Panel regression without network: UI load via routed modules.
This does not validate actual AudioWorklet playback: browser blocks local secure origins.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    for name,opts in [
        ('moto-g04s',{'viewport':{'width':390,'height':844},'has_touch':True,'is_mobile':True,'user_agent':'Mozilla/5.0 (Linux; Android 14; moto g04s) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36'}),
        ('desktop',{'viewport':{'width':1280,'height':800}})
    ]:
        ctx=browser.new_context(**opts);page=ctx.new_page();errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        def route_req(route):
            path=route.request.url.split('://',1)[-1].split('/',1)[-1].split('?',1)[0]
            file=ROOT/(path or 'index.html')
            if file.is_file():route.fulfill(status=200,body=file.read_bytes(),content_type={'.js':'text/javascript','.html':'text/html','.css':'text/css'}.get(file.suffix,'application/octet-stream'))
            else:route.fulfill(status=404,body='not found')
        page.route('**/*',route_req)
        html=(ROOT/'index.html').read_text()
        page.set_content(html.replace('<head>','<head><base href="https://stage-synth.test/">'),wait_until='load')
        page.wait_for_function('window.__palcoTest!==undefined')
        assert page.locator('.module').count()==6
        page.locator('#tab-piano').click()
        opts1=page.locator('#edit-piano select[aria-label="Motor do piano"]')
        vals=opts1.locator('option').evaluate_all('(els)=>els.map(e=>e.value)')
        assert vals==['modal','physicalLegacy','physical','classic'],vals
        profile=page.evaluate('window.__palcoTest.profile')
        if name=='moto-g04s':assert opts1.input_value()=='physical'
        opts1.select_option('physical')
        quality=page.locator('#edit-piano select[aria-label="Detalhe físico"]')
        quality.select_option('eco')
        assert quality.input_value()=='eco'
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        page.screenshot(path=str(ROOT/f'preview_{name}_v19.png'),full_page=True)
        assert not errors,errors
        print(name,'profile=',profile,'engines=',vals,'errors=',errors,flush=True)
        ctx.close()
    browser.close()
print('PASS: responsive editor, original six modules, preserved controls')
