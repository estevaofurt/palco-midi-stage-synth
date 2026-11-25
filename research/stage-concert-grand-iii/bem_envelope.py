"""Triangulate the exact upper envelope without a convex-hull approximation."""
import numpy as np
from board_contour import properties
from exterior_bem import subdivide,topology,elements

def triangulate(surfaces,level):
    tris=[];labels=[]
    for i,s in enumerate(surfaces):
        p=s['panel'];_,center,_=properties(p.poly);c=p.world(center[None,:])[0]
        xyz=p.world(p.poly);t=np.array([[c,a,b] for a,b in zip(xyz,np.roll(xyz,-1,axis=0))])
        _,n,_=elements(t);flip=n@s['normal']<0;t[flip]=t[flip][:,[0,2,1]]
        for _ in range(level):t=subdivide(t)
        tris.append(t);labels.extend([i]*len(t))
    t=np.concatenate(tris);labels=np.asarray(labels)
    rep=topology(t)
    if not rep['gate']:raise ValueError('nonconforming envelope: '+str(rep))
    return t,labels,rep

def velocities(surfaces,ports,x,labels):
    offsets=np.r_[0,np.cumsum([p.basis.count for p in ports])]
    V=np.zeros((len(x),offsets[-1]))
    for i,s in enumerate(surfaces):
        j=s['port'];idx=labels==i
        if j is not None:
            p=s['panel'];V[idx,offsets[j]:offsets[j+1]]=p.basis(p.local(x[idx]))
    return V
