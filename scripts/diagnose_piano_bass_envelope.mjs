/**
 * Stage Synth — bass-piano v1.12.7 PREPARATION only; DOES NOT CHANGE AUDIO DSP.
 *
 * Measures onset energy and partial evolution instead of pretending that a
 * 8192/16384-point FFT beginning at 18 ms represents the first 18 ms.
 * In the bass C2 (65 Hz) one 12 ms window covers less than one cycle;
 * the first window is a BROADBAND energy/transient measurement ONLY.
 * Original Iowa PCM stays in private CI temp. Publish numeric summaries only.
 */
import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {HybridPianoEngine} from '../physical-piano-hybrid.js';
import {decodeF32le,locateAttack} from './analyze_reference_audio.mjs';
import {rmsWindow,spectrum,findPartial,midiHz} from '../tests/piano_acoustic_metrics.mjs';

export const RATE=48000, DURATION=1.65;
export const BASS_BINS=Object.freeze([
  [0,.012],[.012,.036],[.036,.100],[.100,.220],
  [.220,.450],[.450,.900],[.900,1.400]
]);
const FFT_SIZE=8192;
const FFT_STARTS=[.020,.220,.520,.850];
const clamp=(x,a,b)=>Math.min(b,Math.max(a,x));
const db=x=>20*Math.log10(Math.max(1e-12,x));
const round=x=>Number.isFinite(x)?Math.round(x*100)/100:null;

export function transientEnvelope(samples,sampleRate=RATE){
  if(!(samples instanceof Float32Array||samples instanceof Float64Array))
    throw new TypeError('PCM must be Float32Array or Float64Array');
  if(samples.length<Math.ceil(DURATION*sampleRate))
    throw new RangeError('PCM too short for transient');
  const reference=rmsWindow(samples,sampleRate,.100,.220);
  if(!(reference>1e-8))throw new RangeError('note too quiet for envelope');
  // Compute baseline loudness-independent envelope. Different mic gains do not
  // contaminate the *time-shape* comparison, but the normalization means these
  // figures cannot validate absolute piano loudness or a calibrated MIDI curve.
  const envelopeDb=BASS_BINS.map(([a,b])=>round(db(
    Math.max(1e-12,rmsWindow(samples,sampleRate,a,b))/reference
  )));
  const alpha=1-Math.exp(-2*Math.PI*900/sampleRate);
  let low=0;
  const bandPower=new Float64Array(BASS_BINS.length),counts=new Uint32Array(BASS_BINS.length);
  for(let i=0;i<Math.round(1.4*sampleRate);i++){
    const x=samples[i];if(!Number.isFinite(x))throw new Error('nonfinite PCM');
    low+=alpha*(x-low);
    const high=x-low;
    const t=i/sampleRate;
    for(let k=0;k<BASS_BINS.length;k++){
      const [a,b]=BASS_BINS[k];
      if(t>=a&&t<b){bandPower[k]+=high*high;counts[k]++;break}
    }
  }
  const highpassDb=Array.from(bandPower,(v,k)=>round(
    db(Math.sqrt(v/Math.max(1,counts[k]))/reference)
  ));
  return {normalizationWindow:[.100,.220],bins:BASS_BINS,
    envelopeDb,highpass900HzDb:highpassDb,
    attackToBodyDb:round(envelopeDb[1]-envelopeDb[3]),
    earlyToTailDb:round(envelopeDb[3]-envelopeDb[6])};
}

/**
 * Spectral trajectories: each 8192 frame spans 171 ms @48kHz, so these are
 * time-averaged harmonic windows, NEVER isolated first-millisecond attacks.
 * Relative magnitudes are not string force, bridge FRF or room compensation.
 */
export function partialTrajectories(samples,key,sampleRate=RATE){
  const f0=midiHz(key);
  const result=[];
  for(const start of FFT_STARTS){
    const s=spectrum(samples,sampleRate,start,FFT_SIZE);
    const fundamental=findPartial(s,f0,{relativeWindow:.045,minHz:6});
    const harmonics=[];
    for(let n=1;n<=8&&n*f0<sampleRate*.43;n++){
      const peak=findPartial(s,n*f0,{relativeWindow:.045,minHz:6});
      harmonics.push({n,fHz:round(peak.frequency),
        relativeDb:round(db(peak.amplitude/Math.max(fundamental.amplitude,1e-12)))});
    }
    result.push({startSeconds:start,spanSeconds:FFT_SIZE/sampleRate,
      harmonics});
  }
  return result;
}

