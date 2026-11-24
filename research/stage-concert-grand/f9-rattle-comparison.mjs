// F9.19f: offline comparison of existing renders, no DSP changes.
const ascii=(a,p,n)=>String.fromCharCode(...a.subarray(p,p+n));
const put=(a,p,s)=>{for(let i=0;i<s.length;i++)a[p+i]=s.charCodeAt(i)};
export function inspect24(a){
 if(!(a instanceof Uint8Array)||a.length<44)throw Error('short WAV');
 const v=new DataView(a.buffer,a.byteOffset,a.byteLength);
 if(ascii(a,0,4)!=='RIFF'||ascii(a,8,4)!=='WAVE'||ascii(a,12,4)!=='fmt '||
 v.getUint32(4,true)!==a.length-8||v.getUint32(16,true)!==16||
 v.getUint16(20,true)!==1||v.getUint16(22,true)!==2||v.getUint32(24,true)!==48000||
 v.getUint32(28,true)!==288000||v.getUint16(32,true)!==6||v.getUint16(34,true)!==24||
 ascii(a,36,4)!=='data'||v.getUint32(40,true)!==a.length-44||(a.length-44)%6)throw Error('expected canonical stereo 48k PCM24');
 return {frames:(a.length-44)/6,pcm:a.subarray(44)};
}
export function header(frames){
 if(!Number.isInteger(frames)||frames<1||frames*6+36>0xffffffff)throw Error('invalid frames');
 const a=new Uint8Array(44+frames*6),v=new DataView(a.buffer);
 put(a,0,'RIFF');v.setUint32(4,a.length-8,true);put(a,8,'WAVE');put(a,12,'fmt ');
 v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,2,true);
 v.setUint32(24,48000,true);v.setUint32(28,288000,true);v.setUint16(32,6,true);
 v.setUint16(34,24,true);put(a,36,'data');v.setUint32(40,frames*6,true);
 return a;
}
const s24=(a,i)=>((a[i]|a[i+1]<<8|a[i+2]<<16)<<8)>>8;
const p24=(a,i,x)=>{a[i]=x&255;a[i+1]=(x>>8)&255;a[i+2]=(x>>16)&255};
export function makeSequence(inputs,{clipFrames=144000,gapFrames=48000,fadeFrames=2400}={}){
 if(inputs.length!==3||![clipFrames,gapFrames,fadeFrames].every(Number.isInteger)||clipFrames<2||gapFrames<0||fadeFrames<2||fadeFrames>clipFrames)throw Error('invalid sequence');
 const q=inputs.map(inspect24);
 if(q.some(x=>x.frames<clipFrames))throw Error('source too short');
 const out=header(3*clipFrames+2*gapFrames),dst=out.subarray(44);
 q.forEach((x,k)=>{
  const start=k*(clipFrames+gapFrames)*6;
  dst.set(x.pcm.subarray(0,clipFrames*6),start);
  for(let i=clipFrames-fadeFrames;i<clipFrames;i++){
   const w=.5*(1+Math.cos(Math.PI*(i-(clipFrames-fadeFrames))/(fadeFrames-1)));
   for(let ch=0;ch<2;ch++){const p=start+6*i+3*ch;p24(dst,p,Math.round(s24(dst,p)*w))}
  }
 });
 return out;
}
export function compare(cases){
 if(cases.length!==8)throw Error('expected eight cases');
 const models=['global4','hybridGlobal3','hybridGlobal2','selective4'];
 const out=[];
 for(const midi of [76,127]){
  const group=models.map(model=>{
   const matches=cases.filter(c=>c.case===model&&c.midiVelocity===midi);
   if(matches.length!==1)throw Error('missing/duplicate case');
   return matches[0];
  });
  const ref=group[0];
  for(const c of group){
   if(c.gain!==ref.gain||c.threshold!==ref.threshold||c.duration!==ref.duration||c.clipped!==0||
     c.pair.rate!==48000||c.pair.frames!==c.duration*48000+239||
     c.contextualCrossing.status!=='observed-window'||c.windows.length!==4)throw Error('incomparable case');
   const rms2=c.rms.find(w=>w.startS===2)?.rms,ref2=ref.rms.find(w=>w.startS===2)?.rms;
   if(![rms2,ref2].every(x=>Number.isFinite(x)&&x>0))throw Error('invalid RMS');
   const windows=c.windows.map((w,i)=>{
    const v=ref.windows[i];
    if(w.startS!==v.startS||w.endS!==v.endS||w.binHz!==v.binHz||JSON.stringify(w.analysisBandHz)!==JSON.stringify(v.analysisBandHz))throw Error('incomparable windows');
    for(const t of [w,v])if(!Number.isFinite(t.rmsBand)||t.rmsBand<=0||!Number.isFinite(t.wideOffFraction)||t.wideOffFraction<=0||t.wideOffFraction>1)throw Error('invalid spectrum');
    const offPower=w.rmsBand**2*w.wideOffFraction,refPower=v.rmsBand**2*v.wideOffFraction;
    return {startS:w.startS,endS:w.endS,wideOffFraction:w.wideOffFraction,offPower,relativePower:offPower/refPower,deltaDb:10*Math.log10(offPower/refPower)};
   });
   out.push({case:c.case,midiVelocity:midi,crossingS:c.contextualCrossing.startS,rms2,relativeRms2:rms2/ref2,windows});
  }
 }
 return out;
}
export function selfTest(cases){
 const result=compare(cases);
 const a=result.find(x=>x.case==='hybridGlobal3'&&x.midiVelocity===127);
 if(Math.abs(a.windows[1].relativePower-1.1847341319707323)>1e-10||a.crossingS!==19.5)throw Error('D reference');
 const e=result.find(x=>x.case==='hybridGlobal2'&&x.midiVelocity===76);
 if(Math.abs(e.windows[1].relativePower-2.4022938463496395)>1e-10||e.crossingS!==14)throw Error('E reference');
 const bad=JSON.parse(JSON.stringify(cases));bad[0].gain*=2;
 let rejected=false;try{compare(bad)}catch{rejected=true}if(!rejected)throw Error('gain guard');
 const inputs=[100000,-200000,300000].map(n=>{const x=header(10);for(let i=44;i<x.length;i+=3)p24(x,i,n);return x});
 const q=inspect24(makeSequence(inputs,{clipFrames:8,gapFrames:2,fadeFrames:2}));
 if(q.frames!==28)throw Error('sequence duration');
 for(let k=0;k<3;k++){
  const src=inspect24(inputs[k]).pcm,at=k*10*6;
  for(let j=0;j<7*6;j++)if(q.pcm[at+j]!==src[j])throw Error('PCM changed before fade');
  for(let j=7*6;j<(k===2?8:10)*6;j++)if(q.pcm[at+j]!==0)throw Error('nonzero gap/fade endpoint');
 }
 rejected=false;try{inspect24(new Uint8Array(44))}catch{rejected=true}if(!rejected)throw Error('WAV guard');
 return result;
}
