"""Experimental exterior Neumann radiation by internal equivalent monopoles.
Closed convex envelope only, with prescribed velocity on its boundary.
No scattering correction from the earlier free-space sheet model is added.
Convention exp(i omega t), pressure=i rho omega potential, v=-d_n potential.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss
from rigid_scattering import green,normal_derivative
from split_radiation import relative

def fit(x,n,w,V,sources,k):
    A=normal_derivative(x,n,sources,k);B=-V
    sw=np.sqrt(w)[:,None]
    q,_,rank,sv=np.linalg.lstsq(sw*A,sw*B,rcond=1e-12)
    return q,dict(rank=int(rank),columns=len(sources),condition=float(sv[0]/sv[-1]),
        trainingResidual=relative(sw*(A@q),sw*B))

def far(sources,q,k,order=28):
    mu,w=leggauss(order);phi=2*np.pi*np.arange(4*order)/(4*order)
    s=np.sqrt(1-mu*mu)
    d=np.stack([s[:,None]*np.cos(phi),s[:,None]*np.sin(phi),np.broadcast_to(mu[:,None],(order,len(phi)))],axis=-1).reshape(-1,3)
    wt=np.repeat(w*2*np.pi/len(phi),len(phi))
    F=np.exp(1j*k*(d@sources.T))@q
    return F.conj().T@(wt[:,None]*F)/(4*np.pi)

def audit(x,n,w,V,sources,q,k,points,rho=1.204,c=343.):
    A=normal_derivative(x,n,sources,k);sw=np.sqrt(w)[:,None]
    Z=1j*rho*c*k*(V.T@(w[:,None]*(green(x,sources,k)@q)))
    P=1j*rho*c*k*(green(points,sources,k)@q)
    R=(Z+Z.conj().T)/2
    G=rho*c*k*k/(4*np.pi)*far(sources,q,k)
    den=max(np.linalg.norm(Z),1e-30)
    rep=dict(heldoutResidual=relative(sw*(A@q),-sw*V),reciprocity=relative(Z,Z.T),
        powerRelative=relative(R,G),passivityMinRelative=float(min(np.linalg.eigvalsh(R))/den))
    rep['gate']=rep['heldoutResidual']<=.05 and rep['reciprocity']<=.01 and rep['powerRelative']<=.01 and rep['passivityMinRelative']>=-1e-8
    return Z,P,rep
