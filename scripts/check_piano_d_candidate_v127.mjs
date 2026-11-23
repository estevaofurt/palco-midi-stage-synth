/** Regression against a historic source snapshot checked out with `git show`.
 * This script is an experimental test harness, not browser deployment.
 * It enforces bitwise identical C4-C6 stereo PCM for all three qualities.
 */
import {HybridPianoEngine as Candidate} from '../physical-piano-hybrid.js';
import {HybridPianoEngine as Stable} from '../.stage-d-v126-baseline.mjs';
const sr=48000,block=128;
let equal=0,steps=0;const diffs=[];
function run(Engine,key,velocity,quality){
 const e=new Engine(sr,quality);
 const l=new Float32Array(block),r=new Float32Array(block),s=new Float32Array(block);
 e.noteOn({id:100,key,speed:velocity/127,character:'american',
  hardness:.55,brightness:.50,send:.2});
 const n=Math.floor(sr*.75),buf=new Float32Array(n*2);
 for(let i=0;i<n;i+=block){
  const count=Math.min(block,n-i);
  e.render(l,r,s,count);
  for(let j=0;j<count;j++){
   buf[2*(i+j)]=l[j];buf[2*(i+j)+1]=r[j];
  }
 }
 return buf;
}
function rms(x){let sum=0;for(const v of x)sum+=v*v;return Math.sqrt(sum/x.length)}
for(const key of [49,60,72,84,108])for(const v of [32,80,120])
 for(const q of ['eco','balanced','studio']){
  const a=run(Stable,key,v,q),b=run(Candidate,key,v,q);
  for(let i=0;i<a.length;i++)if(a[i]!==b[i])throw Error('C4+ stable PCM changed! key='+key+' v='+v+' quality='+q+' frame='+i+' old='+a[i]+' new='+b[i]);
  equal++;steps+=a.length;
 }
for(const key of [24,36,48])for(const velocity of [32,80,120]){
 const a=run(Stable,key,velocity,'eco'),b=run(Candidate,key,velocity,'eco');
 let peak=0,nonfinite=0,changed=0;
 for(let i=0;i<b.length;i++){if(!Number.isFinite(b[i]))nonfinite++;peak=Math.max(peak,Math.abs(b[i]));if(a[i]!==b[i])changed++;}
 const ratio=rms(b)/rms(a);
 if(nonfinite||peak>.961||!(ratio>.03&&ratio<15)||changed<100)throw Error('Bass candidate invalid key='+key+' v='+velocity+' ratio='+ratio+' peak='+peak+' changed='+changed);
 diffs.push({key,velocity,relativeRms:Math.round(ratio*1000)/1000,peak:Math.round(peak*1e4)/1e4,changedSamples:changed});
}
console.log('C4+ BITWISE PCM EQUAL: '+equal+' cases, '+steps+' stereo samples compared against main v1.12.6');
for(const d of diffs)console.log('BASS_CANDIDATE '+JSON.stringify(d));
console.log('No claim of acoustic realism: tests only check deliberate bass changes and untouched C4–C6.');
