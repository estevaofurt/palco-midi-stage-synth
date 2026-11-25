"""Refined weak P1: derivative-only assembly and positive symmetric
degree-five target integration. Same weak Neumann equations as G3.07t.
Tensor quadrature remains an independent refinement of the target integral.
"""
import numpy as np
from scipy.linalg import solve
from exterior_bem import elements,samples
from bem_linear import shape,rule
from bem_p1_stream import derivative
from split_radiation import relative

def perms(a,b):
    return [[a,b,b],[b,a,b],[b,b,a]]
L5=np.array([[1/3,1/3,1/3]]+perms(.059715871789770,.470142064105115)+perms(.797426985353087,.101286507323456))
W5=np.repeat([.225,.132394152788506,.125939180544827],[1,3,3])

def quadrature(t,outer):
    if outer=='symmetric5':
        a=elements(t)[2]
        return np.einsum('qa,tad->tqd',L5,t),a[:,None]*W5[None,:],shape(L5)
    if not isinstance(outer,int) or outer<2:raise ValueError('invalid target quadrature')
    x,w=samples(t,outer);u,v,_=rule(outer)
    return x,w,shape(np.c_[1-u,u*(1-v),u*v])

def assembly(t,k,outer,inner,velocity):
    x,w,L=quadrature(t,outer);_,n,_=elements(t);N=len(t)
    D=np.zeros((N,3,3*N),complex);B=None;owner=np.arange(N)
    for j in range(len(L)):
        K=derivative(t,x[:,j],n,owner,k,inner)
        V=np.asarray(velocity(x[:,j],owner))
        if B is None:B=np.zeros((N,3,V.shape[1]),float)
        W=w[:,j,None]*L[j][None,:]
        D+=W[:,:,None]*K[:,None,:];B+=W[:,:,None]*V[:,None,:]
    return D.reshape(3*N,3*N),B.reshape(3*N,-1)

def fit(t,k,outer,inner,velocity):
    D,B=assembly(t,k,outer,inner,velocity)
    sc=np.repeat(np.sqrt(elements(t)[2]),3)
    A=D/sc[:,None]/sc[None,:]
    q=solve(A,-B/sc[:,None],assume_a='gen')/sc[:,None]
    return q,dict(weakResidual=relative(D@q,-B),coefficientNorm=float(np.linalg.norm(q)),
        unknowns=len(q),outerRule=outer,innerOrder=inner)
