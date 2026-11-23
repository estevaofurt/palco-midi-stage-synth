#!/usr/bin/env node
/**
 * Private research PCM from ONLY the E2.3 mechanical network.
 * No piano WAV / soundfont / sample-library imports, ever.
 * CLI: node scripts/render_pure_physical_e28.mjs [output.wav]
 */
import {writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {renderPurePhysicalMechanical,encodeNormalizedMechanicalWav16}
 from '../research/pure-physical-audition-e28.mjs';

const output=process.argv[2]||'e28-physical-only-mechanical-proxy.wav';
if(!/\\.wav$/i.test(output))throw new RangeError('output must end in .wav');
const {signal,diagnostics,peakMechanical}=
 renderPurePhysicalMechanical({sampleRate:48000,seconds:13,
  partialsBass:5,partialsTreble:2});
const {wav,gain}=encodeNormalizedMechanicalWav16(signal,48000);
await writeFile(output,wav,{flag:'w'});
console.log(JSON.stringify({
 file:output,bytes:wav.length,
 sha256:createHash('sha256').update(wav).digest('hex'),
 sampleRate:48000,channels:1,format:'PCM16',
 peakMechanical,gainForAudibility:gain,diagnostics,
 warning:'HEARING TEST ONLY: normalized mechanical board velocity, NOT pressure in Pa, not calibrated realistic piano. ZERO samples/recordings/IR.'
},null,2));
