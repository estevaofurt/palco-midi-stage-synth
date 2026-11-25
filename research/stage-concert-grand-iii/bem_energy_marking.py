"""Local indicators of the prescribed/computed work mismatch.
The signed local Hermitian work matrices sum to the global mismatch.
Their norms are indicators, not rigorous error bounds.
No constraints, tuning or modifications to the physical solver.
"""
import numpy as np
from bem_linear import targets
from bem_weak_p1_refined import L5,W5
from exterior_bem import elements
from bem_p1_static_moments import operators
from bem_power_partition import herm

def local_terms(t,q,velocity,k,order,rho=1.204,c=343.):
    x,n,_,owner=targets(t,L5);w=(elements(t)[2][:,None]*W5[None,:]).ravel()
    V=velocity(x,owner);P=np.empty_like(V,dtype=complex);U=np.empty_like(P)
    for i in range(0,len(x),24):
        sl=slice(i,min(i+24,len(x)));G,D=operators(t,x[sl],n[sl],owner[sl],k,order)
        P[sl]=1j*rho*c*k*(G@q);U[sl]=-D@q
    E=V-U
    norm=np.sum(w[:,None]*abs(V)**2,axis=0)
    if np.any(norm<=1e-60):raise ValueError('unobservable velocity basis')
    residual=(w[:,None]*abs(E)**2/norm[None,:]).reshape(len(t),len(L5),-1).sum(axis=(1,2))
    W=np.einsum('tq,tqi,tqj->tij',w.reshape(len(t),-1),
        E.reshape(len(t),len(L5),-1).conj(),P.reshape(len(t),len(L5),-1))
    H=(W+W.conj().transpose(0,2,1))/2
    exact=herm(E.conj().T@(w[:,None]*P))
    closure=float(np.linalg.norm(H.sum(0)-exact)/max(np.linalg.norm(exact),1e-60))
    energy=np.linalg.norm(H,axis=(1,2))
    return residual,energy,dict(localWorkClosure=closure,
        globalWorkMismatch=float(np.linalg.norm(exact)),sumLocalWorkNorms=float(energy.sum()))

def score(parts,policy):
    if policy not in ('residual','combined'):raise ValueError('unknown policy')
    total=None
    for R,E in parts:
        R=np.asarray(R,float);E=np.asarray(E,float)
        if R.ndim!=1 or R.shape!=E.shape or not np.isfinite(R).all() or not np.isfinite(E).all() or min(R.min(),E.min())<0:
            raise ValueError('invalid local indicators')
        # Normalize each frequency independently, and avoid silently
        # discarding a zero indicator in favor of an arbitrary value.
        r=R/max(R.sum(),1e-60);e=E/max(E.sum(),1e-60)
        s=r if policy=='residual' else .5*(r+e)
        total=s.copy() if total is None else total+s
    if total is None:raise ValueError('no frequencies')
    return total
