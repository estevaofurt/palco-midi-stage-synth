from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def route(r):
    path=r.request.url.split('://',1)[-1].split('/',1)[-1].split('?',1)[0]
    f=ROOT/(path or 'index.html')
    if f.is_file():
        typ={'.js':'text/javascript','.css':'text/css','.html':'text/html','.json':'application/json'}.get(f.suffix,'application/octet-stream')
        r.fulfill(status=200,body=f.read_bytes(),content_type=typ,headers={'Access-Control-Allow-Origin':'*'})
    else:r.fulfill(status=404,body='not found')
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    for width in (390,1024,1440):
        page=browser.new_page(viewport={'width':width,'height':940})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/*',route)
        html=(ROOT/'index.html').read_text().replace('<script src="./app.js" type="module"></script>','')
        page.set_content(html);page.add_style_tag(content=(ROOT/'panel.css').read_text());page.add_script_tag(url='https://stage-synth.test/app.js',type='module')
        page.wait_for_timeout(300)
        page.locator('#tab-effects').click()
        assert page.locator('.fx-slot').count()==8
        choices={'reverb1':['Hall','Room','Plate','Spring','Church','Shimmer'],
                 'delay1':['Tape','Analog','Digital'],
                 'mod1':['Chorus','Flanger','Phaser','Wah-Wah'],
                 'eq':['Paramétrico','Gráfico · 7 bandas']}
        for kind,options in choices.items():
            sel=page.locator(f'[data-effect="{kind}"] .fx-type-select')
            assert sel.locator('option').all_text_contents()==options,(kind,sel.locator('option').all_text_contents())
            for option in sel.locator('option').all():
                sel.select_option(option.get_attribute('value'))
        page.locator('[data-effect="eq"] .fx-type-select').select_option('graphic')
        assert page.locator('[data-effect="eq"] input[aria-label="500 Hz Equalizador"]').count()==1
        page.locator('[data-effect="comp"] input[aria-label="Makeup Gain (dB) Compressor"]').count()==1
        assert page.locator('[data-effect="comp"] input[aria-label="Attack (s) Compressor"]').count()==1
        assert page.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth+2')
        page.locator('#power').click();page.wait_for_timeout(450)
        result=page.evaluate('''() => {
          const s=window.__palcoTest.getStage();if(!s)return {error:'no stage'};
          const state=window.__palcoTest.state;
          state.fx.enabled.piano=true;state.fx.slots.comp.active=true;state.fx.slots.comp.targets=['piano'];
          state.fx.slots.comp.makeup=6;state.fx.slots.comp.mix=100;state.fx.slots.comp.attack=.02;
          state.fx.slots.eq.active=true;state.fx.slots.eq.targets=['piano'];state.fx.slots.eq.eqType='graphic';
          state.fx.slots.eq.eq500=-9;
          state.fx.slots.mod1.active=true;state.fx.slots.mod1.targets=['piano','organ'];state.fx.slots.mod1.modType='wah';
          state.fx.slots.reverb1.active=true;state.fx.slots.reverb1.targets=['piano'];state.fx.slots.reverb1.reverbType='shimmer';
          state.fx.slots.delay1.active=true;state.fx.slots.delay1.targets=['piano'];state.fx.slots.delay1.delayType='tape';
          s.updateEffects();
          const a=s.fx.inserts.piano;
          const before={wet:a.compWet.gain.value,makeup:a.makeup.gain.value};
          state.fx.enabled.piano=false;s.updateEffects();
          return {insert:Object.keys(s.fx.inserts).length,modGain:s.fx.nodes.mod1.wahGain.gain.value,compThreshold:a.comp.threshold.value,eqFilters:a.graphic.length,hasReduction:Number.isFinite(s.fx.reduction('piano')),status:document.querySelector('#power').innerText,before};
        }''')
        assert 'Áudio ativo' in result['status'],result
        assert result['insert']==5 and result['eqFilters']==7,result
        assert result['hasReduction'],result
        assert not errors,(width,errors)
        print('PASS browser',width,result)
        page.close()
    browser.close()
