/**
 * Limited automated acoustic regression against 15 hash-verified Iowa Steinway B
 * recordings. NOT a perceptual realism score. SOURCE audio never enters Git.
 */
import {readFileSync} from 'node:fs';
const input=process.argv[2];
if(!input)throw Error('usage: node scripts/check_iowa_hybrid_improvement.mjs diagnostic.json');
const records=JSON.parse(readFileSync(input,'utf8')).notes;
if(records?.length!==15)throw Error('Expected 5 notes x 3 source layers');
const means=[],longMeans=[],details=[];
for(const n of records){
  if(!n.instrument?.includes('Steinway Model B')||!/^[a-f0-9]{64}$/.test(n.provenance.sha256))
    throw Error('Original-source identity/hash missing');
  const e=n.stage?.D_hybrid;
  if(!e||e.nonFinite>0||e.clipped>0||!(e.peak>0&&e.peak<.95))
    throw Error('Invalid or clipped D output for '+n.key+'/'+n.dynamic);
  const ref=n.real?.earlySpectrum?.harmonics;
  const newPartial=e.earlySpectrum?.harmonics;
  if(!ref||!newPartial||ref.length!==newPartial.length)throw Error('Incompatible spectrum');
  const trusted=ref.map((x,i)=>({orig:x,stage:newPartial[i]})).filter(({orig,stage})=>
    orig.n>=2&&orig.n<=8&&orig.relativeDb>=-34&&
    Number.isFinite(orig.relativeDb)&&Number.isFinite(stage.relativeDb));
  if(!trusted.length)throw Error('No trustworthy acoustic partials for '+n.key+'/'+n.dynamic);
  const early=trusted.reduce((s,x)=>s+Math.abs(x.orig.relativeDb-x.stage.relativeDb),0)/trusted.length;
  means.push(early);
  const longRef=n.real.harmonics,longD=e.harmonics;
  const reliable=longRef.map((x,i)=>({orig:x,stage:longD[i]})).filter(({orig,stage})=>
    orig.n>=2&&orig.n<=8&&orig.relativeDb>-30&&
    Number.isFinite(orig.relativeDb)&&Number.isFinite(stage?.relativeDb));
  const late=reliable.length?
    reliable.reduce((s,x)=>s+Math.abs(x.orig.relativeDb-x.stage.relativeDb),0)/reliable.length:null;
  if(late!==null)longMeans.push(late);
  details.push({key:n.key,dynamic:n.dynamic,early:Math.round(early*100)/100,
    comparable:trusted.length,long:late===null?null:Math.round(late*100)/100});
}
const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
const earlyAvg=mean(means),longAvg=mean(longMeans);
console.log('Iowa verified original spectra: 15 notes; D early |Δ|='+earlyAvg.toFixed(2)+
  'dB; D longer-window |Δ|='+longAvg.toFixed(2)+'dB (diagnostic, not listening score)');
for(const d of details)console.log('RECORD '+d.key+'/'+d.dynamic+
 ' early='+d.early+'dB n='+d.comparable+' longer='+d.long+'dB');
if(earlyAvg>=8||longAvg>=15)throw Error('Stage D acoustic transfer regressed; inspect spectra before merging');
for(const key of [36,48,60]){
 const target=details.find(x=>x.key===key&&x.dynamic==='mf');
 if(!(target.early<10))throw Error('Middle intensity lower/central register mismatch: '+key);
}
