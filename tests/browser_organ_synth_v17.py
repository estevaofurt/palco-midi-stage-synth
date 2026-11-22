from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

def route(r):
    path=r.request.url.split('://',1)[-1].split('/',1)[-1].split('?',1)[0]
    f=ROOT/(path or 'index.html')
    if f.is_file():
        typ={'.js':'text/javascript','.css':'text/css','.html':'text/html','.json':'application/json'}.get(f.suffix,'application/octet-stream')
        r.fulfill(status=200,body=f.read_bytes(),content_type=typ,headers={'Access-Control-Allow-Origin':'*'})
    else:r.fulfill(status=404,body='missing')

with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    page=browser.new_page(viewport={'width':1440,'height':900});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.route('**/*',route)
    html=(ROOT/'index.html').read_text().replace('<script src="./app.js" type="module"></script>','')
    page.set_content(html);page.add_style_tag(content=(ROOT/'panel.css').read_text())
    page.add_script_tag(url='https://stage-synth.test/app.js',type='module')
    page.wait_for_timeout(300)
    page.locator('#tab-organ').click()
    select=page.locator('#edit-organ select[aria-label="Tipo de órgão"]')
    assert select.count()==1
    print('ORGAN_OPTIONS:',select.locator('option').all_text_contents())
    results={}
    for choice in ['gospel','jazz','church','gospel']:
        select=page.locator('#edit-organ select[aria-label="Tipo de órgão"]')
        select.select_option(choice)
        d=page.evaluate('''()=>{const p=window.__palcoTest.state.patches.organ;return {preset:p.preset,registration:p.values.registration,bars:p.values.bars}}''')
        print('ORGAN_SELECTED',choice,d)
        assert d['registration']==choice,d
        assert d['preset'].startswith(choice),d
        results[choice]=d
    assert results['jazz']['bars']!=results['gospel']['bars']
    page.locator('#power').click();page.wait_for_timeout(250)
    readings=page.evaluate('''async()=>{
      const api=window.__palcoTest,stage=api.getStage(),state=api.state;
      if(!stage)throw Error('Áudio não inicializado');
      const wait=ms=>new Promise(r=>setTimeout(r,ms));
      const result={};
      // Mudança Jazz/Gospel com o órgão sustentado deve trocar registro no oscilador existente.
      const oid=stage.startNote('organ-v17',0,60,98,2);
      const organ=stage.instruments.organ,oldWave=organ.wave,oldRegistration=organ.registration;
      const jazz=state.patches.organ;
      // Atualização por preset específico evita dependência de UI no próprio teste de áudio.
      jazz.values.bars=[8,8,8,0,0,0,0,0,0];jazz.values.registration='jazz';
      stage.update('organ','registration');
      result.organ={changed:organ.registration!==oldRegistration,newRegistration:organ.registration,liveOscillators:organ.live.size};
      if(!result.organ.changed)throw Error('Organ registration has not changed on held voice');
      stage.releaseId(oid);
      const p=state.patches.synth.values;
      p.voiceMode='poly';p.glide=.65;p.unison='1';p.matrixSource='velocity';p.matrixDest='pitch';p.matrixAmount=0;
      stage.update('synth');
      const freq0=261.6255653,freq1=523.25113;
      const prior=stage.startNote('glide-v17',0,60,110,4);
      if(!prior)throw Error('synth note 1 failure');
      const group=stage.voices.get(prior).group;
      const log=[];
      const original=AudioParam.prototype.exponentialRampToValueAtTime;
      AudioParam.prototype.exponentialRampToValueAtTime=function(target,time){log.push({target,time,now:stage.ctx.currentTime});return original.call(this,target,time)};
      const second=stage.startNote('glide-v17',0,72,110,4);
      AudioParam.prototype.exponentialRampToValueAtTime=original;
      if(!second)throw Error('synth note 2 failure');
      result.glide={events:log.filter(e=>Math.abs(e.target-freq1)<2),expected:p.glide,source:stage.instruments.synth.previousHz.get(group)};
      if(!result.glide.events.some(e=>e.time-e.now>.5))throw Error('Portamento em poly não agendou rampa de frequência');
      const part=stage.voices.get(second).parts.get('synth');
      const countOsc=()=>[...part.sources.keys()].filter(x=>x instanceof OscillatorNode).length;
      result.unison={before:countOsc()};
      p.unison='3';stage.update('synth','unison');await wait(90);
      result.unison.after=countOsc();
      if(result.unison.before!==3||result.unison.after!==7)throw Error('Unison change has not added oscillators to held note');
      p.matrixAmount=90;stage.update('synth','matrixAmount');await wait(80);
      result.matrix={gain:part.nodes.filter(x=>x.gain).map(x=>x.gain.value).filter(x=>x>30)};
      if(!result.matrix.gain.length)throw Error('Velocity matrix does not affect held note');
      p.matrixSource='aftertouch';stage.update('synth','matrixSource');
      p.matrixSource='velocity';stage.update('synth','matrixSource');
      p.unison='1';stage.update('synth','unison');await wait(70);
      result.unison.muted=part.nodes.filter(x=>x.gain).map(x=>x.gain.value).filter(x=>Math.abs(x)<.001).length;
      if(result.unison.muted<4)throw Error('Unison oscillators not muted on decrease');
      p.glide=.9;stage.update('synth','glide');
      result.glide.reconfigured=p.glide;
      stage.panic();await wait(180);
      result.activeAfterPanic=stage.voiceStats().active;
      if(result.activeAfterPanic)throw Error('panic left voices');
      return result;
    }''')
    print('BROWSER_LIVE_RESULT:',readings)
    print('PAGE_ERRORS:',errors)
    assert not errors,errors
    page.locator('#tab-organ').click()
    page.screenshot(path=str(ROOT/'Stage_Synth_v1_7_0_preview.png'),full_page=True)
    page.close();browser.close()
