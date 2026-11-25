"""Batched evaluation of the identical radial Duffy self-reactive integral.
No changes to singularity treatment, basis, nodes, weights or kernel.
Returns the unsymmetrized reactive matrix for independent audit.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss

def self_react_blocked(panel,samples,k,order,*,block=8):
    xy,_,w,S=map(np.asarray,samples);k=np.asarray(k)
    if not isinstance(block,int) or isinstance(block,bool) or block<1 or not isinstance(order,int) or order<2:
        raise ValueError('invalid self quadrature controls')
    if xy.ndim!=2 or xy.shape[1]!=2 or w.shape!=(len(xy),) or S.shape!=(len(xy),panel.basis.count) or k.ndim!=1 or not len(k):
        raise ValueError('invalid self quadrature shapes')
    if not all(np.isrealobj(x) and np.isfinite(x).all() for x in (xy,w,S,k)) or np.any(w<=0) or np.any(k<=0):
        raise ValueError('invalid self quadrature values')
    z,wt=leggauss(order);z=(z+1)/2;wt=wt/2
    u,v=np.meshgrid(z,z,indexing='ij');u=u.ravel();v=v.ravel()
    W=(wt[:,None]*wt[None,:]).ravel()
    raw=np.zeros((len(k),S.shape[1],S.shape[1]))
    for i in range(0,len(xy),block):
        j=min(i+block,len(xy));x=xy[i:j];m=len(x)
        q=np.zeros((m,len(k),S.shape[1]))
        for a,b in zip(panel.poly,np.roll(panel.poly,-1,axis=0)):
            A=a-x;B=b-x;det=A[:,0]*B[:,1]-A[:,1]*B[:,0]
            if np.any(det<=0):raise ValueError('self quadrature target outside convex panel')
            d=(1-v[None,:,None])*A[:,None,:]+v[None,:,None]*B[:,None,:]
            L=np.linalg.norm(d,axis=2)
            if np.any(L<=0):raise ValueError('degenerate radial quadrature')
            y=x[:,None,:]+u[None,:,None]*d
            shape=panel.basis(y.reshape(-1,2)).reshape(m,len(u),S.shape[1])
            kernel=np.cos(k[None,:,None]*u[None,None,:]*L[:,None,:])
            kernel*=W[None,None,:]*det[:,None,None]/L[:,None,:]
            q+=kernel@shape
        raw+=np.einsum('ti,tfj->fij',w[i:j,None]*S[i:j],q,optimize=True)
    if not np.isfinite(raw).all():raise ValueError('nonfinite self integral')
    return raw
