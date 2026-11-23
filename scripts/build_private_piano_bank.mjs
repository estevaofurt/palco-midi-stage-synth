#!/usr/bin/env node
/**
 * Build a user-local note bank, without publishing the source or the samples.
 * Usage:
 *   node scripts/build_private_piano_bank.mjs /path/to/source.wav manifest.json /path/to/output
 * The manifest requires a SHA256, manual pitch verification per crop, and
 * explicit private-use-only flag. It is NOT a license for redistribution.
 */
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {parseLocalPcmWav,extractLocalNote,validatePrivateBankManifest}
 from '../research/private-wav-note-bank.mjs';
const [sourceFile,manifestFile,outDirectory]=process.argv.slice(2);
if(!sourceFile||!manifestFile||!outDirectory){
 console.error('usage: node scripts/build_private_piano_bank.mjs SOURCE.wav MANIFEST.json OUTPUT_DIRECTORY');
 process.exitCode=2;
}else{
 try{
  const data=await readFile(resolve(sourceFile));
  const manifest=JSON.parse(await readFile(resolve(manifestFile),'utf8'));
  const checked=validatePrivateBankManifest(manifest,data);
  const metadata=parseLocalPcmWav(data);
  const outputs=[];
  await mkdir(resolve(outDirectory),{recursive:true});
  for(const note of manifest.notes){
   const filename=`MIDI${note.midiRoot}_v${note.nominalVelocity}.wav`;
   const wav=extractLocalNote(data,{startSeconds:note.startSeconds,
     durationSeconds:note.durationSeconds});
   // Existing output must not be overwritten accidentally.
   await writeFile(join(resolve(outDirectory),filename),wav,{flag:'wx'});
   outputs.push({filename,key:note.midiRoot,nominalVelocity:note.nominalVelocity,
     startSeconds:note.startSeconds,durationSeconds:note.durationSeconds,
     bytes:wav.length});
  }
  const report={tag:'E2.6 private listening',sourceSha256:checked.sourceSha256,
   outputSampleRate:metadata.sampleRate,channels:metadata.channels,
   bitDepth:metadata.bitsPerSample,
   redistributionAuthorized:false,originalMidiVelocitiesKnown:false,outputs};
  await writeFile(join(resolve(outDirectory),'PRIVATE_MANIFEST.json'),
    JSON.stringify(report,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({count:outputs.length,noteRange:outputs.map(x=>x.key),
   message:'private local bank generated; never commit/distribute user audio'}));
 }catch(e){
  console.error('private WAV extraction failed: '+e.message);
  process.exitCode=1;
 }
}
