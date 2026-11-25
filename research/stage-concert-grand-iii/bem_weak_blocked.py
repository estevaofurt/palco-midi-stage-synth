"""Bounded temporary assembly of the existing analytic P1 weak system.
The global dense operator is still necessary for the direct solve.
Retain all target quadrature points, weights, source kernels and degrees.
"""
import numpy as np
from scipy.linalg import solve
from exterior_bem import elements
from bem_weak_p1_refined import quadrature
from bem_p1_static_moments import operators
from split_radiation import relative

def assemble(t,k,outer,inner,velocity,*,block=32,reuse_sources=False):
    if not isinstance(reuse_sources,bool):raise ValueError('invalid source reuse mode')
    t=np.asarray(t,float)
    if t.ndim!=3 or t.shape[1:]!=(3,3) or not len(t) or not np.isfinite(t).all():
        raise ValueError('invalid boundary mesh')
    if not isinstance(block,int) or isinstance(block,bool) or block<1:
        raise ValueError('invalid assembly block')
    if not np.isfinite(k) or k<=0:raise ValueError('positive harmonic wave number required')
    x,w,L=quadrature(t,outer);_,n,a=elements(t);N=len(t)
    if np.any(a<=0):raise ValueError('degenerate element')
    op=operators
    if reuse_sources:
        from bem_prepared_operator import PreparedOperator
        op=PreparedOperator(t,inner)
    D=np.zeros((N,3,3*N),complex);B=None
    for j in range(len(L)):
        for start in range(0,N,block):
            stop=min(start+block,N);sl=slice(start,stop);owner=np.arange(start,stop)
            _,K=op(t,x[sl,j],n[sl],owner,k,inner,True)
            V=np.asarray(velocity(x[sl,j],owner))
            if V.ndim!=2 or V.shape[0]!=len(owner) or not np.isfinite(V).all() or np.iscomplexobj(V):
                raise ValueError('invalid prescribed velocity')
            W=w[sl,j,None]*L[j][None,:]
            if B is None:B=np.zeros((N,3,V.shape[1]))
            if V.shape[1]!=B.shape[2]:raise ValueError('inconsistent velocity basis')
            D[sl]+=W[:,:,None]*K[:,None,:]
            B[sl]+=W[:,:,None]*V[:,None,:]
    if not np.isfinite(D).all():raise ValueError('nonfinite weak operator')
    return D.reshape(3*N,3*N),B.reshape(3*N,-1),np.repeat(np.sqrt(a),3)

def fit(t,k,outer,inner,velocity,*,block=32,reuse_sources=False):
    D,B,sc=assemble(t,k,outer,inner,velocity,block=block,reuse_sources=reuse_sources)
    q=solve(D/sc[:,None]/sc[None,:],-B/sc[:,None],assume_a='gen')/sc[:,None]
    residual=relative(D@q,-B)
    if not np.isfinite(q).all() or residual>1e-8:raise ValueError('weak system residual failed')
    N=len(t);itemsize=D.dtype.itemsize
    return q,dict(weakResidual=residual,unknowns=len(q),assemblyBlock=block,
        globalMatrixBytes=D.nbytes,
        legacyContributionBytes=9*N*N*itemsize,
        blockedContributionBytes=9*min(block,N)*N*itemsize)
