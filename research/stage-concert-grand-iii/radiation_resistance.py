"""G3.06a: one-sided baffled planar radiation resistance and pressure observation.
Frequency-domain proof only. No reactive load, causal fit, lid, case or actual piano air.
Convention Re[v exp(i omega t)], peak complex amplitudes.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss

def hemisphere(order,azimuth=None):
    n=4*order if azimuth is None else azimuth
    mu,w=leggauss(order);mu=(mu+1)/2;w=w/2
    phi=2*np.pi*np.arange(n)/n
    u=np.sqrt(1-mu**2)
    xyz=np.stack([u[:,None]*np.cos(phi),u[:,None]*np.sin(phi),np.broadcast_to(mu[:,None],(order,n))],axis=-1)
    return xyz.reshape(-1,3),np.repeat(w*2*np.pi/n,n)

def validate(xy,w,S,rho,c,f):
    xy=np.asarray(xy,dtype=float);w=np.asarray(w,dtype=float);S=np.asarray(S,dtype=float)
    if xy.ndim!=2 or xy.shape[1]!=2 or w.shape!=(len(xy),) or S.ndim!=2 or len(S)!=len(xy):raise ValueError('surface quadrature shape')
    if min(w)<=0 or min(rho,c,f)<=0:raise ValueError('positive quadrature and medium required')
    if not all(np.all(np.isfinite(a)) for a in (xy,w,S)):raise ValueError('finite geometry required')
    return xy,w,S

def angular(xy,w,S,f,rho,c,order):
    xy,w,S=validate(xy,w,S,rho,c,f);omega=2*np.pi*f;k=omega/c
    dirs,weights=hemisphere(order);A=w[:,None]*S;R=np.zeros((S.shape[1],S.shape[1]))
    # Real part of complex Gram; for a planar source full azimuth makes the Gram real.
    B=np.zeros_like(R,dtype=complex)
    for i in range(0,len(dirs),128):
        d=dirs[i:i+128];z=np.exp(1j*k*(d[:,:2]@xy.T))@A
        B+=z.conj().T@(weights[i:i+128,None]*z)
    R=rho*omega**2/(4*np.pi**2*c)*B.real
    symmetry=float(np.linalg.norm(B.imag)/max(np.linalg.norm(B.real),1e-30))
    assert symmetry<1e-10
    assert min(np.linalg.eigvalsh(R))>=-1e-10*max(np.linalg.norm(R),1e-30)
    return R

def surface(xy,w,S,f,rho,c):
    """Independent real impedance kernel, including its finite diagonal limit."""
    xy,w,S=validate(xy,w,S,rho,c,f);omega=2*np.pi*f;k=omega/c;A=w[:,None]*S
    R=np.zeros((S.shape[1],S.shape[1]))
    for i in range(0,len(xy),128):
        d=np.linalg.norm(xy[i:i+128,None,:]-xy[None,:,:],axis=-1)
        R+=A[i:i+128].T@(np.sinc(k*d/np.pi)@A)
    return rho*omega**2/(2*np.pi*c)*R

def pressure(xy,w,S,points,f,rho,c):
    """Complex Pa per generalized velocity, same surface/medium as resistance."""
    xy,w,S=validate(xy,w,S,rho,c,f);omega=2*np.pi*f;k=omega/c
    p=np.atleast_2d(points)
    if p.shape[1]!=3 or min(p[:,2])<=0:raise ValueError('observation above planar surface only')
    d=np.linalg.norm(p[:,None,:]-np.c_[xy,np.zeros(len(xy))][None,:,:],axis=-1)
    return 1j*rho*omega/(2*np.pi)*((np.exp(-1j*k*d)/d)@(w[:,None]*S))

def far_amplitude(xy,w,S,dirs,f,rho,c):
    xy,w,S=validate(xy,w,S,rho,c,f);omega=2*np.pi*f
    d=np.atleast_2d(dirs)
    assert d.shape[1]==3 and np.all(d[:,2]>=0) and np.max(abs(np.linalg.norm(d,axis=1)-1))<1e-12
    # r exp(ikr) p -> this limit as radius r grows.
    return 1j*rho*omega/(2*np.pi)*(np.exp(1j*omega/c*(d[:,:2]@xy.T))@(w[:,None]*S))
