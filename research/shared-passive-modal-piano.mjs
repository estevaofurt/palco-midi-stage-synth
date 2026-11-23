/**
 * E2.3 — multi-partial strings coupled through ONE passive shared bridge.
 * RESEARCH ONLY: frequencies/losses are illustrative, no measured hammer,
 * soundboard mobility, airborne pressure, AudioWorklet integration or PCM.
 *
 * Each key has two transverse coordinates for each retained partial.
 * A0..C4: up to 5 partials; C#4..C8: up to 2 partials. All string coordinates
 * couple by springs to the same 2-coordinate bridge/board system, so a
 * struck harmonic transfers energy to other strings; it is NOT a dry sum
 * of oscillators plus wet body audio. O(N) Schur solve per sample.
 *
 * M positive; C>=0 including dampers; K positive from ground springs and
 * positive coupling springs. Implicit midpoint energy identity:
 * E_after - E_before = externalWork - dissipated, within FP roundoff.
 *
 * Generalized velocities are NOT air pressure or calibrated acoustic output.
 */
const TWOPI=2*Math.PI;
const midiHz=k=>440*2**((k-69)/12);
export class SharedPassiveModalPiano {
 constructor({sampleRate=48000,coupling=.12,partialsBass=5,partialsTreble=2,
              releaseDamping=110,inharmonicity=.00010,maxContactMs=12,
              externalForceMode=false}={}){
  if(!Number.isFinite(sampleRate)||sampleRate<22050||sampleRate>192000||
     !Number.isFinite(coupling)||coupling<0||coupling>1||
     !Number.isInteger(partialsBass)||partialsBass<1||partialsBass>8||
     !Number.isInteger(partialsTreble)||partialsTreble<1||partialsTreble>8||
     !Number.isFinite(releaseDamping)||releaseDamping<0||releaseDamping>400||
     !Number.isFinite(inharmonicity)||inharmonicity<0||inharmonicity>.003||
     !Number.isFinite(maxContactMs)||maxContactMs<=0||maxContactMs>25||
     typeof externalForceMode!=='boolean')
   throw new RangeError('invalid passive modal configuration');
  this.sampleRate=sampleRate;this.dt=1/sampleRate;
  this.externalForceMode=externalForceMode;
  this.keyStart=new Uint16Array(89);
  const keyOf=[],partialOf=[],polarOf=[],frequency=[];
  for(let key=21;key<=108;key++){
   this.keyStart[key-21]=frequency.length;
   const f0=midiHz(key);
   const B=inharmonicity*(1+.35*((key-64)/44)**2);
   const count=key<=60?partialsBass:partialsTreble;
   for(let partial=1;partial<=count;partial++){
    // f(n)/f(1) = n sqrt((1+B n²)/(1+B)), preserving f0.
    const f=f0*partial*Math.sqrt((1+B*partial*partial)/(1+B));
    if(f>=sampleRate*.42)break;
    for(let pol=0;pol<2;pol++){
     keyOf.push(key-21);partialOf.push(partial);polarOf.push(pol);
     frequency.push(f*(pol?1.0009:1));
    }
   }
  }
  this.keyStart[88]=frequency.length;
  this.n=frequency.length;
  if(!this.n)throw new RangeError('no modes under Nyquist');
  this.keyIndex=Uint8Array.from(keyOf);
  this.partialIndex=Uint8Array.from(partialOf);
  this.polarization=Uint8Array.from(polarOf);
  this.frequency=Float64Array.from(frequency);
  const n=this.n,h=this.dt;
  this.x=new Float64Array(n);this.v=new Float64Array(n);
  this.rhs=new Float64Array(n);this.mass=new Float64Array(n);
  this.ground=new Float64Array(n);this.coupling=new Float64Array(n);
  this.damping=new Float64Array(n);this.openDamping=new Float64Array(n);
  this.aInverse=new Float64Array(n);this.offDiagonal=new Float64Array(n);
  this.forces=new Float64Array(n);this.strikeWeights=new Float64Array(n);
  this.bx=new Float64Array(2);this.bv=new Float64Array(2);
  this.bmass=new Float64Array([4.2,2.3]);
  this.bdamper=new Float64Array([4.2*24,2.3*32]);
  this.bground=new Float64Array([4.2*(TWOPI*95)**2,2.3*(TWOPI*163)**2]);
  this.boardSpring=.15*(TWOPI*95)**2;
  this.held=new Uint8Array(88);this.pedal=0;
  this.releaseDamping=releaseDamping;
  this.remaining=new Int32Array(88);this.duration=new Int32Array(88);
  this.progress=new Int32Array(88);this.amplitude=new Float64Array(88);
  this.activeContacts=0;
  this.maxContactSamples=Math.ceil(sampleRate*maxContactMs/1000);
  let sumK=0;
  for(let i=0;i<n;i++){
   const key=keyOf[i]+21,partial=partialOf[i],pol=polarOf[i];
   const f=this.frequency[i],w=TWOPI*f;
   const m=(pol?1.1:1)/(partial**1.1);
   this.mass[i]=m;
   this.ground[i]=m*w*w;
   this.openDamping[i]=2*m*(pol?.14:.5)*(1+.12*(partial-1));
   // Use f0 rather than partial frequency for bounded modal bridge loading.
   // Coefficients are positive to ensure passivity, NOT identified mobilities.
   const f0=midiHz(key),scale=partial**-1.5;
   const kc=coupling*m*(TWOPI*f0)**2*(pol?.012:.018)*scale;
   this.coupling[i]=kc;sumK+=kc;
   const position=Math.sin(Math.PI*partial*.13);
   this.strikeWeights[i]=position*(pol?.35:.65)/partial**.7;
  }
  this.sumK=sumK;
  this.S01=-.25*h*h*this.boardSpring;
  this.S11=this.bmass[1]+.5*h*this.bdamper[1]+
    .25*h*h*(this.bground[1]+this.boardSpring);
  this.S00=0;this.determinant=0;
  this.bridgeVelocity=0;this.boardVelocity=0;this.boardPanelVelocity=0;
  this.externalWork=0;this.dissipated=0;this.samples=0;
  this.updateDampers();
 }
 updateDampers(){
  const h=this.dt,pedalDown=this.pedal>=64;
  let schur=0;
  for(let i=0;i<this.n;i++){
   const key=this.keyIndex[i];
   const open=key>=70||pedalDown||this.held[key]>0;
   const mass=this.mass[i],kc=this.coupling[i];
   const d=this.openDamping[i]+(open?0:2*mass*this.releaseDamping);
   this.damping[i]=d;
   const a=mass+.5*h*d+.25*h*h*(this.ground[i]+kc);
   this.aInverse[i]=1/a;
   const s=-.25*h*h*kc;
   this.offDiagonal[i]=s;
   schur+=s*s/a;
  }
  this.S00=this.bmass[0]+.5*h*this.bdamper[0]+
    .25*h*h*(this.bground[0]+this.boardSpring+this.sumK)-schur;
  this.determinant=this.S00*this.S11-this.S01*this.S01;
  if(!(this.S00>0&&this.determinant>0&&Number.isFinite(this.determinant)))
   throw new RangeError('nonpassive modal bridge');
 }
 noteOn(key,{velocity=80,peakForce=50,contactMs=3}={}){
  if(!Number.isInteger(key)||key<21||key>108||
     !Number.isFinite(velocity)||velocity<1||velocity>127||
     !Number.isFinite(peakForce)||peakForce<0||peakForce>1e5||
     !Number.isFinite(contactMs)||contactMs<=0)
   throw new RangeError('invalid strike');
  if(this.externalForceMode)
   throw new RangeError('use external modal forces and explicit damper control');
  const duration=Math.max(2,Math.round(contactMs*this.sampleRate/1000));
  if(duration>this.maxContactSamples)throw new RangeError('contact too long');
  const k=key-21;
  if(this.held[k]<255)this.held[k]++;
  this.updateDampers();
  if(this.remaining[k]===0)this.activeContacts++;
  this.remaining[k]=duration;this.duration[k]=duration;
  this.progress[k]=0;this.amplitude[k]=peakForce*(velocity/127)**1.5;
 }
 noteOff(key){
  if(!Number.isInteger(key)||key<21||key>108)throw new RangeError('invalid MIDI key');
  const k=key-21;if(this.held[k])this.held[k]--;
  this.updateDampers();
 }
 setSustain(cc){
  if(!Number.isFinite(cc)||cc<0||cc>127)throw new RangeError('invalid CC64');
  this.pedal=cc;this.updateDampers();
 }
 step(){
  // Apply the same hammer pulse to the physical partial degrees of freedom,
  // with position-dependent force projections. No post-synthesis harmonic sum.
  const force=this.forces;
  if(!this.externalForceMode)for(let k=0;k<88;k++){
   let f=0;
   if(this.remaining[k]>0){
    const phase=(this.progress[k]+.5)/this.duration[k];
    const sine=Math.sin(Math.PI*phase);
    f=this.amplitude[k]*sine*sine;
    this.progress[k]++;
    if(--this.remaining[k]===0)this.activeContacts--;
   }
   for(let i=this.keyStart[k];i<this.keyStart[k+1];i++)
    force[i]=f*this.strikeWeights[i];
  }
  const h=this.dt,n=this.n,x=this.x,v=this.v,
    rhs=this.rhs,inv=this.aInverse,s=this.offDiagonal;
  const xb=this.bx,bv=this.bv;
  let bridgeStiff=this.sumK*xb[0],schurRhs=0,diss=0,work=0;
  for(let i=0;i<n;i++){
   bridgeStiff-=this.coupling[i]*x[i];
   const kx=(this.ground[i]+this.coupling[i])*x[i]-this.coupling[i]*xb[0];
   const ri=this.mass[i]*v[i]-.5*h*kx+.5*h*force[i];
   rhs[i]=ri;
   schurRhs+=s[i]*ri*inv[i];
  }
  const rhsBoard0=this.bmass[0]*bv[0]-
    .5*h*(bridgeStiff+(this.bground[0]+this.boardSpring)*xb[0]-
      this.boardSpring*xb[1])-schurRhs;
  const rhsBoard1=this.bmass[1]*bv[1]-
    .5*h*((this.bground[1]+this.boardSpring)*xb[1]-
      this.boardSpring*xb[0]);
  const vm0=(rhsBoard0*this.S11-this.S01*rhsBoard1)/this.determinant;
  const vm1=(this.S00*rhsBoard1-this.S01*rhsBoard0)/this.determinant;
  for(let i=0;i<n;i++){
   const vi=(rhs[i]-s[i]*vm0)*inv[i];
   x[i]+=h*vi;v[i]=2*vi-v[i];
   diss+=this.damping[i]*vi*vi;
   work+=force[i]*vi;
  }
  xb[0]+=h*vm0;xb[1]+=h*vm1;
  bv[0]=2*vm0-bv[0];bv[1]=2*vm1-bv[1];
  diss+=this.bdamper[0]*vm0*vm0+this.bdamper[1]*vm1*vm1;
  this.externalWork+=h*work;this.dissipated+=h*diss;
  this.bridgeVelocity=vm0;
  this.boardPanelVelocity=vm1; // E2.9: second passive midpoint mode, no new force/energy
  this.boardVelocity=.67*vm0+.33*vm1;
  this.samples++;
  return this.boardVelocity;
 }
 render(output,offset=0,length=output.length-offset){
  if(!(output instanceof Float32Array||output instanceof Float64Array)||
     !Number.isInteger(offset)||!Number.isInteger(length)||
     offset<0||length<0||offset+length>output.length)
   throw new RangeError('invalid mechanical output buffer');
  for(let i=0;i<length;i++)output[offset+i]=this.step();
 }
 energy(){
  let energy=0;
  const x0=this.bx[0];
  for(let i=0;i<this.n;i++){
   const x=this.x[i],v=this.v[i],delta=x-x0;
   energy+=.5*(this.mass[i]*v*v+this.ground[i]*x*x+
                  this.coupling[i]*delta*delta);
  }
  for(let i=0;i<2;i++)
   energy+=.5*(this.bmass[i]*this.bv[i]**2+
               this.bground[i]*this.bx[i]**2);
  energy+=.5*this.boardSpring*(this.bx[0]-this.bx[1])**2;
  return energy;
 }
 energyBalanceError(){return this.energy()-(this.externalWork-this.dissipated)}
 reset(){
  this.x.fill(0);this.v.fill(0);this.rhs.fill(0);this.forces.fill(0);
  this.bx.fill(0);this.bv.fill(0);
  this.held.fill(0);this.pedal=0;
  this.remaining.fill(0);this.duration.fill(0);
  this.progress.fill(0);this.amplitude.fill(0);
  this.activeContacts=0;this.samples=0;
  this.externalWork=0;this.dissipated=0;
  this.bridgeVelocity=0;this.boardVelocity=0;this.boardPanelVelocity=0;
  this.updateDampers();
 }
}
