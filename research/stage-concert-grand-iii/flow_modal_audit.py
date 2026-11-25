"""Audit flow differences in common orthogonal coordinates.
Each panel basis has mass I/area, so physical velocity L2 weights
are 1/area. Retain the original unweighted coefficient comparison.
"""
import numpy as np
from split_radiation import relative

def audit_flow(low,high,T,counts,areas):
    low,high,T=map(np.asarray,(low,high,T));areas=np.asarray(areas,float)
    if low.shape!=high.shape or low.ndim!=2 or T.ndim!=2 or T.shape[0]!=len(high) or sum(counts)!=len(high) or len(counts)!=len(areas) or any(n<=0 for n in counts) or np.any(areas<=0):
        raise ValueError('incompatible flow geometry')
    if not all(np.isfinite(x).all() for x in (low,high,T,areas)) or relative(T.T@T,np.eye(T.shape[1]))>1e-8:
        raise ValueError('invalid flow embedding')
    resolved=T@(T.T@high);omitted=high-resolved;delta=low-resolved
    if relative(T@(T.T@low),low)>1e-8:raise ValueError('low flow outside declared subspace')
    weights=np.repeat(1/np.sqrt(areas),counts)[:,None]
    norm=lambda x:float(np.linalg.norm(weights*x))
    den=max(norm(high),1e-30);total=norm(low-high)/den
    res=norm(delta)/den;miss=norm(omitted)/den
    rows=[];offset=0
    for i,(n,A) in enumerate(zip(counts,areas)):
        sl=slice(offset,offset+n);q=high[sl];e=low[sl]-q
        rows.append(dict(panel=i,areaM2=float(A),velocityRelative=relative(low[sl],q),
            errorEnergyFraction=float(np.linalg.norm(e)**2/A/max(norm(low-high)**2,1e-60)),
            omittedEnergyRelative=float(np.linalg.norm(omitted[sl])**2/A/den**2),
            highVelocityEnergyFraction=float(np.linalg.norm(q)**2/A/den**2)))
        offset+=n
    return dict(coefficientRelative=relative(low,high),physicalVelocityRelative=total,
        resolvedRelative=res,omittedRelative=miss,orthogonalClosure=abs(total**2-res**2-miss**2),
        panels=rows)

def pressure_defect(Zu,Zl,Ze,F,T,nb):
    from scipy.linalg import block_diag
    A=block_diag(Zu[nb:,nb:],Zl[nb:,nb:])+Ze
    B=np.vstack([Zu[nb:,:nb],-Zl[nb:,:nb]])
    R=A@F-B;den=max(np.linalg.norm(B),1e-30)
    return dict(fullRelative=float(np.linalg.norm(R)/den),
        resolvedRelative=float(np.linalg.norm(T.T@R)/den),
        omittedRelative=float(np.linalg.norm(R-T@(T.T@R))/den))