export function renderStageD(key,velocity,character='american'){
  const e=new HybridPianoEngine(RATE,'eco');
  e.noteOn({id:1,key,speed:clamp(velocity/127,.001,1),hardness:.5,
    character,brightness:.5,send:0});
  const out=new Float32Array(Math.ceil(DURATION*RATE)),l=new Float32Array(128),r=new Float32Array(128);
  for(let pos=0;pos<out.length;pos+=128){
    const n=Math.min(128,out.length-pos);
    e.render(l,r,null,n);
    for(let j=0;j<n;j++)out[pos+j]=(l[j]+r[j])*.5;
  }
  return out;
}

export function diagnoseOne(entry){
  if(!Number.isInteger(entry.key)||entry.key<21||entry.key>108)
    throw new RangeError('invalid note key');
  if(!/^[a-f0-9]{64}$/.test(entry.sha256))
    throw new Error('original source SHA256 missing');
  const pcm=decodeF32le(readFileSync(entry.pcmPath));
  const onset=locateAttack(pcm,RATE),offset=Math.round(onset*RATE);
  if(offset+Math.ceil(DURATION*RATE)>pcm.length)
    throw new Error('original source note too short after detected onset');
  const real=pcm.slice(offset,offset+Math.ceil(DURATION*RATE));
  const nominalVelocity={pp:32,mf:80,ff:120}[entry.dynamic];
  if(!nominalVelocity)throw new Error('unrecognized dynamics');
  const stage=renderStageD(entry.key,nominalVelocity,entry.stageCharacter||'american');
  const a=transientEnvelope(real),b=transientEnvelope(stage);
  return {
    key:entry.key,dynamic:entry.dynamic,
    sourceSha256:entry.sha256,sourceURL:entry.originalUrl,
    onsetSeconds:round(onset),nominalMidiVelocity:nominalVelocity,
    nominalVelocityIsMeasured:false,
    realEnvelope:a,stageDEnvelope:b,
    envelopeDeltaDb:a.envelopeDb.map((x,i)=>round(b.envelopeDb[i]-x)),
    highpassDeltaDb:a.highpass900HzDb.map((x,i)=>round(b.highpass900HzDb[i]-x)),
    realPartials:partialTrajectories(real,entry.key),
    stageDPartials:partialTrajectories(stage,entry.key)
  };
}

if(process.argv[1]&&fileURLToPath(import.meta.url)===process.argv[1]){
  if(process.argv.length!==4)
    throw Error('usage: node scripts/diagnose_piano_bass_envelope.mjs manifest.json output.json');
  const source=JSON.parse(readFileSync(process.argv[2],'utf8'));
  if(!Array.isArray(source.notes)||source.notes.length!==15)
    throw Error('requires 15 SHA256-verified original Iowa recordings');
  const records=source.notes.map(diagnoseOne);
  const low=records.filter(x=>x.key===36||x.key===48);
  const absoluteAverage=arr=>arr.reduce((s,x)=>s+Math.abs(x),0)/Math.max(1,arr.length);
  const bassBody=absoluteAverage(low.map(x=>x.envelopeDeltaDb[3]));
  const bassTransient=absoluteAverage(low.map(x=>x.envelopeDeltaDb[0]));
  const diagnosis={
    schema:'stage-v127-preparation-bass-attack-v1',
    dspModified:false,
    input:'University of Iowa original Steinway B; AIFF SHA256 already verified in workflow',
    nominalMidiVelocityCalibrated:false,
    frameLimitations:'0-12 ms and 12-36 ms are BROADBAND only, NOT resolvable C2 partials; harmonic trajectories use a 171 ms Hann FFT each.',
    roomMicrophoneCaution:'Iowa includes microphone and room; transient deviations not identifiable as hammer-only behavior.',
    bassNotes:[36,48],guardrailNotes:[60,72,84],
    bassBodyEnvelopeMeanAbsDb:round(bassBody),
    bassFirst12msMeanAbsDb:round(bassTransient),
    records
  };
  writeFileSync(process.argv[3],JSON.stringify(diagnosis,null,2)+'\n');
  console.log('BASS PREP DIAGNOSTIC: 15 original notes, no DSP changes, no published PCM');
  console.log('BASS C2/C3 mean abs early broadband 0-12ms delta='+diagnosis.bassFirst12msMeanAbsDb+'dB');
  for(const x of low)
    console.log('BASS '+x.key+'/'+x.dynamic+
      ' first12='+x.envelopeDeltaDb[0]+' dB, 12-36='+x.envelopeDeltaDb[1]+
      ' dB, body100-220='+x.envelopeDeltaDb[3]+
      ' dB, tail900-1400='+x.envelopeDeltaDb[6]+' dB');
  for(const x of records.filter(x=>x.key>=60&&x.dynamic==='mf'))
    console.log('GUARD '+x.key+'/mf relative early '+x.envelopeDeltaDb[0]+
      ' dB; body '+x.envelopeDeltaDb[3]+' dB');
}
