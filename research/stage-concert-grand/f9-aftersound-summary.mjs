import {readFileSync} from 'node:fs';
const a=JSON.parse(readFileSync(process.argv[2],'utf8'));
const db=(x,y)=>x>0&&y>0?20*Math.log10(x/y):null;
const w=a.windows.filter(x=>[0,1,2,4,8,10,13,14].includes(x.startS)).map(x=>({startS:x.startS,globalDb:db(x.rms,a.windows[0].rms),partials:x.partials.slice(0,3).map((p,i)=>({h:i+1,db:db(p.rms,a.windows[0].partials[i].rms),contrastDb:p.contrastDb}))}));
console.log('F96_WINDOWS '+JSON.stringify(w));
