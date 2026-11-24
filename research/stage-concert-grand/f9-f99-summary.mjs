import {readFileSync} from 'node:fs';
const [input,label]=process.argv.slice(2);if(!['FLOAT','PCM16'].includes(label))throw Error('label');
const a=JSON.parse(readFileSync(input,'utf8'));
const db=(x,y)=>x>0&&y>0?20*Math.log10(x/y):null;
const times=[0,.5,1,2,4,6,8,10,12,14,16,18,19,20,24,29,30,34,35,39];
const windows=a.windows.filter(x=>times.includes(x.startS)).map(x=>({startS:x.startS,globalRms:x.rms,globalDb:db(x.rms,a.windows[0].rms),partials:x.partials.map((p,i)=>({h:i+1,rms:p.rms,db:db(p.rms,a.windows[0].partials[i].rms),contrastDb:p.contrastDb}))}));
console.log('F99_'+label+'_WINDOWS '+JSON.stringify(windows));
console.log('F99_'+label+'_DROPS '+JSON.stringify({broadband:a.broadband,partials:a.partialDrops,analyzedThroughS:a.analyzedThroughS}));
