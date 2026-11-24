import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fft} from './f8-render.mjs';
import {attackSpectrum,decodeCanonical24} from './f9-attack-spectrum.mjs';
const [dir,out]=process.argv.slice(2),manifest=JSON.parse(readFileSync(dir+'/manifest.json')),speeds=[.15,.25,.35,.5,1,2.5];
if(manifest.rows.length!==6||manifest.rows.some((r,i)=>r.velocity!==speeds[i]||r.gain!==.36767023440034063||r.feltFactor!==1.5))throw Error('manifest mismatch');
const rows=manifest.rows.map(r=>{
 const bytes=readFileSync(dir+'/'+r.file);if(createHash('sha256').update(bytes).digest('hex')!==r.sha256.pcm24)throw Error('digest mismatch');
 const channels=decodeCanonical24(bytes);
 return {velocity:r.velocity,contactSpanS:r.attack.contactSpanS,windows:[{startS:0,endS:.05},{startS:.05,endS:.15},{startS:.15,endS:.5}].map(w=>attackSpectrum(channels,48000,fft,w))};
});
const result={scope:'Hann-window normalized spectral energy and centroid up to 12 kHz; stereo power average; fixed file-relative windows, no onset alignment, not perceptual loudness or C5 calibration',rows};
writeFileSync(out,JSON.stringify(result,null,2),{flag:'wx'});
console.log('F917B_ATTACK '+JSON.stringify(result));
