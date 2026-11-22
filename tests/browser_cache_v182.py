from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def route(r):
    path=r.request.url.split('://',1)[-1].split('/',1)[-1].split('?',1)[0]
    f=ROOT/(path or 'index.html')
    if f.is_file():
        typ={'.js':'text/javascript','.css':'text/css','.html':'text/html'}.get(f.suffix,'application/octet-stream')
        r.fulfill(status=200,body=f.read_bytes(),content_type=typ,headers={'Access-Control-Allow-Origin':'*'})
    else:
        r.fulfill(status=404,body='not found')
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    for entry in ('index.html','v1.8.3.html'):
        page=browser.new_page(viewport={'width':1366,'height':900})
        errors=[]
        req=[]
        page.on('pageerror',lambda e: errors.append(str(e)))
        page.on('request',lambda q: req.append(q.url))
        page.route('**/*',route)
        html=(ROOT/entry).read_text(encoding='utf-8').replace('<script src="./app.js?build=1.8.3" type="module"></script>','')
        html=html.replace('<head>','<head><base href="https://test-stage.example/">')
        page.set_content(html)
        page.add_style_tag(content=(ROOT/'panel.css').read_text())
        page.add_script_tag(url='https://test-stage.example/app.js?build=1.8.3',type='module')
        page.wait_for_timeout(650)
        assert page.title()=='Stage Synth · Palco MIDI v1.8.3',page.title()
        assert page.locator('.build-tag').inner_text()=='v1.8.3'
        assert page.locator('#modules .module').count()==6,page.locator('#modules .module').count()
        page.locator('#tab-effects').click()
        assert page.locator('.fx-type-select').count()==7
        assert any('app.js?build=1.8.3' in q for q in req),req
        assert any('panel.js?build=1.8.3' in q for q in req),req
        assert any('panel.css?build=1.8.3' in q for q in req),req
        assert not errors,errors
        print(f'PASS {entry}: 6 módulos, 7 tipos FX, recursos com versão e zero erros JS')
        page.close()
    browser.close()
