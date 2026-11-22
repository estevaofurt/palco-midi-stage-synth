from playwright.sync_api import sync_playwright
from pathlib import Path
ROOT='https://stage-synth.test/'
ROOT_DIR=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    for name,device in [('g04s',{'user_agent':'Mozilla/5.0 (Linux; Android 14; moto g04s) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36','viewport':{'width':390,'height':844},'is_mobile':True,'has_touch':True}),('desktop',{'viewport':{'width':1280,'height':800}})]:
        context=browser.new_context(**device)
        context.add_init_script('''(() => {
          window.nodeStats = {convolvers:0,oscillators:0,shapers:0};
          const a=window.AudioContext?.prototype;
          if(a){for(const [method,key] of [['createConvolver','convolvers'],['createOscillator','oscillators'],['createWaveShaper','shapers']]){
            const old=a[method];a[method]=function(...args){window.nodeStats[key]++;return old.apply(this,args)};
          }}
        })()''')
        page=context.new_page();errors=[];page.on('pageerror',lambda e: errors.append(str(e)))
        def route(request):
            path=request.request.url.split('://',1)[-1].split('/',1)[-1].split('?',1)[0]
            file=ROOT_DIR/(path or 'index.html')
            if file.is_file():
                request.fulfill(status=200,body=file.read_bytes(),content_type={'.js':'text/javascript','.html':'text/html','.css':'text/css'}.get(file.suffix,'application/octet-stream'),headers={'Access-Control-Allow-Origin':'*'})
            else:request.fulfill(status=404,body='not found')
        page.route('**/*',route)
        html=(ROOT_DIR/'index.html').read_text()
        page.set_content(html.replace('<head>','<head><base href="https://stage-synth.test/">'),wait_until='load')
        page.wait_for_function('window.__palcoTest !== undefined')
        page.locator('#power').click()
        page.wait_for_function('window.__palcoTest.getStage() !== undefined')
        page.locator('#keys .key').first.click()
        page.wait_for_timeout(250)
        d=page.evaluate('''()=>({
            mode:document.querySelector('#audio-profile').value,
            profile:window.__palcoTest.profile,
            model:window.__palcoTest.state.patches.piano.values.soundEngine,
            note:document.getElementById('profile-note').textContent,
            voices:window.__palcoTest.getStage()?.voiceStats(),
            convolvers:window.nodeStats.convolvers,
            createdFX:Object.values(window.__palcoTest.getStage().fx.nodes).filter(n=>n&&n.input).length,
            inserts:Object.values(window.__palcoTest.getStage().fx.inserts).filter(Boolean).length,
            dims:[document.documentElement.scrollWidth,window.innerWidth],
        })''')
        print(name,d,'errors',errors,flush=True)
        assert not errors,errors
        assert d['profile']==('lite' if name=='g04s' else 'full')
        assert d['model']==('classic' if name=='g04s' else 'modal')
        assert d['voices']['limit']==(8 if name=='g04s' else 32)
        assert d['convolvers']==(0 if name=='g04s' else 7)
        assert d['createdFX']==(0 if name=='g04s' else 6)
        assert d['dims'][0]<=d['dims'][1], d['dims']
        if name=='g04s':
            # Novo efeito pode ser ativado sob demanda no modo Leve.
            def enable_fx():
                page.evaluate('''()=>{
                    const test=window.__palcoTest,stage=test.getStage();
                    test.state.fx.slots.reverb1.active=true;
                    test.state.fx.slots.reverb1.targets=['piano'];
                    test.state.fx.enabled.piano=true;stage.updateEffects();
                }''')
            enable_fx()
            a=page.evaluate('''()=>({convolvers:window.nodeStats.convolvers,active:!!window.__palcoTest.getStage().fx.nodes.reverb1})''')
            print('FX sob demanda',a,flush=True)
            assert a['convolvers']==1 and a['active'],a
            notes=page.evaluate('''()=>{
              const stage=window.__palcoTest.getStage();
              for(let i=0;i<18;i++)stage.startNote('stress-test',0,48+i,96);
              return {stats:stage.voiceStats(),oscillators:window.nodeStats.oscillators};
            }''')
            print('Estresse mobile',notes,flush=True)
            assert notes['stats']['active']<=8, notes
        page.close();context.close()
    browser.close()
print('PASS: mobile + desktop + FX lazy')
