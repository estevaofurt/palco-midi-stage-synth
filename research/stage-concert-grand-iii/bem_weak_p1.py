"""Discontinuous P1 Galerkin testing of the single-layer Neumann trace.
Integrates both linear trial and test functions. Not a symmetric Calderon
formulation; no imposed reciprocity, damping, or eigenvalue clipping.
"""
import numpy as np
from scipy.linalg import solve
from exterior_bem import elements,samples
from bem_linear import shape,rule,operators
from split_radiation import relative

def assembly(t,k,outer,inner,velocity,derivative_only=True):
    x,w=samples(t,outer);_,n,a=elements(t);N=len(t)
    u,v,_=rule(outer);L=shape(np.c_[1-u,u*(1-v),u*v])
    D=np.zeros((N,3,3*N),complex);B=None;owner=np.arange(N)
    # Stream target quadrature slices to bound memory. The trace jump
    # is integrated with the same test and trial functions as K'.
    for j in range(len(L)):
        _,K=operators(t,x[:,j],n,owner,k,inner,derivative_only=derivative_only)
        V=np.asarray(velocity(x[:,j],owner))
        if B is None:B=np.zeros((N,3,V.shape[1]),float)
        W=w[:,j,None]*L[j][None,:]
        D+=W[:,:,None]*K[:,None,:]
        B+=W[:,:,None]*V[:,None,:]
    return D.reshape(3*N,3*N),B.reshape(3*N,-1)

def fit(t,k,outer,inner,velocity,derivative_only=True):
    D,B=assembly(t,k,outer,inner,velocity,derivative_only=derivative_only)
    a=elements(t)[2];sc=np.repeat(np.sqrt(a),3)
    A=D/sc[:,None]/sc[None,:]
    q=solve(A,-B/sc[:,None],assume_a='gen')/sc[:,None]
    return q,dict(weakResidual=relative(D@q,-B),
        coefficientNorm=float(np.linalg.norm(q)),unknowns=len(q),
        outerOrder=outer,innerOrder=inner)
