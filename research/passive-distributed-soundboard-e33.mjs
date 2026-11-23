/**
 * E3.3 RESEARCH: passive 88-key strings + one local bridge DOF + eight
 * spatial soundboard modes. Not a finished or calibrated acoustic piano.
 *
 * Unlike E2.9/E3.0, only panel coordinates are candidate radiating surfaces.
 * The local bridge velocity is NEVER interpreted as a moving soundboard area.
 * String springs connect to one shared bridge point. The bridge connects to
 * the distributed plate evaluated at the bridge position u,v:
 *
 * V_bridge-panel = .5*k*(x_bridge - Σ phi_j(u,v)*q_j)^2
 * phi_j(u,v)=sin(mxπu)sin(nyπv), strictly derived, not a PCM filter.
 *
 * This maintains positive semidefinite spring coupling. Implicit midpoint
 * integration solves an 88-key O(n) string Schur complement followed by a
 * tiny SPD Cholesky system over 1+numberOfPlateModes DOFs. Energy identity:
 * E_new-E_old = Σ F_i Δx_i - h Σ damping_i v_mid_i².
 *
 * The old test pulse is opt-in default only for proving the board topology;
 * externalForceMode:true explicitly disables it for eventual E3.2 reactive
 * hammer contact. Geometry, masses, frequencies and acoustic radiation remain
 * hypothetical; there is NO measured piano validation / worklet approval.
 */
