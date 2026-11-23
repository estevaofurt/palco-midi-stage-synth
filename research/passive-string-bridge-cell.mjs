/**
 * Stage Synth — PASSIVE string/bridge/plate RESEARCH CELL (not a piano engine).
 *
 * Four generalized coordinates:
 *  0: fast transverse string polarization
 *  1: slow transverse string polarization
 *  2: bridge / first radiating board bending mode
 *  3: second radiating board mode
 *
 * Equations M x'' + C x' + K x = [F_h(t),0,0,0].
 *
 * K = sum of positive ground springs and positive coupling spring elements
 *     k_ij (x_i - x_j)^2 / 2. C and M are positive diagonal.
 * Numerical integrator: implicit midpoint on (x, v) using a constant SPD
 * Cholesky solve. In every step, to rounding precision:
 *
 *    E_{n+1} - E_n = dt * (F_mid * v_mid[0]
 *                         - Σ_i c_i * v_mid[i]^2)
 *
 * => with no hammer force, mechanical energy cannot grow; coupling exchanges
 * energy between string modes and soundboard, never creates it.
 *
 * WARNING:
 * - Mass and spring numbers are NORMALIZED ILLUSTRATIVE parameters, not SI
 *   estimates of a Yamaha/Steinway bridge, not measured mobility or radiation.
 * - plateVelocity is NOT acoustic pressure [Pa], and bridgeReaction is NOT
 *   measured force [N]. Mapping these to a listener requires a measured,
 *   authorized acceleration/velocity -> sound pressure transfer function.
 * - This standalone research cell is NOT connected to any Stage DSP or UI.
 * - 4 dense coordinates / voice would be too expensive to scale blindly.
 *   Benchmark and reduce to a passive 2-port before integrating.
 * - Implemented from elementary equations, not copied code.
 */
export const PASSIVE_BRIDGE_DIMENSIONS = 4;
const TWO_PI = 2*Math.PI;
const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
const midiHz=note=>440*2**((note-69)/12);

