from pathlib import Path
from playwright.sync_api import sync_playwright
import wave, math, struct, json
ROOT=Path(__file__).resolve().parents[1]
ORIGIN='https://stage-synth.test/'
WAV=ROOT/'tests/C4_v100.wav'
with wave.open(str(WAV),'wb') as f:
    f.setnchannels(1);f.setsampwidth(2);f.setframerate(22050)
    f.writeframes(b''.join(struct.pack('<h', int(6500*math.sin(2*math.pi*261.6256*i/22050)*math.exp(-i/22050))) for i in range(16538)))

def serve(route):
    name=route.request.url.split('://',1)[-1].split('/',1)[-1].split('?',1)[0].split('#',1)[0]
    file=ROOT/(name or 'index.html')
    if file.is_file():
        mime={'.js':'text/javascript','.css':'text/css','.html':'text/html','.json':'application/json','.wav':'audio/wav'}.get(file.suffix,'application/octet-stream')
        route.fulfill(status=200,content_type=mime,body=file.read_bytes(),headers={'Access-Control-Allow-Origin':'*'})
    else:route.fulfill(status=404,body='not found',headers={'Access-Control-Allow-Origin':'*'})

html=(ROOT/'index.html').read_text().replace('<script src="./app.js" type="module"></script>','')
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    results=[]
    for width in [390,640,900,1180,1365,1600]:
        page=browser.new_page(viewport={'width':width,'height':900})
        errors=[];page.on('pageerror',lambda e,errors=errors:errors.append(str(e)))
        page.route('**/*',serve)
        page.set_content(html);page.add_style_tag(content=(ROOT/'panel.css').read_text());page.add_script_tag(url=ORIGIN+'app.js',type='module')
        page.wait_for_timeout(180)
        assert page.locator('.module').count()==6
        for tab in ['piano','electric','organ','synth','sf','effects']:
            page.locator('#tab-'+tab).click()
            assert page.locator('#edit-'+tab).is_visible()
            if tab in ['piano','electric','synth']:
                geometry=page.evaluate('''id=>{
                  const pane=document.querySelector('#edit-'+id);
                  const boxes=[...pane.querySelectorAll('.dial')].map(d=>({name:d.querySelector('.dial-name')?.textContent,
                    r:d.getBoundingClientRect(),w:d.querySelector('.dial-wheel').getBoundingClientRect(),
                    n:d.querySelector('.dial-name').getBoundingClientRect()}));
                  const intersections=[];
                  for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){
                    let a=boxes[i].w,b=boxes[j].w;
                    if(Math.min(a.right,b.right)-Math.max(a.left,b.left)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1)
                      intersections.push(boxes[i].name+' x '+boxes[j].name);
                    a=boxes[i].n;b=boxes[j].n;
                    if(Math.min(a.right,b.right)-Math.max(a.left,b.left)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1)
                      intersections.push('label '+boxes[i].name+' x '+boxes[j].name);
                  }
                  return {total:boxes.length,intersections,clipped:boxes.filter(v=>v.w.right>innerWidth+2||v.w.left<0).map(v=>v.name)};
                }''',tab)
                assert geometry['total']>5,(width,tab,geometry)
                assert not geometry['intersections'],(width,tab,geometry)
                assert not geometry['clipped'],(width,tab,geometry)
        no_overflow=page.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth+2')
        assert no_overflow,('horizontal overflow',width,page.evaluate('document.documentElement.scrollWidth'))
        assert not errors,(width,errors)
        results.append({'width':width,'knobs':'sem sobreposição','horizontal':'ok'})
        if width==1365:
            page.locator('#tab-electric').click()
            assert page.locator('#edit-electric .tone-field .tone-label').inner_text().strip().casefold()=='preset'
            assert page.locator('#edit-electric select[aria-label="Instrumento"]').input_value()=='mark1'
            assert page.locator('#edit-electric .dial [aria-label="Auto-Pan"]').count()==1
            assert page.locator('#edit-electric .dial [aria-label="Pan"]').count()==0
            page.locator('#edit-electric .tone-field select').select_option('mark1-bright')
            assert page.locator('#edit-electric select[aria-label="Instrumento"]').input_value()=='mark1'
            page.locator('#edit-electric select[aria-label="Instrumento"]').select_option('fmballad')
            assert page.locator('#edit-electric .tone-field select').input_value()=='fmballad'
            assert page.locator('#edit-electric .tone-field select option').count()==3
            page.locator('#power').click();page.wait_for_timeout(150)
            assert 'Áudio ativo' in page.locator('#power').inner_text(),errors
            # Check the new stereo modulation route is actually connected.
            auto=page.evaluate('''() => {let e=window.__palcoTest.getStage().instruments.electric;
              return {connected:Boolean(e.autoPanOsc&&e.autoPanDepth),freq:e.autoPanOsc.frequency.value,
                level:e.autoPanDepth.gain.value};}''')
            assert auto['connected'],auto
            page.locator('#edit-electric select[aria-label="Instrumento"]').select_option('mark1')
            page.locator('#edit-electric input[aria-label="Auto-Pan"]').evaluate('(el)=>{el.value="850";el.dispatchEvent(new Event("input",{bubbles:true}))}')
            page.wait_for_timeout(120)
            depth=page.evaluate('window.__palcoTest.getStage().instruments.electric.autoPanDepth.gain.value')
            assert depth>0.1,depth
            # Upload a real WAV sample to the acoustic instrument, then play a note.
            page.locator('#tab-piano').click()
            page.locator('#edit-piano .sample-upload input[type=file]').set_input_files(str(WAV))
            page.wait_for_timeout(300)
            count=page.evaluate('window.__palcoTest.getStage().instruments.piano.samples.count("japanese")')
            assert count==1,(count,errors,page.locator('#status').inner_text())
            audio=page.evaluate('''async()=>{let stage=window.__palcoTest.getStage();
              const id=stage.startNote('browser',0,60,100,1);
              const count=stage.voices.get(id)?.parts.size||0;
              stage.releaseId(id);stage.panic();await new Promise(r=>setTimeout(r,180));
              return {count,active:stage.voices.size}}
            ''')
            assert audio['count']==1 and audio['active']==0,(audio,errors)
            page.locator('#edit-piano .sample-upload button').click()
            assert page.evaluate('window.__palcoTest.getStage().instruments.piano.samples.count("japanese")')==0
            # Electrical WAV bank is independent from the acoustic piano.
            page.locator('#tab-electric').click()
            page.locator('#edit-electric .sample-upload input[type=file]').set_input_files(str(WAV))
            page.wait_for_timeout(170)
            assert page.evaluate('window.__palcoTest.getStage().instruments.electric.samples.count("mark1")')==1
            ep=page.evaluate('''() => {const st=window.__palcoTest.getStage();
              const id=st.startNote('wav-test',0,60,100,8);
              const parts=st.voices.get(id)?.parts.size||0;st.releaseId(id);
              return parts}''')
            assert ep==1,ep
            page.locator('#edit-electric .sample-upload button').click()
            assert page.evaluate('window.__palcoTest.getStage().instruments.electric.samples.count("mark1")')==0
            # Confirm the original SF2 reader, effect rack and performance mode still operate.
            page.locator('#tab-sf').click()
            page.locator('#edit-sf input[type=file]').set_input_files(str(ROOT/'tests/fixture_minimal.sf2'))
            page.wait_for_timeout(230)
            assert page.evaluate('window.__palcoTest.getStage().instruments.sf.reader?.programs.length')==1
            page.locator('#tab-effects').click()
            page.locator('[data-effect="delay1"] input[type="checkbox"]').check()
            page.locator('[data-effect="delay1"] select').select_option('electric')
            assert page.evaluate('window.__palcoTest.state.fx.slots.delay1.target')=='electric'
            page.locator('#chord-mode').select_option('major')
            chord=page.evaluate('''() => {const t=window.__palcoTest,p=t.performer,st=t.getStage();
              const id=p.noteOn('chord-test',0,60,100);
              const keys=[...st.voices.values()].filter(v=>v.group.source==='chord-test'&&v.held).map(v=>v.key).sort();
              p.noteOffId(id);return keys;}''')
            assert chord==[60,64,67],chord
            page.locator('#chord-mode').select_option('off')
            page.locator('#tab-piano').click()
            page.screenshot(path=str(ROOT.parent/'Stage_Synth_v1_4_0_preview.png'),full_page=True)
        page.close()
    print('RESPONSIVE',json.dumps(results,ensure_ascii=False))
    browser.close()
WAV.unlink(missing_ok=True)
print('BROWSER V1.4 PASSOU')
