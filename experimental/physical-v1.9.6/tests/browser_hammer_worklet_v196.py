"""Real Chrome AudioWorklet load on localhost: tests both 32 and 64 voices.
This uses Chromium headless, not actual Moto g04s hardware."""
from pathlib import Path
import subprocess, time, socket
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
PORT=8796
server=subprocess.Popen(['python','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    time.sleep(.4)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required','--use-fake-ui-for-media-stream'])
        for profile,notes,mobile in [('lite',32,True),('full',64,False)]:
            context=browser.new_context(viewport={'width':390 if mobile else 1365,'height':850},is_mobile=mobile,has_touch=mobile,user_agent=('Mozilla/5.0 (Linux; Android 14; moto g04s) AppleWebKit/537.36 Chrome/131 Mobile Safari/537.36' if mobile else None))
            page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{PORT}/index.html',wait_until='networkidle')
            page.locator('#audio-profile').select_option(profile)
            page.locator('#power').click()
            page.wait_for_function('window.__palcoTest?.getStage()?.instruments?.piano?.physical',timeout=30000)
            result=page.evaluate('''(notes)=>{
              const stage=window.__palcoTest.getStage(),p=stage.instruments.piano;
              const ids=[];
              for(let i=0;i<notes;i++)ids.push(stage.startNote('hammer-test',0,24+(i%84),85,1));
              return {audio:stage.ctx.state,quality:p.physicalQuality,
                active:stage.voiceStats(),hasWorklet:!!p.physical,ids:ids.length,
                errors:[]};
            }''',notes)
            page.wait_for_timeout(900)
            result['errors']=errors
            print(profile,result)
            assert result['audio']=='running' and result['hasWorklet'] and not errors,result
            assert result['ids']==notes,result
            context.close()
        browser.close()
finally:
    server.terminate();server.wait(timeout=4)