const TAU=2*Math.PI;
const hz=k=>440*2**((k-69)/12);
const MODE_SHAPES=Object.freeze([
 [1,1],[2,1],[1,2],[2,2],[3,1],[1,3],[3,2],[2,3],
 // E3.4 additional spatial bending modes; no synthetic impact mixed at output.
 [4,1],[3,3],[5,1],[1,4],[2,4],[4,4],[1,5],[1,6]
]);
const MODE_FREQUENCIES=Object.freeze([95,163,214,286,355,424,510,610]);
const isFiniteIn=(v,low,high)=>Number.isFinite(v)&&v>=low&&v<=high;
export class PassiveDistributedSoundboardE33 {
 constructor({
  sampleRate=48000,partialsBass=5,partialsTreble=2,
  inharmonicity=.00010,coupling=.12,releaseDamping=110,
  panelModes=8,bridgeU=.78,bridgeV=.37,
  bridgePanelSpring=53000,externalForceMode=false
 }={}){
  if(!Number.isInteger(sampleRate)||sampleRate<22050||sampleRate>96000||
     !Number.isInteger(partialsBass)||partialsBass<1||partialsBass>8||
     !Number.isInteger(partialsTreble)||partialsTreble<1||partialsTreble>8||
     !Number.isInteger(panelModes)||panelModes<2||panelModes>16||
     !isFiniteIn(inharmonicity,0,.003)||!isFiniteIn(coupling,0,1)||
     !isFiniteIn(releaseDamping,0,400)||
     !isFiniteIn(bridgeU,.05,.95)||!isFiniteIn(bridgeV,.05,.95)||
     !isFiniteIn(bridgePanelSpring,1,1e7)||
     typeof externalForceMode!=='boolean')
    throw new RangeError('invalid distributed plate physics');
  this.sampleRate=sampleRate;this.dt=1/sampleRate;
  this.panelModes=panelModes;this.boardSize=panelModes+1;
  this.externalForceMode=externalForceMode;
  this.keyStart=new Uint16Array(89);
  const keyIndices=[],partIndices=[],polIndices=[],frequencies=[];
  for(let key=21;key<=108;key++){
   this.keyStart[key-21]=frequencies.length;
   const f0=hz(key),B=inharmonicity*(1+.35*((key-64)/44)**2);
   const count=key<=60?partialsBass:partialsTreble;
   for(let partial=1;partial<=count;partial++){
    const f=f0*partial*Math.sqrt((1+B*partial*partial)/(1+B));
    if(f>=sampleRate*.42)break;
    for(let pol=0;pol<2;pol++){
     keyIndices.push(key-21);partIndices.push(partial);polIndices.push(pol);
     frequencies.push(f*(pol?1.0009:1));
    }
   }
  }
  this.keyStart[88]=frequencies.length;
  this.n=frequencies.length;
  this.keyIndex=Uint8Array.from(keyIndices);
  this.x=new Float64Array(this.n);this.v=new Float64Array(this.n);
  this.mass=new Float64Array(this.n);this.ground=new Float64Array(this.n);
  this.coupling=new Float64Array(this.n);this.damping=new Float64Array(this.n);
  this.openDamping=new Float64Array(this.n);
  this.aInverse=new Float64Array(this.n);this.offDiagonal=new Float64Array(this.n);
  this.rhs=new Float64Array(this.n);this.forces=new Float64Array(this.n);
  this.strikeWeights=new Float64Array(this.n);
  this.held=new Uint8Array(88);this.pedal=0;this.releaseDamping=releaseDamping;
  this.remaining=new Int32Array(88);this.duration=new Int32Array(88);
  this.progress=new Int32Array(88);this.amplitude=new Float64Array(88);
  this.bridgeX=0;this.bridgeV=0;this.bridgeMass=4.2;
  this.bridgeDamper=4.2*24;
  this.bridgeGround=4.2*(TAU*95)**2;
  this.bridgePanelSpring=bridgePanelSpring;
  this.panelX=new Float64Array(panelModes);
  this.panelV=new Float64Array(panelModes);
  this.panelVelocity=new Float64Array(panelModes);
  this.panelMass=new Float64Array(panelModes);
  this.panelGround=new Float64Array(panelModes);
  this.panelDamper=new Float64Array(panelModes);
  this.panelShapeAtBridge=new Float64Array(panelModes);
  this.panelShapes=MODE_SHAPES.slice(0,panelModes);
  // Preserve all E3.3 (2..8) frequencies exactly. Additional candidate
  // modes use ideal simply-supported thin-plate dispersion, anchored at
  // 95 Hz for (1,1). This is NOT a calibrated spruce soundboard.
  const ref=(1/1.22)**2+(1/.92)**2;
  const plateScale=95/ref;
  this.panelFrequencies=this.panelShapes.map(([mx,my],i)=>
   i<MODE_FREQUENCIES.length?MODE_FREQUENCIES[i]:
   plateScale*((mx/1.22)**2+(my/.92)**2));
  for(let i=0;i<panelModes;i++){
   const [mx,my]=this.panelShapes[i];
   const f=this.panelFrequencies[i],mass=2.1/(1+.15*i);
   this.panelShapeAtBridge[i]=Math.sin(Math.PI*mx*bridgeU)*
    Math.sin(Math.PI*my*bridgeV);
   this.panelMass[i]=mass;
   this.panelGround[i]=mass*(TAU*f)**2;
   this.panelDamper[i]=2*mass*(TAU*f)*(.015+.002*i);
  }
  this.boardMatrix=new Float64Array(this.boardSize**2);
  this.cholesky=new Float64Array(this.boardSize**2);
  this.boardRhs=new Float64Array(this.boardSize);
  this.boardMidV=new Float64Array(this.boardSize);
  this.solveTemp=new Float64Array(this.boardSize);
  let sumK=0;
  for(let i=0;i<this.n;i++){
   const key=keyIndices[i]+21,partial=partIndices[i],pol=polIndices[i];
   const f=frequencies[i],m=(pol?1.1:1)/partial**1.1;
   this.mass[i]=m;this.ground[i]=m*(TAU*f)**2;
   this.openDamping[i]=2*m*(pol?.14:.5)*(1+.12*(partial-1));
   const ks=coupling*m*(TAU*hz(key))**2*
     (pol?.012:.018)*partial**-1.5;
   this.coupling[i]=ks;sumK+=ks;
   this.strikeWeights[i]=Math.sin(Math.PI*partial*.13)*
     (pol?.35:.65)/partial**.7;
  }
  this.sumK=sumK;
  this.externalWork=0;this.dissipated=0;this.samples=0;
  this.updateDampers();
 }
 updateDampers(){
  const h=this.dt,sz=this.boardSize,M=this.panelModes;
  const A=this.boardMatrix,L=this.cholesky;
  A.fill(0);L.fill(0);
  let schur=0;
  for(let i=0;i<this.n;i++){
   const key=this.keyIndex[i],open=key>=70||
      this.pedal>=64||this.held[key]!==0;
   const m=this.mass[i],ks=this.coupling[i];
   const c=this.openDamping[i]+(open?0:2*m*this.releaseDamping);
   this.damping[i]=c;
   const ai=m+.5*h*c+.25*h*h*(this.ground[i]+ks);
   const si=-.25*h*h*ks;
   this.aInverse[i]=1/ai;
   this.offDiagonal[i]=si;
   schur+=si*si/ai;
  }
  A[0]=this.bridgeMass+.5*h*this.bridgeDamper+
   .25*h*h*(this.bridgeGround+this.sumK+this.bridgePanelSpring)-schur;
  for(let j=0;j<M;j++){
   const k=j+1,phi=this.panelShapeAtBridge[j];
   const cross=-.25*h*h*this.bridgePanelSpring*phi;
   A[k]=cross;A[k*sz]=cross;
   for(let l=0;l<M;l++){
    const b=l+1;
    A[k*sz+b]=.25*h*h*this.bridgePanelSpring*
       phi*this.panelShapeAtBridge[l];
   }
   A[k*sz+k]+=this.panelMass[j]+.5*h*this.panelDamper[j]+
     .25*h*h*this.panelGround[j];
  }
  // Cholesky A = LL^T, strictly positive definite.
  for(let i=0;i<sz;i++)for(let j=0;j<=i;j++){
   let x=A[i*sz+j];
   for(let k=0;k<j;k++)x-=L[i*sz+k]*L[j*sz+k];
   if(i===j){
    if(!(x>0&&Number.isFinite(x)))throw new RangeError('nonpassive plate');
    L[i*sz+j]=Math.sqrt(x);
   }else L[i*sz+j]=x/L[j*sz+j];
  }
 }
 solveBoard(){
  const n=this.boardSize,L=this.cholesky,rhs=this.boardRhs,
      t=this.solveTemp,z=this.boardMidV;
  for(let i=0;i<n;i++){
   let v=rhs[i];
   for(let k=0;k<i;k++)v-=L[i*n+k]*t[k];
   t[i]=v/L[i*n+i];
  }
  for(let i=n-1;i>=0;i--){
   let v=t[i];
   for(let k=i+1;k<n;k++)v-=L[k*n+i]*z[k];
   z[i]=v/L[i*n+i];
  }
 }
 noteOn(key,{velocity=80,peakForce=105,contactMs=3}={}){
  if(this.externalForceMode)throw new RangeError('externally driven only');
  if(!Number.isInteger(key)||key<21||key>108||
     !isFiniteIn(velocity,1,127)||!isFiniteIn(peakForce,0,1e5)||
     !isFiniteIn(contactMs,.1,20))
   throw new RangeError('invalid plate key strike');
  const k=key-21;
  this.held[k]=Math.min(255,this.held[k]+1);
  this.updateDampers();
  const duration=Math.max(2,Math.round(contactMs*this.sampleRate/1000));
  this.remaining[k]=duration;this.duration[k]=duration;this.progress[k]=0;
  this.amplitude[k]=peakForce*(velocity/127)**1.5;
 }
 noteOff(key){
  if(!Number.isInteger(key)||key<21||key>108)
   throw new RangeError('invalid MIDI key');
  const k=key-21;if(this.held[k])this.held[k]--;
  this.updateDampers();
 }
 setSustain(cc){
  if(!isFiniteIn(cc,0,127))throw new RangeError('invalid CC64');
  this.pedal=cc;this.updateDampers();
 }
 step(){
  const h=this.dt,n=this.n,M=this.panelModes,w=this.strikeWeights;
  const forces=this.forces;
  if(!this.externalForceMode)for(let k=0;k<88;k++){
   let F=0;
   if(this.remaining[k]){
    const s=Math.sin(Math.PI*(this.progress[k]+.5)/this.duration[k]);
    F=this.amplitude[k]*s*s;
    this.progress[k]++;this.remaining[k]--;
   }
   for(let i=this.keyStart[k];i<this.keyStart[k+1];i++)
    forces[i]=F*w[i];
  }
  const xb=this.bridgeX;
  let springForce=this.bridgeGround*xb+
    this.sumK*xb,schurRhs=0;
  for(let i=0;i<n;i++){
   springForce-=this.coupling[i]*this.x[i];
   const kx=(this.ground[i]+this.coupling[i])*this.x[i]-
       this.coupling[i]*xb;
   const ri=this.mass[i]*this.v[i]-.5*h*kx+.5*h*forces[i];
   this.rhs[i]=ri;
   schurRhs+=this.offDiagonal[i]*ri*this.aInverse[i];
  }
  let plateDisplacementAtBridge=0;
  for(let j=0;j<M;j++)plateDisplacementAtBridge+=
    this.panelShapeAtBridge[j]*this.panelX[j];
  const mismatch=xb-plateDisplacementAtBridge;
  springForce+=this.bridgePanelSpring*mismatch;
  this.boardRhs[0]=this.bridgeMass*this.bridgeV-
    .5*h*springForce-schurRhs;
  for(let j=0;j<M;j++)
   this.boardRhs[j+1]=this.panelMass[j]*this.panelV[j]-
    .5*h*(this.panelGround[j]*this.panelX[j]-
       this.bridgePanelSpring*this.panelShapeAtBridge[j]*mismatch);
  this.solveBoard();
  const vm0=this.boardMidV[0];
  let work=0,diss=this.bridgeDamper*vm0*vm0;
  for(let i=0;i<n;i++){
   const vm=(this.rhs[i]-this.offDiagonal[i]*vm0)*this.aInverse[i];
   this.x[i]+=h*vm;this.v[i]=2*vm-this.v[i];
   work+=forces[i]*vm;
   diss+=this.damping[i]*vm*vm;
  }
  this.bridgeX+=h*vm0;this.bridgeV=2*vm0-this.bridgeV;
  for(let j=0;j<M;j++){
   const vm=this.boardMidV[j+1];
   this.panelX[j]+=h*vm;this.panelV[j]=2*vm-this.panelV[j];
   this.panelVelocity[j]=vm;
   diss+=this.panelDamper[j]*vm*vm;
  }
  this.externalWork+=h*work;this.dissipated+=h*diss;this.samples++;
  if(!Number.isFinite(vm0)||!Number.isFinite(this.externalWork))
   throw new RangeError('nonfinite multimode response');
  return this.panelVelocity;
 }
 energy(){
  let e=0;
  for(let i=0;i<this.n;i++){
   const dx=this.x[i]-this.bridgeX;
   e+=.5*(this.mass[i]*this.v[i]**2+
    this.ground[i]*this.x[i]**2+this.coupling[i]*dx*dx);
  }
  e+=.5*(this.bridgeMass*this.bridgeV**2+
        this.bridgeGround*this.bridgeX**2);
  let plateAtBridge=0;
  for(let j=0;j<this.panelModes;j++){
   e+=.5*(this.panelMass[j]*this.panelV[j]**2+
          this.panelGround[j]*this.panelX[j]**2);
   plateAtBridge+=this.panelShapeAtBridge[j]*this.panelX[j];
  }
  e+=.5*this.bridgePanelSpring*(this.bridgeX-plateAtBridge)**2;
  return e;
 }
 energyBalanceError(){return this.energy()-
   (this.externalWork-this.dissipated)}
}
