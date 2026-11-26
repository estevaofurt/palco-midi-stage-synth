"""Run actual preview app and worklet on isolated localhost."""
import argparse,contextlib,http.server,threading,json
from pathlib import Path
from playwright.sync_api import sync_playwright
def main():
    p=argparse.ArgumentParser();p.add_argument('--site',type=Path,required=True);p.add_argument('--voices',type=int,choices=[128,192],default=128);p.add_argument('--engine',choices=['modal','physicalLegacy','physical','hybrid'],default='modal');a=p.parse_args()
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
            with page.expect_navigation():page.locator('#polyphony-limit').select_option(str(a.voices))
            page.wait_for_function('window.__palcoTest!==undefined')
            assert page.locator('#polyphony-limit').input_value()==str(a.voices)
            page.evaluate("""engine=>{const s=window.__palcoTest.state;s.mask=1;s.patches.piano.values.soundEngine=engine;s.patches.piano.values.physicalQuality='studio';s.patches.piano.values.mechanicalModel='on';}""",a.engine)
            page.locator('#power').click()
            node={'modal':'modal','physicalLegacy':'legacyPhysical','physical':'physical','hybrid':'hybrid'}[a.engine]
            page.wait_for_function('(node)=>Boolean(window.__palcoTest.getStage()?.instruments.piano[node])',arg=node,timeout=30000)
            result=page.evaluate("""async({requested,node})=>{
              const s=window.__palcoTest.getStage(),p=s.instruments.piano[node].port;
              const probe=()=>new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('probe timeout')),5000);
                const listen=e=>{if(e.data?.type==='polyphony-probe'){clearTimeout(timer);p.removeEventListener('message',listen);resolve(e.data)}};
                p.addEventListener('message',listen);p.postMessage({type:'polyphony-probe'});});
              const cap=s.activeVoiceLimit(1),initial=await probe();
              const n=Math.min(requested,cap);
              for(let i=0;i<n;i++)s.startNote('proof',0,36+i%36,.8,1);
              const actual=await probe(),stage=s.voiceStats();
              const data=new Float32Array(s.meter.fftSize);let signal=0;
              for(let i=0;i<12;i++){await new Promise(r=>setTimeout(r,20));s.meter.getFloatTimeDomainData(data);for(const v of data){if(!Number.isFinite(v))throw Error('nonfinite audio');signal=Math.max(signal,Math.abs(v));}}
              // Observe the live graph for 2 seconds, without claiming hardware deadlines.
              const wall=performance.now(),audio=s.ctx.currentTime;
              let polls=0,nonzero=0;
              for(let i=0;i<40;i++){await new Promise(r=>setTimeout(r,50));s.meter.getFloatTimeDomainData(data);
                let peak=0;for(const v of data){if(!Number.isFinite(v))throw Error('nonfinite audio');peak=Math.max(peak,Math.abs(v));}
                polls++;if(peak>1e-8)nonzero++;}
              const progress=(s.ctx.currentTime-audio)/((performance.now()-wall)/1000);
              const sustained=await probe();
              const layerLimit=s.activeVoiceLimit(3);
              s.startNote('proof',0,60,.8,1);
              const stolen=await probe();
              s.state.mask=3;s.startNote('proof',0,60,.8,3);
              const reduced=s.voiceStats();
              return {sampleRate:s.ctx.sampleRate,cap,initial,actual,stage,layerLimit,stolen,reduced,signal,n,polls,nonzero,progress,sustained};
            }""",dict(requested=a.voices,node=node))
            assert result['cap']==(a.voices if result['sampleRate']<=48000 else 64),result
            assert result['initial']['capacity']==result['cap'],result
            assert result['actual']['active']==result['n'],result
            assert result['stage']['active']==result['n'],result
            assert result['layerLimit']==64,result
            assert result['stolen']['active']==result['n'],result
            assert len(set(result['actual']['ids']))==result['n'],result
            assert result['reduced']['active']<=64,result
            assert result['signal']>1e-7,result
            assert result['sustained']['active']==result['n'],result
            assert result['polls']==40 and result['nonzero']>=36,result
            assert result['progress']>0.8,result
            assert not errors,errors
            print('G3_APP_POLYPHONY_PROBE '+json.dumps(dict(engine=a.engine,**result)),flush=True)
            browser.close()
        server.shutdown()
if __name__=='__main__':main()
