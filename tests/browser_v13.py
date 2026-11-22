from pathlib import Path
from playwright.sync_api import sync_playwright
import json, time
ROOT=Path(__file__).resolve().parents[1]
ORIGIN='https://stage-synth.test/'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    page=browser.new_page(viewport={'width':1365,'height':950})
    errors=[];miss=[];console=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('console',lambda m:console.append(m.text) if m.type=='error' else None)
    def serve(route):
        name=route.request.url.split('://',1)[-1].split('/',1)[-1].split('?',1)[0].split('#',1)[0]
        file=ROOT/(name or 'index.html')
        if file.is_file():
            mime={'.js':'text/javascript','.css':'text/css','.html':'text/html','.json':'application/json'}.get(file.suffix,'application/octet-stream')
            route.fulfill(status=200,content_type=mime,body=file.read_bytes(),headers={'Access-Control-Allow-Origin':'*'})
        else:
            miss.append(name);route.fulfill(status=404,body='not found',headers={'Access-Control-Allow-Origin':'*'})
    page.route('**/*',serve)
    html=(ROOT/'index.html').read_text().replace('<script src="./app.js" type="module"></script>','')
    page.set_content(html);page.add_style_tag(content=(ROOT/'panel.css').read_text());page.add_script_tag(url=ORIGIN+'app.js',type='module')
    page.wait_for_timeout(400)
    init=page.evaluate('''() => ({modules:document.querySelectorAll('.module').length,
      editors:document.querySelectorAll('.editor').length,
      fxSlots:document.querySelectorAll('.fx-slot').length,
      scenes:document.querySelectorAll('#scene option').length,
      keys:document.querySelectorAll('#keys .key').length,
      duplicates:[...document.querySelectorAll('[id]')].map(e=>e.id).filter((id,i,ids)=>ids.indexOf(id)!==i)})''')
    print('INIT',init,'ERR',errors)
    assert init['modules']==6,init
    assert init['editors']==6,init
    assert init['fxSlots']==8,init
    assert init['scenes']>=9,init
    assert not init['duplicates'],init
    assert not errors,errors
    page.locator('#power').click();page.wait_for_timeout(550)
    print('POWER',page.locator('#power').inner_text(),'STATUS',page.locator('#status').inner_text())
    assert 'Áudio ativo' in page.locator('#power').inner_text(),errors
    for tab in ['piano','electric','organ','synth','sf','effects']:
        page.locator('#tab-'+tab).click(); assert page.locator('#edit-'+tab).is_visible(),tab
    page.locator('#tab-piano').click();
    for preset in ['japanese','american','felt','upright']:
        page.locator('#edit-piano .tone-field select').select_option(preset)
        assert page.locator('#edit-piano .tone-field select').input_value()==preset
    page.locator('#tab-electric').click();
    for preset in ['mark1','mark2','wurly200','wurly140','cp80','clav','fmfull','fmdino','fmballad']:
        page.locator('#edit-electric .tone-field select').select_option(preset)
    page.locator('#tab-organ').click();page.locator('#edit-organ .tone-field select').select_option('church')
    page.locator('#tab-synth').click();page.locator('#edit-synth .tone-field select').select_option('pulse')
    page.locator('#scene').select_option('synth')
    page.locator('#tab-effects').click()
    page.locator('[data-effect="reverb1"] input[type="checkbox"]').check()
    page.locator('[data-effect="reverb1"] select').select_option('synth')
    page.locator('#tab-synth').click();page.locator('#tab-synth').scroll_into_view_if_needed()
    page.locator('#modules .module').filter(has=page.locator('#tab-synth')).locator('.fx-toggle').click()
    audio=page.evaluate('''async () => {const {state,getStage,performer}=window.__palcoTest;
     let output=[];let st=getStage();
     for (const [id,bit] of [['piano',1],['electric',8],['organ',2],['synth',4],['sf',16]]) {
       state.mask=bit;
       const voice=st.startNote('automated',0,60,105);
       output.push({name:id,voice,parts:st.voices.get(voice)?.parts.size||0});
       st.releaseId(voice);
     }
     state.mask=4;
     const before=st.voiceStats();
     st.panic();await new Promise(r=>setTimeout(r,250));
     return {output,before,after:st.voiceStats(),fxActive:state.fx.slots.reverb1.active,fxEnabled:state.fx.enabled.synth};
    }''')
    print('AUDIO',audio,'CONSOLE',console,'ERRORS',errors)
    assert all(x['voice'] and x['parts']>=1 for x in audio['output']),audio
    assert audio['fxActive'] and audio['fxEnabled'],audio
    assert audio['after']['active']==0,audio
    page.locator('#arp-toggle').click()
    assert page.locator('#arp-toggle').get_attribute('aria-pressed')=='true'
    page.locator('#chord-mode').select_option('minor')
    page.locator('#bpm').fill('150');page.locator('#bpm').press('Tab')
    page.locator('#arp-rate').select_option('1/16')
    page.locator('#arp-toggle').click()
    page.locator('#scene').select_option('piano')
    keyboard=page.locator('#keys .key').first
    keyboard.scroll_into_view_if_needed();keyboard.click(force=True)
    page.wait_for_timeout(150)
    print('BUTTON',page.locator('#voice-status').inner_text(),errors)
    # Test native input pathway used by MIDI and touch with chord mode enabled.
    notes=page.evaluate('''() => {const t=window.__palcoTest;const p=t.performer;
      const id=p.noteOn('sim-midi',0,62,106);
      const active=[...t.getStage().voices.values()].filter(v=>v.held&&v.group.source==='sim-midi').map(v=>v.key).sort((a,b)=>a-b);
      p.noteOffId(id);return active;}''')
    assert notes==[62,65,69],notes
    page.locator('#chord-mode').select_option('off')
    # Record a short loop through exported performance API without waiting for bars.
    loop=page.evaluate('''() => {const p=window.__palcoTest.performer;p.startRecording();
      const id=p.noteOn('sim',0,60,95);p.noteOffId(id);p.stopRecording();
      const count=p.events.length,playing=p.loopPlaying;p.stopLoop();return {count,playing};}''')
    assert loop['count']>=2 and loop['playing'],loop
    page.locator('#tab-sf').click()
    page.locator('#edit-sf input[type=file]').set_input_files(str(ROOT/'tests/fixture_minimal.sf2'))
    page.wait_for_timeout(380)
    sf2=page.evaluate('''() => {const t=window.__palcoTest,st=t.getStage();
      return {programs:st.instruments.sf.reader?.programs?.length||0,
        selected:st.instruments.sf.program,mask:t.state.mask,
        status:document.getElementById('status').textContent};}''')
    print('SF2',sf2)
    assert sf2['programs']==1 and sf2['mask']&16,sf2
    assert page.locator('#sf-program option').count()==1
    sfNote=page.evaluate('''async () => {const t=window.__palcoTest,st=t.getStage();
      const id=st.startNote('sf2-test',0,60,110,16);
      const active=st.voices.get(id)?.parts.size||0;
      st.releaseId(id);await new Promise(r=>setTimeout(r,100));return {id,active};}''')
    print('SF2_NOTE',sfNote)
    assert sfNote['active']>0,sfNote
    assert not errors,errors
    page.screenshot(path=str(ROOT.parent/'Stage_Synth_v1_3_0_preview.png'),full_page=True)
    print('RESULT',json.dumps({'dom':init,'audio':audio,'notes':notes,'loop':loop,'errors':errors,'console':console,'missing':miss},ensure_ascii=False))
    # Check mobile in same origin with fresh storage.
    mob=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
    mob.route('**/*',serve);mobile_errors=[];mob.on('pageerror',lambda e:mobile_errors.append(str(e)))
    mob.set_content(html);mob.add_style_tag(content=(ROOT/'panel.css').read_text());mob.add_script_tag(url=ORIGIN+'app.js',type='module');mob.locator('#tab-organ').click()
    widths=mob.evaluate('''() => ({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth,modules:document.querySelectorAll('.module').length})''')
    mob.screenshot(path=str(ROOT.parent/'Stage_Synth_v1_3_0_mobile.png'),full_page=True)
    print('MOBILE',widths,mobile_errors)
    assert widths['scroll']<=widths['client']+1,widths
    assert not mobile_errors,mobile_errors
    browser.close()
