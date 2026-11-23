#!/usr/bin/env node
/**
 * OFFLINE, user-audition experimental E2.9 ray-traced air radiation.
 * No recorded piano, WAV input, SoundFont, sample pack or measured IR.
 */
import {writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {renderAnalyticPhysicalPiano} from '../research/pure-physical-radiation-e29.mjs';
import {encodeRelativeStereoWav16} from '../research/analytic-soundboard-radiation.mjs';

const output=process.argv[2]||'e29-physical-piano-analytic-air.wav';
if(!/\.wav$/i.test(output))throw new RangeError('output must end with .wav');
const result=renderAnalyticPhysicalPiano();
const {wav,gain}=encodeRelativeStereoWav16(result.left,result.right,48000);
await writeFile(output,wav,{flag:'w'});
console.log(JSON.stringify({
 file:output,format:'WAV PCM16 stereo 48000Hz',bytes:wav.length,
 sha256:createHash('sha256').update(wav).digest('hex'),
 globalAuditionGain:gain,diagnostics:result.diagnostics,
 warning:'RESEARCH ONLY. Physical surface radiation equations, not a measured piano; generalized modal velocities lack SI calibration.'
},null,2));
