from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def route(r):
 path=r.request.url.split('://',1)[-1].split('/',1)[-1].split('?',1)[0]
 f=ROOT/(path or 'index.html')
 if f.is_file():r.fulfill(status=200,body=f.read_bytes(),content_type={'.js':'text/javascript','.html':'text/html','.css':'text/css'}.get(f.suffix,'application/octet-stream'),headers={'Access-Control-Allow-Origin':'*'})
 else:r.fulfill(status=404,body='not found')
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
 page=browser.new_page();page.route('**/*',route)
 page.set_content('<!doctype html><html><body>Stage test</body></html>')
 page.add_script_tag(url='https://stage-synth.test/stage.js',type='module')
 data=page.evaluate('''async()=>{
  const {loadState,engines}=await import('https://stage-synth.test/patches.js');
  const {Stage}=await import('https://stage-synth.test/stage.js');
  const {Part}=await import('https://stage-synth.test/voice.js');
  const results={};
  async function render({instrument='piano',keys=[48,52,55,60],fx=false,max=false,all=false}){
    const hz=44100,ctx=new OfflineAudioContext(2,hz*2,hz),state=loadState(null);
    for(const name of Object.keys(engines))state.patches[name].level=max?100:75;
    for(const name of Object.keys(engines))state.fx.enabled[name]=fx;
    const targets=Object.keys(engines);
    if(fx)for(const [name,slot] of Object.entries(state.fx.slots)){
      slot.active=true;slot.targets=targets;slot.mix= name==='eq'||name==='comp'?100:65;
      if(name.startsWith('reverb'))slot.time=3.1;
      if(name.startsWith('delay'))slot.feedback=65;
      if(name==='comp'){slot.makeup=14;slot.threshold=-10;}
      if(name==='eq'){slot.low=6;slot.mid=6;slot.high=8;}
    }
    const stage=new Stage(ctx,state),g=stage.group('t',0);
    for(const key of keys){
      for(const name of (all?targets:[instrument])){
        const part=new Part(ctx,stage.instruments[name].input,g,()=>{});
        stage.instruments[name].play(part,key,116,state.patches[name].values,g,false);
      }
    }
    const start=performance.now();const audio=await ctx.startRendering();
    let peak=0,abs=0,clip=0,nonfinite=0,sum=0,count=0;
    for(let c=0;c<2;c++){
      const a=audio.getChannelData(c);
      for(let i=4410;i<a.length;i++){
        const x=a[i],ax=Math.abs(x);peak=Math.max(peak,ax);if(ax>1)clip++;if(!Number.isFinite(x))nonfinite++;
        sum+=x*x;count++;
      }
    }
    return {peak,clipFraction:clip/count,rms:Math.sqrt(sum/count),nonfinite,duration:Math.round(performance.now()-start)};
  }
  for(const [id,options] of Object.entries({piano:{},synth:{instrument:'synth'},piano8:{keys:[48,52,55,60,64,67,72,76]},fx:{fx:true},all:{all:true},allFx:{fx:true,all:true}})){
    try{results[id]=await render(options);}catch(e){results[id]={error:String(e),stack:e.stack}};
  }
  return results;
}''')
 print(data,flush=True)
 for scenario, metric in data.items():
  assert 'error' not in metric, (scenario, metric)
  assert metric['nonfinite'] == 0, (scenario, metric)
  assert metric['clipFraction'] == 0 and metric['peak'] < 0.95, (scenario, metric)
 print('PASS: 6 renderizações sem clipping digital nem NaN',flush=True)
 browser.close()
