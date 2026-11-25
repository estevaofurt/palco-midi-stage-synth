import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {join} from 'node:path';
import {inspect24} from './f9-rattle-comparison.mjs';
import {inspectPair} from './f9-soft-pcm-audit.mjs';
import {pitchSpectrum,cents} from './f11f-bass-pitch.mjs';
const [input,out]=process.argv.slice(2);
if(!input||!out)throw Error('input/output required');
const cases=[];
for(const midi of [36,43,48])for(const count of [1,2]){
 const dir=join(input,'F11E-bass-midi'+midi+'-strings'+count+'-touch127-long'),files=readdirSync(dir);
 const find=s=>{const q=files.filter(x=>x.endsWith(s));if(q.length!==1)throw Error('unique file '+s);return join(dir,q[0])};
 const meta=JSON.parse(readFileSync(find('_rattle.json'),'utf8')),raw=JSON.parse(readFileSync(find('_20s.json'),'utf8'));
 const wave=readFileSync(find('_24bit.wav')),base=readFileSync(find('_20s.wav')),pair=inspectPair(base,wave),p=inspect24(wave);
 if(meta.midi!==midi||meta.count!==count||meta.midiVelocity!==127||meta.duration!==20||meta.clipped!==0||meta.gain!==.2757526758002555||p.frames!==960239||pair.frames!==p.frames)throw Error('source metadata');
 const channels=[0,1].map(ch=>Float64Array.from({length:p.frames},(_,i)=>{const j=i*6+ch*3;return ((p.pcm[j]|p.pcm[j+1]<<8|p.pcm[j+2]<<16)<<8>>8)/8388607;}));
 const f1=440*2**((midi-69)/12),B=meta.wire.B;
 const windows=[[.25,1.25],[1,3],[3,7],[8,12],[14,18]].map(([a,b])=>pitchSpectrum(channels,48000,a,b,f1,B));
 const wires=raw.chunks[0].wires.map(w=>({f1Hz:w.f1Hz,cents:cents(w.f1Hz,f1),B:w.B}));
 cases.push({midi,count,f1,B,wires,windows,relativeDrops:meta.relativeDrops});
}
mkdirSync(out,{recursive:true});
writeFileSync(join(out,'pitch-analysis.json'),JSON.stringify({scope:'spectral peaks in actual PCM, not perceived pitch or resolved unison below window resolution',cases},null,2),{flag:'wx'});
console.log('F11F_PITCH_RESULT '+JSON.stringify(cases.map(q=>({midi:q.midi,count:q.count,f1:q.f1,wires:q.wires,windows:q.windows.map(w=>({startS:w.startS,endS:w.endS,dominant:w.dominant,fundamental:w.partials[0],partials:w.partials.slice(1,4).map(p=>({h:p.h,peak:p.peak,usable:p.usable}))}))}))));
