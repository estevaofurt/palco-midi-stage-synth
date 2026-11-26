"""Align independent mass-normalized structural bases by their physical lifts."""
import numpy as np
from split_radiation import relative

def align(local,reference):
    L=reference['physicalLift'];R=local['physicalLift']
    if L.shape!=R.shape or L.ndim!=2 or not np.isfinite(L).all() or not np.isfinite(R).all():raise ValueError('physical lift')
    scale=np.maximum(np.maximum(np.linalg.norm(L,axis=1),np.linalg.norm(R,axis=1)),1e-12*np.max(abs(L)))
    T,_,rank,_=np.linalg.lstsq(L/scale[:,None],R/scale[:,None],rcond=1e-12)
    if rank!=L.shape[1]:raise ValueError('rank')
    U,_,V=np.linalg.svd(T,full_matrices=False);Q=U@V
    errors=dict(orthogonality=relative(T.T@T,np.eye(len(T))),correction=relative(T,Q),
        physicalLift=relative(L@Q,R),
        stiffness=relative(Q.T@np.diag(reference['stiffness'])@Q,np.diag(local['stiffness'])),
        damping=relative(Q.T@reference['damping']@Q,local['damping']),
        ports=relative(Q.T@reference['ports'],local['ports']),
        wirePorts=relative(reference['wirePorts']@Q,local['wirePorts']),
        regionalDamping=relative(np.stack([Q.T@g@Q for g in reference['regionalDamping']]),local['regionalDamping']))
    if max(errors.values())>1e-7:raise ValueError('coordinate congruence '+str(errors))
    return Q,errors
