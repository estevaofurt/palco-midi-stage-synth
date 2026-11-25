"""Diagnose the exterior acoustic power discrepancy without changing the solve.

Prescribed work = computed-velocity work + boundary-mismatch work.
Computed-velocity work is compared against an independent radiation Gram.
All work matrices use identical pressure samples and positive quadrature.
This is a diagnostic partition, not an alternative approval criterion.
"""
import numpy as np
from exterior_bem import elements,samples
from bem_linear import operators,far_gram
from split_radiation import relative

def herm(A):
    return (A+A.conj().T)/2

def partition(prescribed,computed,far):
    prescribed,computed,far=map(np.asarray,(prescribed,computed,far))
    if prescribed.shape!=computed.shape or prescribed.shape!=far.shape or prescribed.ndim!=2 or prescribed.shape[0]!=prescribed.shape[1]:
        raise ValueError('incompatible work matrices')
    if not all(np.isfinite(x).all() for x in (prescribed,computed,far)):
        raise ValueError('nonfinite work matrix')
    Rp,Rv,Rf=map(herm,(prescribed,computed,far))
    boundary=Rp-Rv
    integration=Rv-Rf
    total=Rp-Rf
    den=max(np.linalg.norm(Rf),1e-30)
    norm=lambda x:float(np.linalg.norm(x)/den)
    # The terms can cancel: do not add relative norms as scalars.
    alignment=float(np.vdot(boundary,integration).real/max(np.linalg.norm(boundary)*np.linalg.norm(integration),1e-30))
    return dict(totalPowerRelative=norm(total),boundaryWorkRelative=norm(boundary),
        computedWorkRelative=norm(integration),partitionClosure=norm(total-boundary-integration),
        errorAlignment=alignment,computedWorkTrace=float(np.trace(Rv).real),
        prescribedWorkTrace=float(np.trace(Rp).real),farWorkTrace=float(np.trace(Rf).real),
        computedPassivityMinRelative=float(np.linalg.eigvalsh(Rv).min()/den),
        prescribedPassivityMinRelative=float(np.linalg.eigvalsh(Rp).min()/den))

def integrate(t,q,velocity,k,outer,inner,rho=1.204,c=343.,batch=24):
    """Stream whole-surface work quadrature, separate from fit/audit points.

    The velocity callback takes points and element owners and returns the
    prescribed real basis fields. Actual velocity is the exterior trace
    of the same computed single-layer density, including the jump.
    """
    y,w=samples(t,outer);_,n,_=elements(t);N,Q=y.shape[:2]
    owner=np.repeat(np.arange(N),Q);x=y.reshape(-1,3)
    n=np.repeat(n,Q,axis=0);w=w.ravel()
    ncol=q.shape[1]
    P=np.zeros((ncol,ncol),complex);C=np.zeros_like(P)
    residual=np.zeros(ncol);target=np.zeros(ncol)
    for i in range(0,len(x),batch):
        sl=slice(i,min(i+batch,len(x)))
        V=np.asarray(velocity(x[sl],owner[sl]))
        G,D=operators(t,x[sl],n[sl],owner[sl],k,inner)
        pressure=1j*rho*c*k*(G@q);actual=-D@q
        wt=w[sl,None]
        P+=V.conj().T@(wt*pressure);C+=actual.conj().T@(wt*pressure)
        residual+=np.sum(wt*abs(actual-V)**2,axis=0)
        target+=np.sum(wt*abs(V)**2,axis=0)
    return P,C,dict(heldoutResidual=float(np.sqrt(residual.sum()/max(target.sum(),1e-60))),
        heldoutWorstColumn=float(np.sqrt(np.max(residual/np.maximum(target,1e-60)))),
        reciprocity=relative(P,P.T),outerOrder=outer,innerOrder=inner)

def audit(t,q,velocity,k,outer,inner,angular=28,source_order=7,rho=1.204,c=343.):
    P,C,r=integrate(t,q,velocity,k,outer,inner,rho,c)
    F=rho*c*k*k/(4*np.pi)*far_gram(t,q,k,order=angular,surface_order=source_order)
    return P,C,F,dict(**r,**partition(P,C,F),angularOrder=angular,sourceOrder=source_order)
