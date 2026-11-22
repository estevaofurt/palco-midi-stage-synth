from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def route(r):
 path=r.request.url.split('://',1)[-1].split('/',1)[-1].split('?',1)[0]
 f=ROOT/(path or 'index.html')
 if f.is_file():r.fulfill(status=200,body=f.read_bytes(),content_type={'.js':'text/javascript','.html':'text/html','.css':'text/css'}.get(f.suffix,'application/octet-stream'),headers={'Access-Control-Allow-Origin':'*'})
 else:r.fulfill(status=404,body='not found')
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page();page.route('**/*',route)
 page.set_content('<!doctype html><html><body>FX audio test</body></html>')
 page.add_script_tag(url='https://stage-synth.test/fx-rack.js',type='module')
 result=page.evaluate('''async()=>{
  const {FXRack,impulse}=await import('https://stage-synth.test/fx-rack.js');
  const {loadState,engines}=await import('https://stage-synth.test/patches.js');
  const hz=48000;
  async function render(compress=false,eq=false){
    const ctx=new OfflineAudioContext(1,hz*2,hz);
    const state=loadState(null);state.fx.enabled.piano=true;
    state.fx.slots.comp.active=compress;state.fx.slots.comp.targets=['piano'];
    Object.assign(state.fx.slots.comp,{mix:100,threshold:-35,ratio:12,attack:.005,release:.15,makeup:0,knee:0});
    state.fx.slots.eq.active=eq;state.fx.slots.eq.targets=['piano'];
    Object.assign(state.fx.slots.eq,{mix:100,eqType:'graphic',eq1000:-15});
    const master=ctx.createGain();master.connect(ctx.destination);
    const buses={};for(const name of Object.keys(engines)){const g=ctx.createGain();g.connect(master);buses[name]=g}
    const fx=new FXRack(ctx,master,state,buses);
    const src=ctx.createOscillator(),amp=ctx.createGain();src.frequency.value=1000;amp.gain.value=.65;
    src.connect(amp).connect(buses.piano);src.start();src.stop(1.6);
    const buf=await ctx.startRendering(),a=buf.getChannelData(0);
    let sum=0,peak=0,count=0;
    for(let i=hz*.4;i<hz*1.4;i++){sum+=a[i]*a[i];peak=Math.max(peak,Math.abs(a[i]));count++}
    return {rms:Math.sqrt(sum/count),peak,finite:Number.isFinite(sum),gainAt1k:fx.inserts.piano.graphic[3].gain.value};
  }
  const dry=await render(false,false),comp=await render(true,false),eq=await render(false,true);
  const sample=new OfflineAudioContext(1,128,hz),ir={};
  for(const k of ['hall','room','plate','spring','church','shimmer']){
    const b=impulse(sample,1.4,k);ir[k]={length:b.length,first:b.getChannelData(0)[0]};
  }
  return {dry,comp,eq,ir};
 }''')
 print(result)
 assert result['comp']['rms'] < result['dry']['rms'] * .5, result
 assert result['eq']['rms'] < result['dry']['rms']*.65, result
 assert len({x['length'] for x in result['ir'].values()})>=5,result
 assert result['dry']['finite'] and result['comp']['finite'] and result['eq']['finite']
 b.close()
