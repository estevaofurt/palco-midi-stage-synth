"""Independent far-field Gram with panel-local weighted basis matrices.
Exactly the same direction nodes and positive weights as lid_exterior.angular.
No modal truncation or change in physical kernel.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss

def angular_panels(samples,k,order,*,block=128):
    if not isinstance(order,int) or isinstance(order,bool) or order<2 or not isinstance(block,int) or isinstance(block,bool) or block<1:
        raise ValueError('invalid angular quadrature')
    if not np.isfinite(k) or k<=0 or not samples:raise ValueError('invalid wave number or samples')
    parts=[]
    for x,A in samples:
        x,A=np.asarray(x),np.asarray(A)
        if x.ndim!=2 or x.shape[1]!=3 or A.ndim!=2 or len(x)!=len(A) or min(A.shape)<1 or not all(np.isrealobj(v) and np.isfinite(v).all() for v in (x,A)):
            raise ValueError('invalid panel samples')
        parts.append((x,A))
    mu,w=leggauss(order);phi=2*np.pi*np.arange(4*order)/(4*order);s=np.sqrt(1-mu**2)
    d=np.stack([s[:,None]*np.cos(phi),s[:,None]*np.sin(phi),np.broadcast_to(mu[:,None],(order,len(phi)))],axis=-1).reshape(-1,3)
    w=np.repeat(w*2*np.pi/len(phi),len(phi))
    N=sum(A.shape[1] for x,A in parts);G=np.zeros((N,N),complex)
    for i in range(0,len(d),block):
        D=d[i:i+block]
        F=np.column_stack([np.exp(1j*k*(D@x.T))@A for x,A in parts])
        G+=F.conj().T@(w[i:i+block,None]*F)
    if not np.isfinite(G).all():raise ValueError('nonfinite Gram')
    totalSamples=sum(len(x) for x,A in parts)
    return G.real/(4*np.pi),dict(directions=len(d),modes=N,
        denseBasisBytes=8*totalSamples*N,localBasisBytes=sum(A.nbytes for x,A in parts),
        densePhaseBytes=16*min(block,len(d))*totalSamples,
        localLargestPhaseBytes=16*min(block,len(d))*max(len(x) for x,A in parts))
