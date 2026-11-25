"""Edge-graded weak P1 trial/test integration, retaining analytic source moments.
No new basis functions, constraints, damping or reciprocity projection.
The rule changes only the outer Galerkin integral.
"""
import numpy as np
from scipy.linalg import solve
from exterior_bem import elements,gauss
from bem_linear import shape
from bem_p1_static_moments import operators
from split_radiation import relative

def rule(order):
    if not isinstance(order,int) or order<2:raise ValueError('invalid edge rule order')
    z,w=gauss(order);u,v=np.meshgrid(z,z,indexing='ij');u=u.ravel();v=v.ravel()
    d=u*u;weight=(w[:,None]*w[None,:]).ravel()*(1-d)*4*u/3
    eye=np.eye(3);L=[]
    for j in range(3):
        L.append((1-d[:,None])*((1-v[:,None])*eye[j]+v[:,None]*eye[(j+1)%3])+d[:,None]/3)
    return np.vstack(L),np.tile(weight,3)

def assembly(t,k,outer,inner,velocity):
    L,w=rule(outer);S=shape(L);_,n,a=elements(t)
    N=len(t);owner=np.arange(N);D=np.zeros((N,3,3*N),complex);B=None
    for j,(l,wt) in enumerate(zip(L,w)):
        x=np.einsum('a,tad->td',l,t)
        _,K=operators(t,x,n,owner,k,inner,True)
        V=np.asarray(velocity(x,owner))
        W=a[:,None]*wt*S[j][None,:]
        if B is None:B=np.zeros((N,3,V.shape[1]),dtype=V.dtype)
        D+=W[:,:,None]*K[:,None,:];B+=W[:,:,None]*V[:,None,:]
    return D.reshape(3*N,3*N),B.reshape(3*N,-1)

def fit(t,k,outer,inner,velocity):
    D,B=assembly(t,k,outer,inner,velocity)
    sc=np.repeat(np.sqrt(elements(t)[2]),3)
    q=solve(D/sc[:,None]/sc[None,:],-B/sc[:,None],assume_a='gen')/sc[:,None]
    return q,dict(weakResidual=relative(D@q,-B),unknowns=len(q),targetPointsPerElement=3*outer**2)
