#!/usr/bin/env node
/** Rejection evidence, NOT a sonically improved piano candidate.
 * This only synthesizes passive mechanical equations and evaluates them.
 * The uploaded American WAV is never loaded or transferred.
 */
import {writeFile} from 'node:fs/promises';
import {diagnoseBridgeVsPanel} from '../research/diagnose-piano-source-e31.mjs';

const report=diagnoseBridgeVsPanel({sampleRate:48000,seconds:.5,key:48});
await writeFile('e31-physical-source-diagnostic.json',
 JSON.stringify(report,null,2)+'\n',{flag:'w'});
console.log(JSON.stringify(report,null,2));
