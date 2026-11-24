import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fft} from './f8-render.mjs';
import {decodeCanonical24} from './f9-attack-spectrum.mjs';
import {inspectRattleWindow} from './f9-rattle-spectrum.mjs';
const [dir,out]=process.argv.slice(2),manifest=JSON.parse(readFileSync(dir+'/manifest.json')),historic=JSON.parse(readFileSync(new URL('./audio/analysis_f9_18a_ci.json',import.meta.url))).listening;
if(manifest.rows.length!==12||manifest.gain!==historic.gain||manifest.rows.some((r,i)=>r.midiVelocity!==historic.rows[i].midiVelocity||r.sha256!==historic.rows[i].sha256||r.file!==historic.rows[i].file))throw Error('historic manifest mismatch');
const rows=manifest.rows.map(r=>{
 const bytes=readFileSync(dir+'/'+r.file);if(createHash('sha256').update(bytes).digest('hex')!==r.sha256)throw Error('hash mismatch');
 const channels=decodeCanonical24(bytes);
 return {midiVelocity:r.midiVelocity,velocity:r.velocity,windows:[[.025,.525],[.525,1.025],[1.025,1.525]].map(([startS,endS])=>inspectRattleWindow(channels,48000,fft,{startS,endS}))};
});
const result={scope:'off-partial energy diagnostic, nominal stiff string centers; includes leakage, loaded frequency shifts, board transients, unison and polarization; not a noise floor or proof of rattle',sourceRunId:45464139346,sourceArtifactId:14954032000,rows};
writeFileSync(out,JSON.stringify(result,null,2),{flag:'wx'});
console.log('F919_RATTLE '+JSON.stringify(rows.map(r=>({midiVelocity:r.midiVelocity,velocity:r.velocity,windows:r.windows.map(w=>({startS:w.startS,wideOffFraction:w.wideOffFraction,narrowOffFraction:w.narrowOffFraction,offPeaks:w.offPeaks.slice(0,3)}))}))));
