#!/usr/bin/env node
/**
 * E2.7 — Offline audit of PRIVATE MIDI*_v*.wav note banks (no network).
 * Harmonic-family evidence vs adjacent semitones, NOT octave-proof or
 * acoustic origin/rights verification. Input bytes are never committed.
 * Usage: node scripts/audit_private_piano_bank.mjs BANK_DIR [OUTPUT_JSON]
 */
import {readdir,readFile,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';
import {auditPrivatePcmPitch} from '../research/private-pcm-pitch-audit.mjs';

const [directory,outputFile]=process.argv.slice(2);
if(!directory){
 console.error('usage: node scripts/audit_private_piano_bank.mjs BANK_DIRECTORY [OUTPUT_JSON]');
 process.exitCode=2;
}else{
 try{
  const root=resolve(directory),files=(await readdir(root)).filter(f=>/\.wav$/i.test(f)).sort();
  if(!files.length||files.length>128)throw new RangeError('expected 1..128 WAV files');
  const rows=[];
  for(const file of files){
   const match=/^MIDI(\d{1,3})_v(\d{1,3})\.wav$/i.exec(file);
   if(!match)throw new RangeError('unrecognized piano filename: '+file);
   const midiRoot=Number(match[1]),velocity=Number(match[2]);
   if(!Number.isInteger(velocity)||velocity<1||velocity>127)
    throw new RangeError('invalid nominal velocity: '+file);
   const buffer=await readFile(join(root,file));
   const evidence=auditPrivatePcmPitch(buffer,{midiRoot});
   rows.push({
    filename:file,nominalVelocity:velocity,
    sha256:createHash('sha256').update(buffer).digest('hex'),
    semitoneContrastDb:evidence.semitoneContrastDb,
    supportsLabeledSemitone:evidence.supportsLabeledSemitone,
    rms:evidence.rms
   });
  }
  const failed=rows.filter(x=>!x.supportsLabeledSemitone).map(x=>x.filename);
  const report={
   title:'E2.7 private note-level pitch evidence; not acoustic provenance',
   method:'Hann FFT; harmonic score ±1/2 semitones; octave NOT verified',
   absolutePitchVerified:false,originalVelocityVerified:false,
   rightsToRedistributeVerified:false,
   count:rows.length,passed:rows.length-failed.length,failed,files:rows
  };
  if(outputFile)await writeFile(resolve(outputFile),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify(report,null,2));
  if(failed.length)process.exitCode=1;
 }catch(error){
  console.error('private pitch audit failed: '+error.message);
  process.exitCode=1;
 }
}
