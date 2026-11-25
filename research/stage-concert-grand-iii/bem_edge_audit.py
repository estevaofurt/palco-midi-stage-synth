"""Independent positive edge-graded surface quadrature.
Split each flat triangle into three centroid-to-edge sectors.
The map d=u**2 clusters quadrature near each original edge, while
the Jacobian includes both the radial stretching and sector area.
No change of density, geometry or physical acceptance thresholds.
"""
import numpy as np
from exterior_bem import elements,gauss

def edge_samples(t,order):
    t=np.asarray(t,float)
    if not isinstance(order,int) or order<2:raise ValueError('invalid quadrature order')
    z,w=gauss(order);u,v=np.meshgrid(z,z,indexing='ij');u=u.ravel();v=v.ravel()
    wt=(w[:,None]*w[None,:]).ravel();d=u*u
    center=t.mean(1);area=elements(t)[2];xs=[];ws=[]
    for j in range(3):
        edge=(1-v[None,:,None])*t[:,j,None,:]+v[None,:,None]*t[:,(j+1)%3,None,:]
        x=(1-d[None,:,None])*edge+d[None,:,None]*center[:,None,:]
        weight=(2*area[:,None]/3)*(wt*(1-d)*2*u)[None,:]
        xs.append(x);ws.append(weight)
    return np.concatenate(xs,axis=1),np.concatenate(ws,axis=1)
