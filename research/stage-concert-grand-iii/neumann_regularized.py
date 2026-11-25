"""Numerical MFS stabilization with weighted column scaling and spectral filtering.
Selection uses boundary tuning points only, never the final audit or far field.
Regularization of equivalent-source coefficients is not physical damping.
"""
import numpy as np
from scipy.linalg import svd
from rigid_scattering import normal_derivative
from split_radiation import relative

def residual(A,q,B,w):
    R=np.sqrt(w)[:,None]*(A@q-B)
    T=np.sqrt(w)[:,None]*B
    cols=np.linalg.norm(R,axis=0)/np.maximum(np.linalg.norm(T,axis=0),1e-30)
    return dict(aggregate=relative(R+T,T),worstColumn=float(max(cols)))

def candidates(A,B,w,At,Bt,wt,levels=(1e-2,3e-3,1e-3,3e-4,1e-4,3e-5,1e-5,1e-6,1e-8)):
    A,B,At,Bt=map(np.asarray,(A,B,At,Bt));w=np.asarray(w);wt=np.asarray(wt)
    if min(w)<=0 or min(wt)<=0 or min(levels)<=0:raise ValueError('positive weights and cutoffs required')
    sw=np.sqrt(w)[:,None];C=sw*A;D=sw*B
    scale=np.linalg.norm(C,axis=0)
    if np.any(scale<=0):raise ValueError('zero equivalent source column')
    U,s,Vh=svd(C/scale[None,:],full_matrices=False,check_finite=True)
    d=U.conj().T@D
    choices=[];best=None
    for level in levels:
        keep=s>=s[0]*level
        Q=Vh[keep].conj().T@(d[keep]/s[keep,None])
        Q=Q/scale[:,None]
        training=residual(A,Q,B,w);tuning=residual(At,Q,Bt,wt)
        score=max(tuning.values())
        row=dict(cutoff=level,rank=int(sum(keep)),training=training,tuning=tuning,
            coefficientNorm=float(np.linalg.norm(Q)),score=score)
        choices.append(row)
        if best is None or score<best[0]:best=(score,Q,row)
    return best[1],dict(selected=best[2],candidates=choices,columns=A.shape[1],
        singularRatio=float(s[-1]/s[0]))

def fit(train,tune,sources,k,levels=(1e-2,3e-3,1e-3,3e-4,1e-4,3e-5,1e-5,1e-6,1e-8)):
    x,n,w,V=train;xt,nt,wt,Vt=tune
    A=normal_derivative(x,n,sources,k);At=normal_derivative(xt,nt,sources,k)
    return candidates(A,-V,w,At,-Vt,wt,levels)
