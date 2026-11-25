"""Audit coordinate invariance of the aperture basis and FEM trace.
Canonical ports use exact geometric corners, not mesh node ordering.
No existing reference is silently replaced by this experimental path.
"""
import numpy as np
from scipy.linalg import block_diag
from split_radiation import relative
from lid_exterior import ports

def transform(old,new,order=16):
    """q_old=T q_new; equal physical fluxes in the two polynomial bases."""
    if len(old)!=len(new):raise ValueError('port count changed')
    blocks=[];errors=[];orth=[]
    for a,b in zip(old,new):
        if a.basis.count!=b.basis.count or abs(a.basis.area-b.basis.area)>1e-10:
            raise ValueError('incompatible bases')
        _,x,w,V=b.samples(order);U=a.basis(a.local(x))
        T=a.basis.area*(U.T@(w[:,None]*V))
        errors.append(relative(U@T,V))
        orth.append(relative(T.T@T,np.eye(len(T))))
        blocks.append(T)
    return block_diag(*blocks),dict(fieldRelative=max(errors),orthogonalityRelative=max(orth))

def audit(model,C0,report,count):
    old,Co=ports(model,C0,report,count)
    new,Cn=ports(model,C0,report,count,canonical=True)
    T,rep=transform(old,new)
    rep['traceRelative']=relative(Co@T,Cn)
    rep['gate']=max(rep.values())<=1e-8
    return old,new,Co,Cn,T,rep

def same_coordinates(a,b,order=12):
    T,rep=transform(a,b,order)
    rep['coordinateRelative']=relative(T,np.eye(len(T)))
    rep['gate']=max(rep.values())<=1e-8
    return rep
