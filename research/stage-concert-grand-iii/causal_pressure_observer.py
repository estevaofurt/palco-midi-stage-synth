"""G3.12z: causal retarded Rayleigh pressure observer.
Co-coordinate physical surface; acceleration input in structural modes.
Linear observation only: no acoustic feedback or calibrated piano recording."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.signal import fftconvolve
from wire_physical_midpoint import load
from structural_region_decay import rebuild
from polygon_radiation import SurfaceModes
from enriched_baffle import samples
from radiation_resistance import pressure
from dual_cavity_spatial_diagnostic import save_matrices
from split_radiation import relative

RHO=1.204
C=343.
TRAIN=[30.,65.,150.,250.,261.4,261.63,261.86,300.,500.]
HIGH=[750.,1000.,1500.,2000.,4000.,8000.]

def delay_weights(x,degree):
    if degree not in (1,3):raise ValueError('degree')
    x=np.asarray(x,float)
    if not np.isfinite(x).all() or np.any(x<0) or np.any(x>=1):raise ValueError('fraction')
    nodes=np.arange(degree+1,dtype=float)
    # Cubic uses one earlier tap and two later taps; causal for physical delays >=1.
    if degree==3:nodes-=1
    L=np.ones((len(x),len(nodes)))
    for i,a in enumerate(nodes):
        for j,b in enumerate(nodes):
            if i!=j:L[:,i]*=(x-b)/(a-b)
    return nodes.astype(int),L

def build_kernel(xy,w,S,mic,rate,degree=3):
    xy=np.asarray(xy,float);w=np.asarray(w,float);S=np.asarray(S,float);mic=np.asarray(mic,float)
    if xy.ndim!=2 or xy.shape[1]!=2 or w.shape!=(len(xy),) or S.ndim!=2 or len(S)!=len(xy) or mic.ndim!=2 or mic.shape[1]!=3 or rate<=0:
        raise ValueError('geometry')
    if not all(np.isfinite(a).all() for a in (xy,w,S,mic)) or np.any(w<=0) or np.any(mic[:,2]<=0):raise ValueError('physical domain')
    distance=np.linalg.norm(mic[:,None,:]-np.c_[xy,np.zeros(len(xy))][None,:,:],axis=-1)
    delays=rate*distance/C;whole=np.floor(delays).astype(int)
    nodes=np.arange(degree+1)-(degree==3)
    if whole.min()+nodes.min()<0:raise ValueError('noncausal stencil')
    K=np.zeros((len(mic),int(whole.max()+nodes.max()+1),S.shape[1]))
    for m in range(len(mic)):
        _,weights=delay_weights(delays[m]-whole[m],degree)
        amplitude=RHO*w/(2*np.pi*distance[m])
        for j,offset in enumerate(nodes):
            taps=whole[m]+offset;v=amplitude*weights[:,j]
            # Sum all quadrature contributions assigned to each sample delay.
            for i in range(S.shape[1]):
                K[m,:,i]+=np.bincount(taps,weights=v*S[:,i],minlength=K.shape[1])
    support=np.stack([whole.min(axis=1)+nodes.min(),whole.max(axis=1)+nodes.max()],axis=1)
    return K,support,delays

def transfer(K,f,rate,velocity=False):
    f=np.atleast_1d(np.asarray(f,float));z=np.exp(-2j*np.pi*f/rate)
    H=np.einsum('ft,mti->fmi',z[:,None]**np.arange(K.shape[1]),K)
    if velocity:H*=((3-4*z+z*z)*rate/2)[:,None,None]
    return H

class Observer:
    def __init__(self,K,rate,velocity=False):
        self.K=np.array(K,float,copy=True);self.rate=rate;self.velocity=velocity
        if self.K.ndim!=3 or min(self.K.shape)<1 or not np.isfinite(self.K).all() or rate<=0:raise ValueError('kernel')
        self.history=np.zeros((self.K.shape[1]-1,self.K.shape[2]));self.prev=np.zeros((2,self.K.shape[2]))
    def process(self,x):
        x=np.asarray(x,float)
        if x.ndim!=2 or x.shape[1]!=self.K.shape[2] or not np.isfinite(x).all():raise ValueError('input block')
        if len(x)==0:return np.zeros((0,self.K.shape[0]))
        if self.velocity:
            y=np.concatenate([self.prev,x],axis=0)
            self.prev=y[-2:].copy()
            x=(3*y[2:]-4*y[1:-1]+y[:-2])*self.rate/2
        n=len(self.history);y=np.concatenate([self.history,x],axis=0);out=[]
        for k in self.K:
            z=fftconvolve(y,k,mode='full',axes=0)
            out.append(z[n:n+len(x)].sum(axis=1))
        if n:self.history=y[-n:].copy()
        return np.stack(out,axis=1)

def stream_proof(K,rate,support):
    n=K.shape[1]+513;p=K.shape[2];rng=np.random.default_rng(321)
    x=rng.normal(size=(n,p));x[400:]=0.
    impulse=np.zeros((n,p));impulse[0,0]=1.
    silence=Observer(K,rate).process(np.zeros_like(x))
    imp=Observer(K,rate).process(impulse);expected=np.zeros_like(imp);expected[:K.shape[1]]=K[:,:,0].T
    impulseError=relative(imp,expected)
    # FFT convolution may produce roundoff before arrival. Audit bound, not bitwise zeros.
    scale=max(np.max(abs(imp)),1e-30)
    early=max(float(np.max(abs(imp[:a,i]),initial=0.))/scale for i,(a,b) in enumerate(support))
    errors=[]
    for v in (False,True):
        y=Observer(K,rate,v).process(x);obs=Observer(K,rate,v)
        chunks=[];pos=0;lengths=(1,17,128,37,256);j=0
        while pos<n:
            end=min(n,pos+lengths[j%len(lengths)]);chunks.append(obs.process(x[pos:end]));pos=end;j+=1
        errors.append(relative(np.concatenate(chunks),y))
        if not np.isfinite(y).all():raise ValueError('nonfinite stream')
    return dict(impulseRelative=impulseError,preArrivalRelative=early,blockPartitionRelative=errors,
        silenceExact=bool(np.count_nonzero(silence)==0),
        gate=bool(max(impulseError,early,*errors)<=1e-10 and np.count_nonzero(silence)==0))

def harmonic_proof(K,rate,xy,w,S,mic,frequencies):
    accel=transfer(K,frequencies,rate);vel=transfer(K,frequencies,rate,True)
    rows=[]
    for i,f in enumerate(frequencies):
        exact=pressure(xy,w,S,mic,f,RHO,C)
        row=dict(frequencyHz=f,accelerationRelative=relative(accel[i]*(2j*np.pi*f),exact),
            velocityRelative=relative(vel[i],exact))
        rows.append(row)
    return rows

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','source','surface','regions','out'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();archive,wires,sha=load(a.source,a.scale)
    raw=(a.regions/'structural_region_decay.json').read_bytes();d=json.loads(raw)
    if d['sourceFrozenSha256']!=sha or any(d['summary'].get(k)!=v for k,v in dict(gate=True,cases=28,localBasisRebuilt=True,acousticLoadIncluded=False).items()):
        raise ValueError('unapproved regional source')
    local={}
    def sink(plate,poly,lift):local.update(plate=plate,poly=poly,lift=lift)
    k,D,P,A,wires,G,lift,replay=rebuild(a.scale,a.surface,archive,wires,surface_sink=sink)
    plate,poly=local['plate'],local['poly'];field=SurfaceModes(plate,local['lift'])
    x0,w0,S0=samples(plate,field,6);x,w,S=samples(plate,field,8)
    center=poly.mean(0);mic=np.array([[*center,.5],[center[0]+.25,center[1],1.5]])
    freq=TRAIN+HIGH
    spatial=[dict(frequencyHz=f,relative=relative(pressure(x0,w0,S0,mic,f,RHO,C),pressure(x,w,S,mic,f,RHO,C))) for f in freq]
    cases=[];matrices=dict(stiffness=k,damping=D,ports=P,wirePorts=A,physicalLift=lift,regionalDamping=G,
        microphoneXYZ=mic,pressureReference=np.stack([pressure(x,w,S,mic,f,RHO,C) for f in freq]))
    for rate in (48000,96000):
        for degree in (1,3):
            K,support,delays=build_kernel(x,w,S,mic,rate,degree)
            if any(np.count_nonzero(K[i,:lo]) or np.count_nonzero(K[i,hi+1:]) for i,(lo,hi) in enumerate(support)):raise ValueError('kernel outside support')
            stream=stream_proof(K,rate,support);harm=harmonic_proof(K,rate,x,w,S,mic,freq)
            dc=float(np.linalg.norm(transfer(K,[0.],rate,True)))
            band=max(max(v['accelerationRelative'],v['velocityRelative']) for v in harm if v['frequencyHz'] in TRAIN)
            row=dict(rate=rate,degree=degree,taps=K.shape[1],supportSamples=support.tolist(),
                physicalDelayMs=(1000/rate*np.stack([delays.min(axis=1),delays.max(axis=1)],axis=1)).tolist(),
                dcVelocityResponse=dc,stream=stream,harmonic=harm,maximumBandError=band,
                gate=bool(stream['gate'] and dc==0. and band<=.005))
            cases.append(row);matrices[f'kernel_{rate}_{degree}']=K
            print('G3_CAUSAL_PRESSURE_CASE '+json.dumps(row,allow_nan=False),flush=True)
    summary=dict(gate=bool(all(v['gate'] for v in cases) and max(v['relative'] for v in spatial if v['frequencyHz'] in TRAIN)<=1e-6),
        diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,oneSidedIdealBaffle=True,
        structureRank=80,microphones=2,cases=len(cases),validatedBandHz=[30,500],higherBandDiagnosticOnly=True,
        sameCoordinateSurface=True,causalDelayObserver=True,pressureUnits='Pa per modal acceleration input',
        maximumBandError=max(v['maximumBandError'] for v in cases),
        acousticFeedbackIncluded=False,physicalAcousticFitAccepted=False,audibleSustainMeasured=False,
        timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    a.out.mkdir(parents=True,exist_ok=True)
    desc=save_matrices(a.out,'causal_pressure_observer',frequencies=freq,**matrices)
    (a.out/'causal_pressure_observer.json').write_text(json.dumps(dict(summary=summary,cases=cases,spatial=spatial,
        coordinateReplay=replay,archive=desc,sourceFrozenSha256=sha,regionManifestSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_CAUSAL_PRESSURE_GATE '+json.dumps(summary),flush=True)
    if not summary['gate']:raise ValueError('causal pressure proof failed')
if __name__=='__main__':main()
