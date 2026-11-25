"""Localize residual energy at physical creases and artificial mesh edges.
Each triangle is partitioned into centroid-to-edge sectors. Sector
assignment is a geometric diagnostic, not an asymptotic singularity fit.
"""
import numpy as np
from exterior_bem import elements,gauss,topology
from bem_adaptive import edge
from bem_edge_audit import edge_samples
from bem_p1_static_moments import operators

def inventory(t,labels,kinds):
    t=np.asarray(t,float);labels=np.asarray(labels,int)
    if labels.shape!=(len(t),) or np.any(labels<0) or np.any(labels>=len(kinds)) or not topology(t)['gate']:
        raise ValueError('invalid closed mesh or surface labels')
    _,n,_=elements(t);edges={}
    for i,tri in enumerate(t):
        for j in range(3):
            edges.setdefault(edge(tri[j],tri[(j+1)%3]),[]).append((i,j))
    classes=np.empty((len(t),3),dtype='<U32');angles=np.zeros((len(t),3))
    for pair in edges.values():
        if len(pair)!=2:raise ValueError('nonmanifold edge')
        (i,j),(h,k)=pair
        angle=float(np.degrees(np.arctan2(np.linalg.norm(np.cross(n[i],n[h])),np.clip(n[i]@n[h],-1,1))))
        crease=angle>1e-5
        transition=(kinds[labels[i]]=='rigid')!=(kinds[labels[h]]=='rigid')
        if crease:kind='crease-port-transition' if transition else 'crease'
        elif transition:kind='coplanar-port-transition'
        elif labels[i]!=labels[h]:kind='coplanar-panel-seam'
        else:kind='mesh-edge'
        classes[i,j]=classes[h,k]=kind;angles[i,j]=angles[h,k]=angle
    return classes,angles

def summarize(classes,E,T,A):
    """E and T are nonnegative integrated squared residual/target arrays,
    with shape (triangle,sector,radial band,port). A is integrated area.
    """
    E,T,A=map(np.asarray,(E,T,A))
    if E.shape!=T.shape or E.ndim!=4 or E.shape[:2]!=classes.shape or A.shape!=E.shape[:3]:
        raise ValueError('incompatible localization arrays')
    if not all(np.isfinite(x).all() and np.all(x>=0) for x in (E,T,A)):
        raise ValueError('invalid localization values')
    target=T.sum(axis=(0,1,2));error=E.sum(axis=(0,1,2))
    if min(target)<=0 or A.sum()<=0:raise ValueError('unobservable target')
    total=float(error.sum());den=float(target.sum())
    normalized=E/target[None,None,None,:]
    rows=[]
    for name in sorted(set(classes.ravel())):
        mask=classes==name
        e=E[mask];a=A[mask];v=normalized[mask]
        rows.append(dict(kind=name,sectors=int(mask.sum()),areaFraction=float(a.sum()/A.sum()),
            residualEnergyFraction=float(e.sum()/max(total,1e-60)),
            normalizedPortEnergyFraction=float(v.sum()/max(normalized.sum(),1e-60)),
            bandEnergyFractions=(e.sum(axis=(0,2))/max(total,1e-60)).tolist(),
            bandAreaFractions=(a.sum(axis=0)/A.sum()).tolist()))
    closure=abs(sum(r['residualEnergyFraction'] for r in rows)-(1. if total>0 else 0.))
    return dict(heldoutResidual=float(np.sqrt(total/den)),heldoutWorstColumn=float(np.sqrt(max(error/target))),
        totalResidualEnergy=total,area=float(A.sum()),energyClosure=float(closure),
        categories=rows,elementIndicator=normalized.sum(axis=(1,2,3)).tolist(),
        sectorIndicator=normalized.sum(axis=(2,3)).tolist())

def localize(t,labels,kinds,q,velocity,k,outer,inner,batch=24,*,exact_bands=False):
    classes,angles=inventory(t,labels,kinds)
    if exact_bands:
        from bem_edge_bands import band_samples
        y,w,sector,bands=band_samples(t,outer)
    else:
        y,w=edge_samples(t,outer)
        z,_=gauss(outer);d=np.repeat(z*z,outer)
        # Legacy point classification, retained to reproduce earlier meshes.
        bands=np.tile(np.searchsorted([.1,.4],d,side='right'),3)
        sector=np.repeat(np.arange(3),outer*outer)
    _,n,_=elements(t);N,Q=y.shape[:2]
    x=y.reshape(-1,3);w=w.ravel();n=np.repeat(n,Q,axis=0)
    E=np.zeros((N,3,3,q.shape[1]));T=np.zeros_like(E);A=np.zeros(E.shape[:3])
    for start in range(0,len(x),batch):
        stop=min(start+batch,len(x));sl=slice(start,stop)
        ids=np.arange(start,stop);o=ids//Q;s=sector[ids%Q];b=bands[ids%Q]
        V=np.asarray(velocity(x[sl],o));_,D=operators(t,x[sl],n[sl],o,k,inner,True)
        if V.shape!=(len(ids),q.shape[1]):raise ValueError('invalid velocity callback')
        np.add.at(E,(o,s,b),w[sl,None]*abs(-D@q-V)**2)
        np.add.at(T,(o,s,b),w[sl,None]*abs(V)**2)
        np.add.at(A,(o,s,b),w[sl])
    rep=summarize(classes,E,T,A)
    rep.update(outerOrder=outer,innerOrder=inner,bandLimits=[0.,.1,.4,1.],
        maximumDihedralDeg=float(angles.max()),targetPoints=len(x),
        exactBandIntegration=bool(exact_bands))
    return rep
