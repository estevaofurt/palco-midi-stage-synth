"""Per-port residual marking for the existing P1 discretization.
No changes to acoustic equations, boundary conditions or approval gates.
"""
import numpy as np
from bem_linear import targets
from bem_linear_adaptive import MARK,budget_refine
from bem_p1_stream import derivative

def contribution(t,q,V,k,order):
    x,n,w,owner=targets(t,MARK)
    D=derivative(t,x,n,owner,k,order)
    R=np.sqrt(w)[:,None]*(D@q+V)
    T=np.sqrt(w)[:,None]*V
    den=np.sum(abs(T)**2,axis=0)
    if np.any(den<=1e-60):raise ValueError('unobservable prescribed velocity column')
    return (abs(R)**2/den[None,:]).reshape(len(t),len(MARK),-1).sum(1)

def scores(contributions,policy):
    """Equal sum or targeted weighting of worst residual columns.
    A smooth weighting avoids throwing away the remaining excitation modes.
    """
    A=np.concatenate([np.asarray(c,float) for c in contributions],axis=1)
    if A.ndim!=2 or not np.isfinite(A).all() or np.any(A<0):raise ValueError('invalid residual contributions')
    energy=A.sum(0)
    if policy=='balanced':weights=np.ones_like(energy)
    elif policy=='worst':
        peak=max(float(energy.max()),1e-60)
        weights=(energy/peak)**2
        weights=.1+.9*weights
    else:raise ValueError('unknown marking policy')
    return A@weights,dict(worstColumnResidual=float(np.sqrt(energy.max())),
        minWeight=float(weights.min()),maxWeight=float(weights.max()),
        weightedColumns=len(weights))
