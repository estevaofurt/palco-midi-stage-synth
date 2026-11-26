"""Run actual preview app and worklet on isolated localhost."""
import argparse,contextlib,http.server,threading,json
from pathlib import Path
from playwright.sync_api import sync_playwright
def main():
    p=argparse.ArgumentParser();p.add_argument('--site',type=Path,required=True);a=p.parse_args()
    handler=lambda *args,**kw:http.server.SimpleHTTPRequestHandler(*args,directory=str(a.site),**kw)
    with http.server.ThreadingHTTPServer(('127.0.0.1',0),handler) as server:
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        url=f'http://127.0.0.1:{server.server_port}/'
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
            context=browser.new_context(viewport={'width':1280,'height':800})
            page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(url);page.wait_for_function('window.__palcoTest!==undefined')
            page.evaluate("localStorage.setItem('palco-stage-audio-profile-v1','full')")
            page.reload();page.wait_for_function('window.__palcoTest!==undefined')
            with page.expect_navigation():page.locator('#polyphony-limit').select_option('128')
            page.wait_for_function('window.__palcoTest!==undefined')
            assert page.locator('#polyphony-limit').input_value()=='128'
            page.evaluate("""()=>{const s=window.__palcoTest.state;s.mask=1;s.patches.piano.values.soundEngine='modal';}""")
            page.locator('#power').click()
            page.wait_for_function("window.__palcoTest.getStage()?.instruments.piano.modal",timeout=30000)
            result=page.evaluate("""async()=>{
              const s=window.__palcoTest.getStage(),p=s.instruments.piano.modal.port;
              const probe=()=>new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('probe timeout')),5000);
                const listen=e=>{if(e.data?.type==='polyphony-probe'){clearTimeout(timer);p.removeEventListener('message',listen);resolve(e.data)}};
                p.addEventListener('message',listen);p.postMessage({type:'polyphony-probe'});});
              const cap=s.activeVoiceLimit(1),initial=await probe();
              const n=Math.min(128,cap);
              for(let i=0;i<n;i++)s.startNote('proof',0,36+i%36,.8,1);
              const actual=await probe(),stage=s.voiceStats();
              const layerLimit=s.activeVoiceLimit(3);
              s.startNote('proof',0,60,.8,1);
              const stolen=await probe();
              return {sampleRate:s.ctx.sampleRate,cap,initial,actual,stage,layerLimit,stolen,n};
            }""")
            assert result['cap']==(128 if result['sampleRate']<=48000 else 64),result
            assert result['initial']['capacity']==result['cap'],result
            assert result['actual']['active']==result['n'],result
            assert result['stage']['active']==result['n'],result
            assert result['layerLimit']==64,result
            assert result['stolen']['active']==result['n'],result
            assert not errors,errors
            print('G3_APP_POLYPHONY_PROBE '+json.dumps(result),flush=True)
            browser.close()
        server.shutdown()
if __name__=='__main__':main()
