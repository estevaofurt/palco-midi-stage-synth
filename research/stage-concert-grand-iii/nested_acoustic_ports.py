"""Nested polynomial aperture coordinates, without changing the physical domain.
Map low-order flux coefficients into a high-order basis, and project dual
pressures by the transpose. Compare full reconstructed flows, not raw
coefficient arrays with different dimensions.
"""
import numpy as np
from scipy.linalg import block_diag
from lid_exterior import Panel
from acoustic_port_bridge import compatible,vertices,normal
from split_radiation import relative

def reduced_panels(high,counts):
    if len(high)!=len(counts):raise ValueError('incompatible port counts')
    return [Panel(vertices(p),normal(p),n) for p,n in zip(high,counts)]

def embedding(high,low,order=16):
    if len(high)!=len(low) or not high:raise ValueError('incompatible port lists')
    maps=[];errors=[];orth=[]
    for a,b in zip(high,low):
        if not compatible(a,b) or a.basis.count<b.basis.count or abs(a.basis.area-b.basis.area)>1e-10:
            raise ValueError('incompatible nested port geometry')
        _,x,w,V=b.samples(order);U=a.basis(a.local(x))
        T=a.basis.area*(U.T@(w[:,None]*V))
        errors.append(relative(U@T,V));orth.append(relative(T.T@T,np.eye(len(T.T))))
        maps.append(T)
    rep=dict(fieldRelative=max(errors),orthogonalityRelative=max(orth))
    rep['gate']=max(rep.values())<=1e-8
    if not rep['gate']:raise ValueError('invalid nested embedding')
    return block_diag(*maps),rep

def project(Z,P,T):
    Z,P,T=map(np.asarray,(Z,P,T))
    if Z.ndim!=2 or Z.shape[0]!=Z.shape[1] or T.ndim!=2 or T.shape[0]!=len(Z) or P.ndim!=2 or P.shape[1]!=len(Z):
        raise ValueError('incompatible projection dimensions')
    if np.iscomplexobj(T) or not all(np.isfinite(x).all() for x in (Z,P,T)) or relative(T.T@T,np.eye(T.shape[1]))>1e-8:
        raise ValueError('invalid embedding')
    return T.T@Z@T,P@T

def coupled_projection(Zu,Pu,Zl,Pl,Ze,Pe,Tu,Tl,nb):
    from dual_cavity_reference import couple
    Tu,Tl=map(np.asarray,(Tu,Tl))
    T=block_diag(Tu,Tl)
    zu,pu=project(Zu,Pu,block_diag(np.eye(nb),Tu))
    zl,pl=project(Zl,Pl,block_diag(np.eye(nb),Tl))
    ze,pe=project(Ze,Pe,T)
    Y,pi,plow,pfar,F,r=couple(zu,pu,zl,pl,ze,pe,nb,reference_kind='common-free-space-monopole')
    Fhigh=T@F
    r['projectedWorkRelative']=relative(F.conj().T@ze@F,Fhigh.conj().T@Ze@Fhigh)
    r['gate']=bool(r['gate'] and r['projectedWorkRelative']<=1e-8)
    return Y,pi,plow,pfar,Fhigh,r
