"""Independent residual audit in the static screen energy metric.
For harmonic problems the static metric is a diagnostic, NOT a certified
error bound. Do not replace the existing weak residual gate.
"""
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from split_radiation import relative

def metric(W0):
    W0=np.asarray(W0)
    if W0.ndim!=2 or W0.shape[0]!=W0.shape[1]:raise ValueError('square static operator required')
    if relative(W0,W0.T)>1e-10 or np.linalg.norm(W0.imag)>1e-12*max(np.linalg.norm(W0),1e-30):
        raise ValueError('real reciprocal static operator required')
    return cho_factor(W0.real,lower=True)

def norm(X,factor,dual=False):
    X=np.asarray(X)
    if dual:Y=cho_solve(factor,X)
    else:
        L=np.tril(factor[0])
        Y=L.T@X
        return float(np.linalg.norm(Y))
    value=float(np.vdot(X,Y).real)
    if value<0:raise ValueError('nonpositive dual norm')
    return np.sqrt(value)

def audit(W,B,Q,W0):
    W,B,Q=map(np.asarray,(W,B,Q))
    if W.shape!=W0.shape or B.shape!=Q.shape or B.shape[0]!=len(W):
        raise ValueError('incompatible residual inputs')
    factor=metric(W0)
    R=B-W@Q;exact=np.linalg.solve(W,B);E=exact-Q
    return dict(weakRelative=relative(W@Q,B),
        dualStaticRelative=float(norm(R,factor,True)/max(norm(B,factor,True),1e-30)),
        enrichedSolutionRelative=float(norm(E,factor)/max(norm(exact,factor),1e-30)),
        enrichedResidual=relative(W@exact,B),
        staticIdentityRelative=relative(W0@E,R) if relative(W,W0)<=1e-12 else None)
