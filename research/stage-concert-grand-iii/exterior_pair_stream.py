"""Memory-bounded tensor integration of exterior panel pairs.
Same quadrature nodes, physical kernels and basis weights as lid_exterior.
Only the reduction order changes. No truncation or approximation.
"""
import numpy as np
from scipy.spatial.distance import cdist

def pair_integrals(x,A,y,B,k,*,mutual,block=128):
    x,A,y,B,k=map(np.asarray,(x,A,y,B,k))
    if x.ndim!=2 or y.ndim!=2 or x.shape[1:]!=(3,) or y.shape[1:]!=(3,) or A.ndim!=2 or B.ndim!=2 or len(A)!=len(x) or len(B)!=len(y) or min(len(x),len(y))<1 or k.ndim!=1 or len(k)<1:
        raise ValueError('invalid pair shapes')
    if not isinstance(block,int) or isinstance(block,bool) or block<1 or not all(np.isrealobj(z) and np.isfinite(z).all() for z in (x,A,y,B,k)) or np.any(k<=0):
        raise ValueError('invalid pair integration')
    R=np.zeros((len(k),A.shape[1],B.shape[1]));X=np.zeros_like(R) if mutual else None
    for i in range(0,len(x),block):
        j=min(i+block,len(x));D=cdist(x[i:j],y)
        if mutual and D.min()<=0:raise ValueError('coincident mutual quadrature nodes')
        At=A[i:j].T
        for l,kl in enumerate(k):
            R[l]+=At@(np.sinc(kl*D/np.pi)@B)
            if mutual:X[l]+=At@((np.cos(kl*D)/D)@B)
    return R,X,dict(fullDistanceBytes=len(x)*len(y)*8,
        blockedDistanceBytes=min(block,len(x))*len(y)*8,block=block)
