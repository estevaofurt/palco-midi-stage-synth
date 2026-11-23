/** Stage Synth — offline acoustic measurements, without DSP changes or WAVs. */
export const midiHz = key => 440 * 2 ** ((key - 69) / 12);
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const db=x=>20*Math.log10(Math.max(x,1e-12));

export function rmsWindow(samples,sampleRate,start,end){
  const a=clamp(Math.floor(start*sampleRate),0,samples.length);
  const b=clamp(Math.floor(end*sampleRate),a,samples.length);
  if(b<=a)return null;
  let power=0;
  for(let i=a;i<b;i++){const x=samples[i];if(!Number.isFinite(x))return null;power+=x*x;}
  return Math.sqrt(power/(b-a));
}

/** Hann-window FFT and log-parabolic peak interpolation. */
export function spectrum(samples,sampleRate,start=.18,fftSize=32768){
  if(!Number.isInteger(fftSize)||fftSize<1024||(fftSize&(fftSize-1)))throw new RangeError('fftSize must be power of two >=1024');
  const re=new Float64Array(fftSize),im=new Float64Array(fftSize);
  const offset=Math.floor(start*sampleRate);
  if(offset<0||offset+fftSize>samples.length)throw new RangeError('not enough samples for spectral window');
  for(let i=0;i<fftSize;i++)re[i]=(Number.isFinite(samples[offset+i])?samples[offset+i]:0)*(.5-.5*Math.cos(2*Math.PI*i/(fftSize-1)));
  for(let i=1,j=0;i<fftSize;i++){
    let bit=fftSize>>1;
    for(;j&bit;bit>>=1)j^=bit;
    j^=bit;
    if(i<j){const t=re[i];re[i]=re[j];re[j]=t;}
  }
  for(let len=2;len<=fftSize;len<<=1){
    const angle=-2*Math.PI/len,stepRe=Math.cos(angle),stepIm=Math.sin(angle);
    for(let base=0;base<fftSize;base+=len){
      let wr=1,wi=0;
      for(let k=0;k<len/2;k++){
        const u=base+k,v=u+len/2;
        const tr=wr*re[v]-wi*im[v],ti=wr*im[v]+wi*re[v];
        re[v]=re[u]-tr;im[v]=im[u]-ti;
        re[u]+=tr;im[u]+=ti;
        const next=wr*stepRe-wi*stepIm;
        wi=wr*stepIm+wi*stepRe;wr=next;
      }
    }
  }
  const magnitudes=new Float64Array(fftSize/2+1);
  for(let i=0;i<magnitudes.length;i++)magnitudes[i]=Math.hypot(re[i],im[i]);
  return {sampleRate,fftSize,magnitudes};
}

export function findPartial(spec,targetHz,{relativeWindow=.025,minHz=4}={}){
  const {sampleRate,fftSize,magnitudes:m}=spec;
  const h=sampleRate/fftSize,halfWidth=Math.max(minHz,targetHz*relativeWindow);
  const a=clamp(Math.ceil((targetHz-halfWidth)/h),1,m.length-2);
  const b=clamp(Math.floor((targetHz+halfWidth)/h),a,m.length-2);
  let index=a;for(let k=a+1;k<=b;k++)if(m[k]>m[index])index=k;
  const log=x=>Math.log(Math.max(x,1e-20));
  const y0=log(m[index-1]),y1=log(m[index]),y2=log(m[index+1]);
  const denom=y0-2*y1+y2;
  const shift=Math.abs(denom)>1e-15?clamp(.5*(y0-y2)/denom,-.5,.5):0;
  const frequency=(index+shift)*h;
  return {frequency,amplitude:m[index],cents:1200*Math.log2(frequency/targetHz)};
}

