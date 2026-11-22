from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def route(r):
    path=r.request.url.split('://',1)[-1].split('/',1)[-1].split('?',1)[0]
    f=ROOT/(path or 'index.html')
    if f.is_file():
        typ={'.js':'text/javascript','.css':'text/css','.html':'text/html'}.get(f.suffix,'application/octet-stream')
        r.fulfill(status=200,body=f.read_bytes(),content_type=typ,headers={'Access-Control-Allow-Origin':'*'})
    else:r.fulfill(status=404,body='not found')
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    for width in (390,1024,1440):
        page=browser.new_page(viewport={'width':width,'height':940})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/*',route)
        html=(ROOT/'index.html').read_text().replace('<script src="./app.js" type="module"></script>','')
        page.set_content(html);page.add_style_tag(content=(ROOT/'panel.css').read_text());page.add_script_tag(url='https://stage-synth.test/app.js',type='module')
        page.wait_for_timeout(400)
        page.locator('#tab-effects').click()
        for id in ['reverb1','reverb2','delay1','delay2','mod1','mod2','eq']:
            card=page.locator(f'[data-effect="{id}"]')
            select=card.locator('.fx-type-panel select')
            assert select.count()==1 and select.is_visible(),id
            assert card.evaluate("card=>[...card.children].findIndex(x=>x.classList.contains('fx-type-panel')) < [...card.children].findIndex(x=>x.classList.contains('fx-routing'))")
            assert select.evaluate('x=>getComputedStyle(x).minHeight')!='0px'
        assert page.locator('[data-effect="comp"] .fx-type-panel').count()==0
        assert page.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth+2')
        if width==1440:
            page.locator('[data-effect="reverb1"] .fx-type-select').select_option('shimmer')
            assert page.locator('[data-effect="reverb1"] .fx-type-select').input_value()=='shimmer'
            page.locator('[data-effect="reverb1"]').screenshot(path='/mnt/data/Stage_Synth_v1_8_1_fx_tipos.png')
        assert not errors,errors
        print('PASS tipos FX',width)
        page.close()
    browser.close()
