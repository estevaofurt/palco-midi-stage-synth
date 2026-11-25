"""Memory-conscious P1 operator application; same discrete equations.
Derivative-only assembly skips the pressure matrix and singular pressure
self integral. Surface audit streams blocks instead of storing full traces.
Experimental until compared numerically with the existing solver.
"""
import numpy as np
from scipy.linalg import solve
from bem_linear import COL,targets,operators,observe,far_gram
from bem_oversampled import audit_targets
from split_radiation import relative

def derivative(t,x,n,owner,k,order):
    return operators(t,x,n,owner,k,order,derivative_only=True)[1]

def fit(t,V,k,order):
    x,n,w,owner=targets(t,COL);D=derivative(t,x,n,owner,k,order)
    q=solve(D,-V,assume_a='gen')
    return q,dict(collocationResidual=relative(D@q,-V),coefficientNorm=float(np.linalg.norm(q)))

def trace(t,q,x,n,owner,k,order,batch=24):
    if batch<1:raise ValueError('batch must be positive')
    P=np.empty((len(x),q.shape[1]),complex);U=np.empty_like(P)
    for start in range(0,len(x),batch):
        sl=slice(start,min(start+batch,len(x)))
        G,D=operators(t,x[sl],n[sl],owner[sl],k,order)
        P[sl]=G@q;U[sl]=-D@q
    return P,U

def audit(t,q,V,k,points,order,rho=1.204,c=343.,batch=24):
    x,n,w,owner=audit_targets(t);p,u=trace(t,q,x,n,owner,k,order,batch)
    R=np.sqrt(w)[:,None]*(V-u);T=np.sqrt(w)[:,None]*V
    Z=1j*rho*c*k*(V.T@(w[:,None]*p));P=1j*rho*c*k*observe(t,q,points,k,order)
    H=(Z+Z.conj().T)/2;expected=rho*c*k*k/(4*np.pi)*far_gram(t,q,k,surface_order=order)
    den=max(np.linalg.norm(Z),1e-30)
    rep=dict(heldoutResidual=float(np.linalg.norm(R)/max(np.linalg.norm(T),1e-30)),
        heldoutWorstColumn=float(max(np.linalg.norm(R,axis=0)/np.maximum(np.linalg.norm(T,axis=0),1e-30))),
        reciprocity=relative(Z,Z.T),powerRelative=relative(H,expected),
        passivityMinRelative=float(min(np.linalg.eigvalsh(H))/den))
    rep['gate']=max(rep['heldoutResidual'],rep['heldoutWorstColumn'])<=.05 and rep['reciprocity']<=.01 and rep['powerRelative']<=.01 and rep['passivityMinRelative']>=-1e-8
    # Storage of full trace matrices only, not process peak RSS.
    rep['denseTraceMatrixBytes']=int(2*len(x)*len(q)*np.dtype(complex).itemsize)
    rep['streamTraceMatrixBytes']=int(2*min(batch,len(x))*len(q)*np.dtype(complex).itemsize)
    return Z,P,rep
