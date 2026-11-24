import {readFileSync,writeFileSync} from 'node:fs';
import {parsePcm16} from './f9-decay-analysis.mjs';
import {fft} from './f8-render.mjs';
import {analyzeSustain} from './f9-long-analysis.mjs';
const [input,output,onset='0',rawRate='48000',rawChannels='2',excludeEnd='0']=process.argv.slice(2);
if(!input||!output||input===output)throw Error('input WAV or raw f32le, output JSON, onset seconds, raw rate, raw channels, exclude end seconds');
const b=readFileSync(input);let rate,channels;
if(input.endsWith('.f32')){rate=Number(rawRate);const c=Number(rawChannels);if(!Number.isInteger(c)||c<1||c>8||b.length%(4*c))throw Error('raw format');channels=Array.from({length:c},(_,j)=>Float64Array.from({length:b.length/(4*c)},(_,i)=>b.readFloatLE(4*(i*c+j))));}
else {const q=parsePcm16(b),v=new DataView(q.data.buffer,q.data.byteOffset,q.data.byteLength);rate=q.rate;channels=Array.from({length:q.channels},(_,j)=>Float64Array.from({length:q.frames},(_,i)=>v.getInt16(2*(i*q.channels+j),true)/32768));}
const report=analyzeSustain(channels,rate,fft,{onsetS:Number(onset),excludeEndS:Number(excludeEnd)});
writeFileSync(output,JSON.stringify(report,null,2),{flag:'wx'});
console.log(JSON.stringify({file:input,analyzedThroughS:report.analyzedThroughS,broadband:report.broadband,firstThreePartials:report.partialDrops.slice(0,3)}));
