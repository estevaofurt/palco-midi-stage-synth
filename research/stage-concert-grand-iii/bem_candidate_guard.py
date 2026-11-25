"""Validate a conforming refinement against its archived parent mesh."""
import numpy as np
from exterior_bem import elements,topology
from bem_mesh_guard import signature

def validate_candidate(t,l,tt,ll,parents,entry,budget):
    t,l,tt,ll,parents=map(np.asarray,(t,l,tt,ll,parents))
    if not len(t)<len(tt)<=budget or parents.shape!=(len(tt),) or not np.issubdtype(parents.dtype,np.integer) or np.any(parents<0) or np.any(parents>=len(t)):
        raise ValueError('invalid candidate parent mapping or budget')
    if not np.issubdtype(ll.dtype,np.integer) or not np.array_equal(ll,l[parents]):
        raise ValueError('candidate surface labels changed')
    if entry.get('gate') is not True or entry.get('oldElements')!=len(t) or entry.get('newElements')!=len(tt) or entry.get('elementBudget')!=budget or entry.get('meshSha256')!=signature(tt,ll):
        raise ValueError('candidate evidence mismatch')
    a,b=topology(t),topology(tt)
    if not a['gate'] or not b['gate'] or abs(a['volume']-b['volume'])>1e-10:
        raise ValueError('candidate topology changed')
    _,n,A=elements(t);_,nn,AA=elements(tt)
    areaError=float(np.max(abs(np.bincount(parents,weights=AA,minlength=len(t))-A)/A))
    normalError=float(np.max(np.linalg.norm(nn-n[parents],axis=1)))
    # Verify every child vertex is inside its own parent, not merely
    # coplanar with the same normal and conserved aggregate area.
    P=t[parents];v=tt-P[:,:1];e=P[:,1]-P[:,0];f=P[:,2]-P[:,0]
    ee=np.sum(e*e,axis=1);ff=np.sum(f*f,axis=1);ef=np.sum(e*f,axis=1)
    ve=np.einsum('tvd,td->tv',v,e);vf=np.einsum('tvd,td->tv',v,f);det=ee*ff-ef*ef
    u=(ff[:,None]*ve-ef[:,None]*vf)/det[:,None]
    w=(ee[:,None]*vf-ef[:,None]*ve)/det[:,None]
    plane=float(np.max(abs(np.einsum('tvd,td->tv',v,n[parents]))))
    outside=float(max(0.,-u.min(),-w.min(),(u+w-1).max()))
    if areaError>1e-9 or normalError>1e-9 or plane>1e-10 or outside>1e-9:
        raise ValueError('candidate children do not partition parent surfaces')
    return dict(gate=True,areaRelative=areaError,normalError=normalError,planeErrorM=plane,outsideBarycentric=outside,volumeError=abs(a['volume']-b['volume']))
