/**
 * Stage D bass-only research components, original implementation.
 *
 * The existing D synthesizes transverse modes but radiates their output almost
 * directly. This file tests TWO INDEPENDENT missing mechanisms:
 *  1) a broad, lossy shared bridge/soundboard radiation path (not a reverb);
 *  2) second-order, quadratically excited longitudinal-like modes (not simple
 *     octave doubling, and not measured longitudinal frequencies).
 *
 * Modal frequencies and weights are ILLUSTRATIVE, NOT an identified spruce
 * plate / bridge admittance or an actual piano string impedance. The purpose
 * is listening A/B and controlled measurements BEFORE release.
 * No sample assets, IRs or code from third parties.
 */
const PI2=Math.PI*2;
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const hz=k=>440*2**((k-69)/12);

// Lower modes more persistent, higher modes progressively more lossy.
// The bridge and ribs create many distributed overlapping plate modes; this
// tiny set is a reduced phenomenological *radiation* approximation.
export const BOARD_BANDS=Object.freeze([
  [86,.22,.32,-.35],
  [139,.17,.28,.31],
  [213,.145,.23,-.26],
  [324,.119,.23,.27],
  [455,.091,.18,-.18],
  [611,.074,.18,.23],
  [842,.065,.16,-.19],
  [1169,.054,.15,.20],
  [1550,.047,.12,-.23],
  [1955,.039,.10,.22],
  [2521,.032,.09,-.19],
  [3280,.028,.07,.15]
]);

export class PianoBassWoodRadiator{
  constructor(sampleRate=48000){
    if(!Number.isFinite(sampleRate)||sampleRate<22050)throw new RangeError('sampleRate');
    this.sr=sampleRate;this.divisor=4;this.rate=sampleRate/4;
    const n=BOARD_BANDS.length;
    this.y1=new Float64Array(n);this.y2=new Float64Array(n);
    this.coef=new Float64Array(n);this.r2=new Float64Array(n);
    this.g=new Float64Array(n);this.pan=new Float64Array(n);
    for(let i=0;i<n;i++){
      const [f,decay,gain,pan]=BOARD_BANDS[i];
      if(f>=this.rate*.43)throw new RangeError('wood mode is aliased');
      const w=PI2*f/this.rate,r=Math.exp(-1/(decay*this.rate));
      this.coef[i]=2*r*Math.cos(w);this.r2[i]=r*r;
      this.g[i]=Math.sin(w)*(1-r)*gain*2.5;
      this.pan[i]=pan;
    }
    this.tick=0;this.acc=0;this.strike=0;
    this.pre1=0;this.pre2=0;this.pre3=0;this.pre4=0;this.low=0;
    this.left=0;this.right=0;
    this.outputL=0;this.outputR=0;
  }
  // Small non-tonal plate impact independent of decay of the main string.
  noteOn(key,speed){
    if(key>48||key<21)return;
    const energy=clamp(speed,0,1)**1.7;
    this.strike+=.0022*energy;
  }
  step(inputL,inputR){
    // This is only a PROXY for bridge drive because D's current dry sum is not
    // a calibrated force or velocity. Do NOT close a mechanical feedback loop
    // using this signal; that would silently create energy.
    const x=(inputL+inputR)*.5;
    // Cascaded input low-passes strongly reduce folding above the 6 kHz
    // Nyquist of the 12 kHz board model. This is a *proxy* for bridge drive.
    // Reject the previous high-pass-before-decimation, which would alias
    // some string overtones into false wooden resonances.
    this.pre1+=.30*(x-this.pre1);
    this.pre2+=.30*(this.pre1-this.pre2);
    this.pre3+=.30*(this.pre2-this.pre3);
    this.pre4+=.30*(this.pre3-this.pre4);
    this.low+=.024*(this.pre4-this.low);
    this.acc+=(this.pre4-.38*this.low);
    if(++this.tick===this.divisor){
      const drive=this.acc/this.divisor+this.strike;
      this.tick=0;this.acc=0;this.strike*=.49;
      let l=0,r=0;
      for(let i=0;i<this.y1.length;i++){
        const y=this.coef[i]*this.y1[i]-this.r2[i]*this.y2[i]+this.g[i]*drive;
        this.y2[i]=this.y1[i];this.y1[i]=y;
        l+=y*(1-.35*this.pan[i]);
        r+=y*(1+.35*this.pan[i]);
      }
      this.left=l;this.right=r;
    }
    // Interpolate decimated radiator output without block-rate zipper noise.
    this.outputL+=(this.left-this.outputL)*.31;
    this.outputR+=(this.right-this.outputR)*.31;
  }
}

// Two resonances representing free longitudinal motion; quadratic input
// produces both sum/difference ("phantom") frequencies of the transverse modes.
// Frequencies are heuristic until the component can be calibrated with physics
// or isolated longitudinal-mode recordings.
export class PianoBassLongitudinal{
  constructor(sr=48000){
    this.sr=sr;this.y1=new Float64Array(2);this.y2=new Float64Array(2);
    this.c=new Float64Array(2);this.r2=new Float64Array(2);
    this.g=new Float64Array(2);
    this.avg=0;this.prev=0;this.active=false;this.gain=0;
  }
  reset(key,speed){
    this.y1.fill(0);this.y2.fill(0);
    this.avg=0;this.prev=0;
    this.active=key>=21&&key<=48;
    // A lightweight illustrative scale-length trend; this is NOT a measured
    // longitudinal wave speed / piano string speaking length.
    const f=clamp(1400+49*(key-36),730,2150);
    for(let i=0;i<2;i++){
      const freq=f*(i+1),w=PI2*freq/this.sr;
      const r=Math.exp(-1/(this.sr*(i===0?.058:.034)));
      this.c[i]=2*r*Math.cos(w);this.r2[i]=r*r;
      this.g[i]=Math.sin(w)*(1-r)*(i===0?125:50);
    }
    this.gain=.9*clamp(speed,0,1)**.65;
  }
  step(transverse,hammerForce=0){
    if(!this.active)return 0;
    // Distortion is on the INTERNAL modal state, not global output.
    // Remove DC/even low-frequency power before the longitudinal bank.
    const squared=transverse*transverse;
    this.avg+=.005*(squared-this.avg);
    const src=(squared-this.avg)+hammerForce*.020;
    let out=0;
    for(let i=0;i<2;i++){
      const y=this.c[i]*this.y1[i]-this.r2[i]*this.y2[i]+this.g[i]*src;
      this.y2[i]=this.y1[i];this.y1[i]=y;
      out+=y*(i===0?1:.46);
    }
    this.prev=transverse;
    return out*this.gain;
  }
}
