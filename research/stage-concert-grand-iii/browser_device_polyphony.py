import argparse,http.server,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--site',type=Path,required=True);a=p.parse_args()
handler=lambda *args,**kw:http.server.SimpleHTTPRequestHandler(*args,directory=str(a.site),**kw)
with http.server.ThreadingHTTPServer(('127.0.0.1',0),handler) as server:
    threading.Thread(target=server.serve_forever,daemon=True).start()
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
        page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}/device_polyphony.html')
        page.locator('#profile').select_option('lite')
        page.locator('#start').click()
        page.wait_for_function("!document.querySelector('#start').disabled",timeout=60000)
        assert page.locator('#rows tr').count()>=2
        status=page.locator('#status').inner_text()
        assert 'interrompido' not in status and 'Falha' not in status,status
        if page.locator('#apply').is_enabled():
            page.locator('#apply').click()
            assert page.evaluate("['32','64'].includes(localStorage.getItem('palco-stage-polyphony-v1'))")
        page.locator('#rate').select_option('96000')
        assert not page.locator('#apply').is_enabled()
        assert not errors,errors
        print('G3_DEVICE_POLYPHONY_UI_GATE true',flush=True)
        browser.close()
    server.shutdown()
