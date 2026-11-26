import {PianoEngine} from './piano-worklet.js';
import {PhysicalPianoEngine as B} from './physical-piano-legacy.js';
import {PhysicalPianoEngine as C} from './physical-piano.js';
import {HybridPianoEngine as D} from './physical-piano-hybrid.js';
import {candidates,score,recommend} from './device_polyphony_logic.mjs';
self.onmessage=({data:c})=>{
  try{
    const caps=candidates(c.engine,c.quality,c.profile,c.rate),rows=[];
    for(const n of caps){
      for(let trial=0;trial<2;trial++){
        const e=c.engine==='modal'?new PianoEngine(c.rate,n):new ({physicalLegacy:B,physical:C,hybrid:D}[c.engine])(c.rate,c.quality,n);
        if(c.engine==='physical')e.setMechanicalModel({enabled:true,amount:.5,sympathy:true});
        if(c.engine==='modal')e.maxPartials=28;
        const L=new Float32Array(128),R=new Float32Array(128),S=new Float32Array(128);
        const strike=i=>e.noteOn({id:i,key:36+(i-1)%36,speed:.72,hardness:.5,character:'american',send:.12});
        for(let i=1;i<=n;i++)strike(i);
        e.setSustain?.(1);
        const times=[];let active=true,peak=0;
        for(let b=0;b<300;b++){
          if(b%10===0)for(let i=1;i<=n;i++)if(!e.find(i))strike(i);
          const start=performance.now();e.render(L,R,S,128);const dt=performance.now()-start;
          if(b>=100){
            times.push(dt);active=active&&e.voices.filter(v=>v.active).length===n;
            for(const x of L){if(!Number.isFinite(x))throw Error('áudio não finito');peak=Math.max(peak,Math.abs(x))}
            for(const buf of [R,S])for(const x of buf)if(!Number.isFinite(x))throw Error('áudio não finito');
          }
        }
        const row={voices:n,trial, ...score(times,active&&peak>0,c.rate),peak};
        rows.push(row);self.postMessage({type:'row',row});
      }
      if(!rows.slice(-2).every(x=>x.pass))break;
    }
    self.postMessage({type:'done',recommended:recommend(rows,caps),config:c,rows});
  }catch(e){self.postMessage({type:'error',message:String(e?.message??e)})}
};
