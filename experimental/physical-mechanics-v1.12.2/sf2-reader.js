// Offline, dependency-free parser for standard uncompressed SF2 soundfonts.
// This intentionally does not parse SFZ directories, SF3/Vorbis or proprietary formats.
const text=(view,at,len)=>{
  let out='';for(let i=0;i<len;i++){const c=view.getUint8(at+i);if(!c)break;out+=String.fromCharCode(c)}return out.trim();
};
const readChunk=(v,at,end)=>{
  if(at+8>end)throw Error('Bloco RIFF truncado');
  const size=v.getUint32(at+4,true),start=at+8,stop=start+size;
  if(stop>end)throw Error('Bloco RIFF fora dos limites');
  return {tag:text(v,at,4),start,end:stop,next:stop+(size&1),size};
};
function collect(view,from,end){const chunks={};for(let i=from;i+8<=end;){const c=readChunk(view,i,end);chunks[c.tag]=c;i=c.next}return chunks}
const signed=(v,pos)=>v.getInt16(pos,true);
const range=(num)=>[num&255,(num>>>8)&255];
const zones=(bags,gens,begin,end)=>{
  const result=[];
  for(let i=begin;i<end;i++){
    let gen={},lo=bags[i].gen,hi=bags[i+1].gen;
    for(let j=lo;j<hi;j++){
      const g=gens[j];if(g.op===43||g.op===44)gen[g.op]=range(g.raw);
      else gen[g.op]=signed(gens[j].view,gens[j].pos+2);
    }
    result.push(gen);
  }
  return result;
};
const merge=(...gens)=>Object.assign({},...gens);
const r=(g,op,defaultValue)=>g[op]??defaultValue;
export class SF2Reader {
  constructor(buffer){
    if(!(buffer instanceof ArrayBuffer))throw Error('Arquivo SF2 inválido');
    if(buffer.byteLength>100*1024*1024)throw Error('Arquivo muito grande (máximo: 100 MB).');
    const v=new DataView(buffer),total=v.byteLength;
    if(total<64||text(v,0,4)!=='RIFF'||text(v,8,4)!=='sfbk')throw Error('O arquivo não é um SoundFont SF2 válido.');
    const riffEnd=Math.min(total,8+v.getUint32(4,true));let sections={};
    for(let i=12;i+12<=riffEnd;){const c=readChunk(v,i,riffEnd);if(c.tag==='LIST')sections[text(v,c.start,4)]=collect(v,c.start+4,c.end);i=c.next}
    const pd=sections.pdta,sd=sections.sdta;
    if(!pd||!sd?.smpl)throw Error('Faltam dados de amostras no SF2.');
    const table=(tag,stride,decode)=>{
      const c=pd[tag];if(!c||c.size%stride)throw Error('Tabela SF2 inválida: '+tag);
      return Array.from({length:c.size/stride},(_,i)=>decode(c.start+i*stride));
    };
    const presets=table('phdr',38,p=>({name:text(v,p,20),program:v.getUint16(p+20,true),bank:v.getUint16(p+22,true),bag:v.getUint16(p+24,true)}));
    const pbag=table('pbag',4,p=>({gen:v.getUint16(p,true)}));
    const pgen=table('pgen',4,p=>({op:v.getUint16(p,true),raw:v.getUint16(p+2,true),view:v,pos:p}));
    const inst=table('inst',22,p=>({name:text(v,p,20),bag:v.getUint16(p+20,true)}));
    const ibag=table('ibag',4,p=>({gen:v.getUint16(p,true)}));
    const igen=table('igen',4,p=>({op:v.getUint16(p,true),raw:v.getUint16(p+2,true),view:v,pos:p}));
    const shdr=table('shdr',46,p=>({name:text(v,p,20),start:v.getUint32(p+20,true),end:v.getUint32(p+24,true),loopStart:v.getUint32(p+28,true),loopEnd:v.getUint32(p+32,true),rate:v.getUint32(p+36,true),pitch:v.getUint8(p+40),correction:v.getInt8(p+41),type:v.getUint16(p+44,true)}));
    if(!presets.length||!inst.length||!shdr.length)throw Error('SoundFont sem instrumentos.');
    this.sampleOffset=sd.smpl.start;this.sampleCount=sd.smpl.size/2;this.buffer=buffer;this.view=v;
    this.samples=shdr;this.instruments=inst.map((row,i)=>zones(ibag,igen,row.bag,inst[i+1]?.bag??row.bag));
    this.presets=presets.slice(0,-1).map((p,i)=>({name:p.name,program:p.program,bank:p.bank,zones:zones(pbag,pgen,p.bag,presets[i+1].bag)}));
    this.programs=this.presets.map((p,i)=>({id:i,name:`${p.bank}:${p.program} · ${p.name}`}));
    this.cache=new Map();this.cacheBytes=0;
  }
  getZones(program,key,velocity){
    const preset=this.presets[program];if(!preset)return [];
    const chosen=[];
    const includes=(g,op,x)=>{const t=g[op];return !t||(x>=t[0]&&x<=t[1])};
    const pg=preset.zones.find(g=>g[41]===undefined)||{};
    for(const p of preset.zones){if(p[41]===undefined||!includes(p,43,key)||!includes(p,44,velocity))continue;
      const instrumentId=p[41];const iz=this.instruments[instrumentId]||[];
      const ig=iz.find(g=>g[53]===undefined)||{};
      for(const item of iz){if(item[53]===undefined||!includes(item,43,key)||!includes(item,44,velocity))continue;
        const global=merge(pg,ig),local=merge(p,item);
        if(!includes(global,43,key)||!includes(global,44,velocity))continue;
        const sample=this.samples[item[53]];
        if(!sample||sample.end<=sample.start||sample.end>this.sampleCount)continue;
        chosen.push({sample,gen:merge(global,local),sampleIndex:item[53]});
      }
    }
    return chosen.slice(0,5);
  }
  audioBuffer(ctx,index){
    if(this.cache.has(index))return this.cache.get(index);
    const s=this.samples[index],start=s.start,end=s.end,count=end-start;
    if(count<8||count>20000000)throw Error('Amostra SF2 inválida.');
    const result=ctx.createBuffer(1,count,Math.max(8000,Math.min(96000,s.rate)));
    const data=result.getChannelData(0);
    for(let i=0;i<count;i++)data[i]=this.view.getInt16(this.sampleOffset+(start+i)*2,true)/32768;
    this.cache.set(index,result);this.cacheBytes+=data.byteLength;
    const cap=48*1024*1024;
    while(this.cacheBytes>cap&&this.cache.size>1){
      const [oldId,oldBuffer]=this.cache.entries().next().value;
      this.cacheBytes-=oldBuffer.length*4;this.cache.delete(oldId);
    }
    return result;
  }
}
