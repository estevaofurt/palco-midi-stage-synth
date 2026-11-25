"""Oversampled discontinuous P1 Neumann BEM.
Weighted least squares of the boundary trace, no physical damping, spectral
cutoff or post-hoc reciprocity projection. Independent degree-four audit.
"""
import numpy as np
from scipy.linalg import lstsq
from exterior_bem import elements
from bem_linear import COL,CHECK,targets,operators,observe,far_gram
from bem_linear_adaptive import MARK
from split_radiation import relative

TRAIN=np.vstack([COL,MARK])
# Positive symmetric Dunavant degree-four rule on the reference triangle,
# weights normalized to one, then multiplied by physical triangle area.
def permutations(a,b):
    return np.array([[a,b,b],[b,a,b],[b,b,a]])
AUDIT=np.vstack([permutations(.816847572980459,.091576213509771),
                 permutations(.108103018168070,.445948490915965)])
WEIGHTS=np.repeat([.109951743655322,.223381589678011],3)

def audit_targets(t):
    x,n,w,owner=targets(t,AUDIT)
    a=elements(t)[2]
    return x,n,(a[:,None]*WEIGHTS[None,:]).ravel(),owner

def fit(t,V,k,order,derivative_only=True):
    x,n,w,owner=targets(t,TRAIN)
    if V.shape[0]!=len(x):raise ValueError('training field dimensions')
    _,D=operators(t,x,n,owner,k,order,derivative_only=derivative_only)
    sw=np.sqrt(w)[:,None];A=sw*D;B=-sw*V
    scales=np.linalg.norm(A,axis=0)
    if np.any(scales<=0):raise ValueError('zero column in trace')
    # QR with column pivoting; reject rank loss rather than accepting
    # truncated unknowns. No ridge penalty or modified acoustic equation.
    q,_,rank,_=lstsq(A/scales[None,:],B,cond=1e-12,lapack_driver='gelsy')
    if rank!=A.shape[1]:raise ValueError('rank-deficient oversampled trace')
    q=q/scales[:,None]
    R=A@q-B
    normal=np.linalg.norm(A.conj().T@R)/max(np.linalg.norm(A)*np.linalg.norm(B),1e-30)
    return q,dict(rank=int(rank),unknowns=A.shape[1],equations=A.shape[0],
        trainingResidual=relative(A@q,B),normalEquationResidual=float(normal),
        coefficientNorm=float(np.linalg.norm(q)))

def audit(t,q,V,k,points,order,rho=1.204,c=343.):
    x,n,w,owner=audit_targets(t);G,D=operators(t,x,n,owner,k,order)
    R=np.sqrt(w)[:,None]*(D@q+V);T=np.sqrt(w)[:,None]*V
    Z=1j*rho*c*k*(V.T@(w[:,None]*(G@q)));P=1j*rho*c*k*observe(t,q,points,k,order)
    H=(Z+Z.conj().T)/2;expected=rho*c*k*k/(4*np.pi)*far_gram(t,q,k,surface_order=order)
    den=max(np.linalg.norm(Z),1e-30)
    rep=dict(heldoutResidual=float(np.linalg.norm(R)/max(np.linalg.norm(T),1e-30)),
        heldoutWorstColumn=float(max(np.linalg.norm(R,axis=0)/np.maximum(np.linalg.norm(T,axis=0),1e-30))),
        reciprocity=relative(Z,Z.T),powerRelative=relative(H,expected),
        passivityMinRelative=float(min(np.linalg.eigvalsh(H))/den))
    rep['gate']=max(rep['heldoutResidual'],rep['heldoutWorstColumn'])<=.05 and rep['reciprocity']<=.01 and rep['powerRelative']<=.01 and rep['passivityMinRelative']>=-1e-8
    return Z,P,rep