export class PassiveStringBridgeCell {
  constructor({sampleRate=48000,key=36,coupling=.12}={}){
    if(!Number.isFinite(sampleRate)||sampleRate<22050||sampleRate>192000)
      throw new RangeError('invalid sampleRate');
    if(!Number.isInteger(key)||key<21||key>108)
      throw new RangeError('invalid MIDI key');
    if(!Number.isFinite(coupling)||coupling<0||coupling>1)
      throw new RangeError('coupling must be within 0..1');
    this.rate=sampleRate;
    this.dt=1/sampleRate;
    this.key=key;
    this.coupling=coupling;
    this.n=PASSIVE_BRIDGE_DIMENSIONS;
    this.x=new Float64Array(4);
    this.v=new Float64Array(4);
    this.vmid=new Float64Array(4);
    this.rhs=new Float64Array(4);
    this.forward=new Float64Array(4);
    this.mass=new Float64Array([1,1.1,3.7,2.4]);
    // Damping coefficients are nonnegative; these do NOT correspond to
    // measured T60 of a commercial piano.
    const f0=midiHz(key);
    const hz=[f0,f0*1.0009,90+clamp((key-36)*.12,-4,4),155];
    const losses=[.5,.14,11,17];
    this.frequencies=new Float64Array(hz);
    this.damping=new Float64Array(4);
    this.stiffness=new Float64Array(16);
    for(let i=0;i<4;i++){
      const m=this.mass[i],w=TWO_PI*hz[i];
      this.stiffness[i*4+i]=m*w*w;
      this.damping[i]=2*m*losses[i];
    }
    // Conservative bidirectional stiffness at the string-to-bridge joint.
    // Each term k(x_i-x_j)^2/2 is positive, so the resulting K is SPD.
    const base=Math.pow(TWO_PI*f0,2)*coupling;
    this.addSpring(0,2,base*.16);
    this.addSpring(1,2,base*.095);
    this.addSpring(2,3,base*.28);
    this.L=new Float64Array(16);
    const h=this.dt;
    // A = M + h*C/2 + h²*K/4, symmetric positive definite.
    for(let i=0;i<4;i++){
      for(let j=0;j<=i;j++){
        let a=(i===j?this.mass[i]+h*this.damping[i]*.5:0)+
          h*h*this.stiffness[i*4+j]*.25;
        for(let k=0;k<j;k++)a-=this.L[i*4+k]*this.L[j*4+k];
        if(i===j){
          if(!(a>0&&Number.isFinite(a)))
            throw new RangeError('unphysical mass, damping or stiffness');
          this.L[i*4+j]=Math.sqrt(a);
        }else this.L[i*4+j]=a/this.L[j*4+j];
      }
    }
    this.plateVelocity=0;
    this.bridgeVelocity=0;
    this.bridgeReaction=0;
    this.hammerWork=0;
    this.dissipatedEnergy=0;
  }
  addSpring(i,j,k){
    if(!(k>=0&&Number.isFinite(k)))throw new RangeError('spring must be passive');
    const K=this.stiffness;
    K[i*4+i]+=k;K[j*4+j]+=k;
    K[i*4+j]-=k;K[j*4+i]-=k;
  }
  setInitialDisplacement(index,displacement){
    if(!Number.isInteger(index)||index<0||index>=4||!Number.isFinite(displacement))
      throw new RangeError('initial coordinate');
    this.x[index]=displacement;
  }
  energy(){
    let e=0;
    for(let i=0;i<4;i++){
      e+=.5*this.mass[i]*this.v[i]*this.v[i];
      for(let j=0;j<4;j++)
        e+=.5*this.x[i]*this.stiffness[i*4+j]*this.x[j];
    }
    return e;
  }
  /**
   * One audio-rate step with constant force over the step.
   * Output is plate midpoint generalized VELOCITY, not sound pressure.
   * All buffers are allocated in the constructor; no per-sample objects.
   */
  step(force=0){
    if(!Number.isFinite(force))throw new TypeError('nonfinite hammer force');
    const h=this.dt,K=this.stiffness,vel=this.v,pos=this.x,
      m=this.mass,L=this.L,b=this.rhs,z=this.forward,vm=this.vmid;
    for(let i=0;i<4;i++){
      let kx=0;
      for(let j=0;j<4;j++)kx+=K[4*i+j]*pos[j];
      b[i]=m[i]*vel[i]-.5*h*kx+(i===0?.5*h*force:0);
    }
    for(let i=0;i<4;i++){
      let y=b[i];
      for(let j=0;j<i;j++)y-=L[4*i+j]*z[j];
      z[i]=y/L[4*i+i];
    }
    for(let i=3;i>=0;i--){
      let y=z[i];
      for(let j=i+1;j<4;j++)y-=L[4*j+i]*vm[j];
      vm[i]=y/L[4*i+i];
    }
    let dissipated=0;
    for(let i=0;i<4;i++){
      pos[i]+=h*vm[i];
      vel[i]=2*vm[i]-vel[i];
      dissipated+=this.damping[i]*vm[i]*vm[i];
    }
    this.hammerWork+=h*force*vm[0];
    this.dissipatedEnergy+=h*dissipated;
    this.bridgeVelocity=vm[2];
    this.plateVelocity=.67*vm[2]+.33*vm[3];
    // Coupling reaction on string fast polarization (not a measured N).
    const spring=this.coupling*Math.pow(TWO_PI*midiHz(this.key),2)*.16;
    this.bridgeReaction=-spring*(pos[0]-pos[2]);
    return this.plateVelocity;
  }
  reset(){
    this.x.fill(0);this.v.fill(0);
    this.vmid.fill(0);this.rhs.fill(0);this.forward.fill(0);
    this.plateVelocity=this.bridgeVelocity=this.bridgeReaction=0;
    this.hammerWork=this.dissipatedEnergy=0;
  }
}
