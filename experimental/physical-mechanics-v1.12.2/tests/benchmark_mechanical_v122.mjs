import {PhysicalPianoEngine} from '../physical-piano.js';
const N=128,sr=48000;
function run(quality,count,mode){
  const e=new PhysicalPianoEngine(sr,quality);
  e.setMechanicalModel({enabled:mode==='coupled',amount:.55,sympathy:true});
  for(let i=0;i<count;i++)e.noteOn({id:i+1,key:30+i,speed:.7,character:'japanese'});
  const L=new Float32Array(N),R=new Float32Array(N),S=new Float32Array(N);
  for(let i=0;i<150;i++)e.render(L,R,S);
  const ns=[];let max=0,clipped=0;
  const start=process.hrtime.bigint();
  for(let b=0;b<375;b++){
    const t=process.hrtime.bigint();e.render(L,R,S);const dur=Number(process.hrtime.bigint()-t)*1e-6;ns.push(dur);
    for(let j=0;j<N;j++){const a=Math.max(Math.abs(L[j]),Math.abs(R[j]));max=Math.max(max,a);if(a>=1)clipped++}
  }
  const total=Number(process.hrtime.bigint()-start)*1e-6;
  ns.sort((a,b)=>a-b);
  return {quality,count,mode,msForOneSecond:+total.toFixed(2),p95BlockMs:+ns[Math.floor(ns.length*.95)].toFixed(4),maxBlockMs:+ns.at(-1).toFixed(4),peak:+max.toFixed(5),clipped};
}
for(const q of [['eco',32],['studio',64]])for(const m of ['baseline','coupled'])console.log(JSON.stringify(run(...q,m)));
