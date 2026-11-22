// Optional local WAV multisample bank. Files are decoded only in the browser and
// never uploaded. No samples or licenses are bundled with this application.
const NOTE={'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11};
const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
export function sampleDescriptor(filename){
  const name=filename.replace(/\.(wav|wave|ogg|mp3)$/i,'');
  let root=null;
  let m=name.match(/(?:^|[_\s-])(?:midi|note)?[_\s-]?(\d{1,3})(?=$|[_\s-])/i);
  if(m){root=+m[1];}
  if(root===null){
    m=name.match(/(?:^|[_\s-])([A-G])([#b]?)(-?\d)(?=$|[_\s-])/i);
    if(m){const letter=m[1].toUpperCase();root=12*(Number(m[3])+1)+NOTE[letter]+(m[2]==='#'?1:m[2]==='b'?-1:0)}
  }
  if(root===null||root<0||root>127)return null;
  const velMatch=name.match(/(?:^|[_\s-])(?:v|vel|velocity)[_\s-]?(\d{1,3})(?=$|[_\s-])/i);
  const velocity=velMatch?clamp(+velMatch[1],1,127):96;
  return {root,velocity};
}
export class SampleLibrary{
  constructor(ctx){this.ctx=ctx;this.banks=new Map()}
  count(model){return this.banks.get(model)?.length||0}
  clear(model){this.banks.delete(model)}
  async load(model,files){
    const all=Array.from(files||[]);
    if(!all.length)throw Error('Selecione arquivos WAV com notas no nome, por exemplo C4_v80.wav.');
    if(all.length>128)throw Error('Máximo de 128 amostras por instrumento.');
    if(all.reduce((sum,file)=>sum+file.size,0)>180*1024*1024)throw Error('Os arquivos excedem 180 MB. Use um banco menor.');
    const results=[];
    for(const file of all){
      const parsed=sampleDescriptor(file.name);
      if(!parsed)continue;
      let decoded;
      try{decoded=await this.ctx.decodeAudioData(await file.arrayBuffer())}
      catch{continue}
      if(!decoded||!Number.isFinite(decoded.duration)||decoded.duration<.05)continue;
      results.push({...parsed,buffer:decoded,name:file.name});
    }
    if(!results.length)throw Error('Nenhuma amostra válida encontrada. Use nomes como C4_v40.wav, C4_v100.wav ou MIDI60_v90.wav.');
    // Replace atomically: a partially decoded bank never replaces a working bank.
    results.sort((a,b)=>a.root-b.root||a.velocity-b.velocity);
    this.banks.set(model,results);
    return results.length;
  }
  choose(model,key,velocity){
    const files=this.banks.get(model);if(!files?.length)return null;
    let nearest=Infinity;
    for(const s of files)nearest=Math.min(nearest,Math.abs(s.root-key));
    // Do not transpose a recording more than 12 semitones: use synthesis outside
    // its useful pitch range rather than creating an obviously wrong sound.
    if(nearest>12)return null;
    const candidates=files.filter(s=>Math.abs(s.root-key)===nearest);
    candidates.sort((a,b)=>Math.abs(a.velocity-velocity)-Math.abs(b.velocity-velocity));
    return candidates[0];
  }
  play(model,part,key,velocity,amount=1){
    const file=this.choose(model,key,velocity);if(!file)return false;
    const src=this.ctx.createBufferSource();src.buffer=file.buffer;
    src.playbackRate.value=2**((key-file.root)/12);
    const level=this.ctx.createGain();
    // Velocity influences amplitude even when only one recorded layer exists.
    level.gain.value=Math.min(1.4,Math.max(.08,(velocity/Math.max(32,file.velocity))**.85))*amount;
    src.connect(level).connect(part.gate);part.own(level);part.start(src);
    return true;
  }
}
