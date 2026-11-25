"""Positive quadrature on exact centroid-to-edge radial intervals.
d is distance from the edge as a fraction of centroid altitude,
not distance in metres. Split u=sqrt(d) at exact interval endpoints.
No change of physical boundary or density.
"""
import numpy as np
from exterior_bem import elements,gauss

LIMITS=(0.,.1,.4,1.)

def band_samples(t,order,limits=LIMITS):
    t=np.asarray(t,float);limits=np.asarray(limits,float)
    if t.ndim!=3 or t.shape[1:]!=(3,3) or not len(t) or not np.isfinite(t).all():
        raise ValueError('invalid triangles')
    if not isinstance(order,int) or isinstance(order,bool) or order<2:
        raise ValueError('invalid quadrature order')
    if limits.ndim!=1 or len(limits)<2 or not np.isfinite(limits).all() or limits[0]!=0 or limits[-1]!=1 or np.any(np.diff(limits)<=0):
        raise ValueError('invalid radial limits')
    z,w=gauss(order);center=t.mean(1);area=elements(t)[2]
    if np.any(area<=0):raise ValueError('degenerate triangles')
    xs=[];ws=[];sectors=[];bands=[]
    for j in range(3):
        for b,(lo,hi) in enumerate(zip(np.sqrt(limits[:-1]),np.sqrt(limits[1:]))):
            u,v=np.meshgrid(lo+(hi-lo)*z,z,indexing='ij');u=u.ravel();v=v.ravel()
            wt=(w[:,None]*w[None,:]).ravel()*(hi-lo);d=u*u
            e=(1-v[None,:,None])*t[:,j,None,:]+v[None,:,None]*t[:,(j+1)%3,None,:]
            x=(1-d[None,:,None])*e+d[None,:,None]*center[:,None,:]
            weight=(2*area[:,None]/3)*(wt*(1-d)*2*u)[None,:]
            xs.append(x);ws.append(weight);sectors.extend([j]*order**2);bands.extend([b]*order**2)
    return np.concatenate(xs,axis=1),np.concatenate(ws,axis=1),np.array(sectors),np.array(bands)

def samples(t,order):
    x,w,_,_=band_samples(t,order)
    return x,w
