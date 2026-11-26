"""G3.14d pilot: convolution quadrature of a Laplace-domain load.
Small synthetic surfaces only; no physical piano or feedback integration.
A sampled positive-real check is not a continuum certificate."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.signal import fftconvolve
from retarded_surface import impedance
from split_radiation import relative

def symbol(z,rate):
    if not np.isfinite(rate) or rate<=0:raise ValueError('rate')
    z=np.asarray(z,complex)
    if not np.isfinite(z).all() or np.any(abs(z)>1+1e-12):raise ValueError('unit disk')
    return rate*((1-z)+(1-z)**2/2)

def harmonic_symbol(f,rate):
    """Exact unit-circle BDF2 identity, avoiding cancellation near DC."""
    f=np.asarray(f,float)
    if not np.isfinite(rate) or rate<=0 or not np.isfinite(f).all() or np.any(abs(f)>rate/2):raise ValueError('frequency')
    theta=2*np.pi*f/rate
    return rate*(4*np.sin(theta/2)**4+1j*np.sin(theta)*(2-np.cos(theta)))

def coefficients(load,rate,n,radius):
    if n<16 or n%2 or not 0<radius<1:raise ValueError('contour')
    z=radius*np.exp(-2j*np.pi*np.arange(n)/n)
    s=symbol(z,rate)
    values=np.stack([load(v) for v in s])
    if values.ndim!=3 or values.shape[1]!=values.shape[2] or not np.isfinite(values).all():raise ValueError('load')
    w=np.fft.ifft(values,axis=0)/radius**np.arange(n)[:,None,None]
    imag=float(np.linalg.norm(w.imag)/max(np.linalg.norm(w.real),1e-30))
    if imag>1e-8:raise ValueError('nonreal coefficients')
    return w.real,imag

def transfer(weights,f,rate):
    z=np.exp(-2j*np.pi*np.asarray(f)/rate)
    return np.einsum('ft,tij->fij',z[:,None]**np.arange(len(weights)),weights)

def convolve(weights,v):
    v=np.asarray(v,float)
    if v.ndim!=2 or v.shape[1]!=weights.shape[2]:raise ValueError('velocity')
    return sum(fftconvolve(v[:,j,None],weights[:,:,j],axes=0)[:len(v)] for j in range(v.shape[1]))

def power_check(Z):
    H=(Z+Z.conj().T)/2
    return float(np.linalg.eigvalsh(H).min()/max(np.linalg.norm(Z),1e-30))

def case(rate,n,radius,B,dx,dy):
    load=lambda s:impedance(B,dx,dy,s,12)
    W,imag=coefficients(load,rate,n,radius)
    W2,_=coefficients(load,rate,2*n,radius**.5)
    # Freeze first half of the longer contour; compare contour aliasing independently.
    alias=relative(W,W2[:n]);tail=float(np.linalg.norm(W2[n:])/max(np.linalg.norm(W2),1e-30))
    f=np.unique(np.r_[0.,np.geomspace(20.,500.,26),np.geomspace(501.,rate/2,48)])
    z=np.exp(-2j*np.pi*f/rate)
    direct=np.stack([load(s) for s in harmonic_symbol(f,rate)])
    ideal=np.stack([load(2j*np.pi*x) for x in f])
    recon=transfer(W,f,rate)
    den=max(np.linalg.norm(direct,axis=(1,2)).max(),1e-30)
    # DC relative error would be undefined for zero impedance.
    err=[relative(x,y) for x,y,ff in zip(recon,direct,f) if ff>0]
    band=[relative(x,y) for x,y,ff in zip(direct,ideal,f) if 0<ff<=500]
    dc=float(np.linalg.norm(recon[0])/den)
    p0=min(power_check(x) for x in direct);p1=min(power_check(x) for x in recon)
    rng=np.random.default_rng(431);work=[]
    for typ in ('noise','low_band','pulse'):
        t=np.arange(4*n)/rate
        if typ=='noise':v=rng.normal(size=(len(t),B.shape[2]))
        elif typ=='low_band':v=np.sin(2*np.pi*261.63*t[:,None]+np.arange(B.shape[2]))
        else:
            v=np.zeros((len(t),B.shape[2]));v[:n//4]=rng.normal(size=(n//4,B.shape[2]))
        force=convolve(W,v);p=np.sum(force*v,axis=1)/rate
        work.append(dict(type=typ,totalJ=float(p.sum()),minimumCumulativeRelative=float(min(0.,np.cumsum(p).min())/max(np.sum(abs(p)),1e-30))))
    gate=bool(max(alias,tail,imag,dc,max(err))<=1e-5 and max(band)<=.005 and min(p0,p1)>=-1e-9 and min(v['minimumCumulativeRelative'] for v in work)>=-1e-9)
    return dict(rate=rate,contourSamples=n,radius=radius,aliasRelative=alias,tailRelative=tail,imaginaryRelative=imag,
        dcRelative=dc,maximumReconstructionRelative=max(err),maximumBandDerivativeRelative=max(band),
        directMinimumRelative=p0,kernelMinimumRelative=p1,work=work,screeningGate=gate)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    # A constant and two independent signed surface fields on 4x4 cells.
    # Cell integrals, not pointwise values. Dimensions deliberately synthetic.
    x,y=np.meshgrid(np.linspace(-1,1,4),np.linspace(-1,1,4),indexing='ij')
    B=np.stack([np.ones_like(x),x,y],axis=-1)*(.02*.03)
    rows=[]
    for rate in (48000,96000):
        for n in (256,512):
            row=case(rate,n,.98,B,.02,.03);rows.append(row)
            print('G3_CQ_PILOT_CASE '+json.dumps(row,allow_nan=False),flush=True)
    summary=dict(gate=True,diagnosticOnly=True,syntheticSurface=True,configurations=len(rows),
        screeningPassed=sum(r['screeningGate'] for r in rows),continuousPassivityCertified=False,
        pianoSurfaceValidated=False,feedbackIntegrated=False,timeDomainReady=False,audibleSustainMeasured=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'acoustic_cq_pilot.json').write_text(json.dumps(dict(summary=summary,cases=rows),indent=2,allow_nan=False))
    print('G3_CQ_PILOT_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