/** Hann-weighted single-frequency amplitude (not an FFT-bin amplitude). */
export function partialAmplitude(samples,sampleRate,frequency,start,end){
  const a=clamp(Math.floor(start*sampleRate),0,samples.length);
  const b=clamp(Math.floor(end*sampleRate),a,samples.length);
  const count=b-a;if(count<32||!(frequency>0))return null;
  const w=2*Math.PI*frequency/sampleRate,cw=Math.cos(w),sw=Math.sin(w);
  let c=1,s=0,x=0,y=0,weightSum=0;
  for(let i=0;i<count;i++){
    const weight=.5-.5*Math.cos(2*Math.PI*i/(count-1));
    const v=(Number.isFinite(samples[a+i])?samples[a+i]:0)*weight;
    x+=v*c;y+=v*s;weightSum+=weight;
    const nc=c*cw-s*sw;s=c*sw+s*cw;c=nc;
  }
  return 2*Math.hypot(x,y)/weightSum;
}

export function measurePianoNote(samples,{sampleRate=48000,key=60,fftSize=32768,maxPartial=8}={}){
  if(!(samples instanceof Float32Array||samples instanceof Float64Array))throw new TypeError('samples must be Float32Array or Float64Array');
  if(samples.length<Math.ceil(1.6*sampleRate))throw new RangeError('minimum 1.6 seconds required');
  let peak=0,nonFinite=0,clipped=0,total=0;
  for(const x of samples){
    if(!Number.isFinite(x)){nonFinite++;continue;}
    peak=Math.max(peak,Math.abs(x));if(Math.abs(x)>=1)clipped++;total+=x*x;
  }
  const windows={
    attack0_20:rmsWindow(samples,sampleRate,0,.02),
    attack20_80:rmsWindow(samples,sampleRate,.02,.08),
    attack80_250:rmsWindow(samples,sampleRate,.08,.25),
    early:rmsWindow(samples,sampleRate,.25,.45),
    late:rmsWindow(samples,sampleRate,.8,1),
    tail:rmsWindow(samples,sampleRate,1.4,1.6)
  };
  const f0=midiHz(key),spec=spectrum(samples,sampleRate,.18,fftSize);
  const fundamental=findPartial(spec,f0),harmonics=[];
  for(let n=1;n<=maxPartial;n++){
    const target=n*f0;if(target>sampleRate*.43)break;
    const p=findPartial(spec,target);
    const reliable=fundamental.amplitude>1e-12&&p.amplitude>=fundamental.amplitude*.0316;
    const early=partialAmplitude(samples,sampleRate,p.frequency,.16,.30);
    const middle=partialAmplitude(samples,sampleRate,p.frequency,.52,.70);
    const late=partialAmplitude(samples,sampleRate,p.frequency,1.12,1.30);
    const r=(p.frequency/(n*fundamental.frequency))**2;
    const bEstimate=n>1&&reliable&&r<n*n?(r-1)/(n*n-r):null;
    harmonics.push({
      n,expectedHz:target,measuredHz:reliable?p.frequency:null,cents:reliable?p.cents:null,
      relativeDb:fundamental.amplitude>1e-12?db(p.amplitude/fundamental.amplitude):null,
      bEstimate,earlyDb:early==null?null:db(early),
      middleDb:middle==null?null:db(middle),lateDb:late==null?null:db(late)
    });
  }
  const values=harmonics.filter(p=>p.n>=2&&p.bEstimate!=null&&p.bEstimate>=0&&Number.isFinite(p.bEstimate)).map(p=>p.bEstimate).sort((a,b)=>a-b);
  const decayDb=(a,b)=>a>0&&b>0?db(b/a):null;
  return {key,f0,sampleRate,peak,clipped,nonFinite,rms:Math.sqrt(total/samples.length),windows,
    earlyDecayDb:decayDb(windows.attack80_250,windows.early),
    lateDecayDb:decayDb(windows.late,windows.tail),
    bMedian:values.length?values[Math.floor(values.length/2)]:null,
    bSampleCount:values.length,harmonics};
}
