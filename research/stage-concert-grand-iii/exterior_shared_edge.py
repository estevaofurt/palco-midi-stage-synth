"""Four-dimensional Duffy transform for two fan triangles sharing an edge.
Split edge coordinates into t>=s and t<=s; split the three vanishing
coordinates (r,q,d) into sectors of their maximum. Jacobian R**2
removes the integrable 1/R singularity. No kernel modification.
Other fan triangle pairs retain tensor integration.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss
from board_contour import properties
from exterior_pair_stream import pair_integrals
from scipy.spatial.distance import cdist

def gauss(order):
    if not isinstance(order,int) or isinstance(order,bool) or order<2:raise ValueError('invalid quadrature order')
    x,w=leggauss(order);return (x+1)/2,w/2

def shared_edge(p,q,tol=1e-9):
    x=p.world(p.poly);y=q.world(q.poly);d=cdist(x,y);pairs=[]
    for i in range(len(x)):
        ii=(i+1)%len(x)
        for j in range(len(y)):
            jj=(j+1)%len(y)
            if max(d[i,j],d[ii,jj])<tol:pairs.append((i,j,False))
            elif max(d[i,jj],d[ii,j])<tol:pairs.append((i,j,True))
    if len(pairs)!=1:raise ValueError('exactly one shared polygon edge required')
    return pairs[0]

def fan_triangle(p,i):
    x=p.world(p.poly);_,c,_=properties(p.poly)
    return x[i],x[(i+1)%len(x)],p.world(c)

def tensor_triangle(p,i,order):
    a,b,c=fan_triangle(p,i);z,w=gauss(order);u,v=np.meshgrid(z,z,indexing='ij')
    u=u.ravel();v=v.ravel()
    x=c+u[:,None]*((1-v[:,None])*(a-c)+v[:,None]*(b-c))
    wt=(w[:,None]*w[None,:]).ravel()*u*np.linalg.norm(np.cross(a-c,b-c))
    return x,wt[:,None]*p.basis(p.local(x))

def edge_duffy(p,q,k,order):
    k=np.asarray(k,float)
    if k.ndim!=1 or not len(k) or not np.isfinite(k).all() or np.any(k<=0):raise ValueError('invalid wave numbers')
    i,j,reverse=shared_edge(p,q);a,b,c=fan_triangle(p,i);aa,bb,e=fan_triangle(q,j)
    if reverse:aa,bb=bb,aa
    J=np.linalg.norm(np.cross(b-a,c-a))*np.linalg.norm(np.cross(bb-aa,e-aa))
    if J<=0:raise ValueError('degenerate fan triangles')
    z,w=gauss(order);R,U,V=np.meshgrid(z,z,z,indexing='ij')
    R=R.ravel();U=U.ravel();V=V.ravel()
    W=(w[:,None,None]*w[None,:,None]*w[None,None,:]).ravel()*R**2
    X=np.zeros((len(k),p.basis.count,q.basis.count));S=np.zeros_like(X)
    area=0.
    for s,ws in zip(z,w):
        for direction in (-1,1):
            span=s if direction==-1 else 1-s
            for axis in range(3):
                coords=[R*U,R*V];coords.insert(axis,R);r,t,d=coords
                s2=s+direction*span*d
                x=(1-r[:,None])*(a+s*(b-a))+r[:,None]*c
                y=(1-t[:,None])*(aa+s2[:,None]*(bb-aa))+t[:,None]*e
                D=np.linalg.norm(x-y,axis=1)
                if D.min()<=0:raise ValueError('coincident transformed nodes')
                wt=J*ws*span*W*(1-r)*(1-t)
                A=p.basis(p.local(x));B=q.basis(q.local(y))
                area+=wt.sum()
                for f,kl in enumerate(k):
                    S[f]+=A.T@((wt*np.sinc(kl*D/np.pi))[:,None]*B)
                    X[f]+=A.T@((wt*np.cos(kl*D)/D)[:,None]*B)
    if abs(area-J/4)>1e-10*J or not np.isfinite(X).all():raise ValueError('edge transform failed area audit')
    return S,X,dict(areaProduct=float(area),expectedAreaProduct=float(J/4),order=order,sharedEdges=[i,j])

def corrected_pair(p,q,k,outer,edge_order,*,block=64):
    i,j,_=shared_edge(p,q)
    _,x,w,A=p.samples(outer);_,y,v,B=q.samples(outer)
    R,X,_=pair_integrals(x,w[:,None]*A,y,v[:,None]*B,k,mutual=True,block=block)
    x,A=tensor_triangle(p,i,outer);y,B=tensor_triangle(q,j,outer)
    r,z,_=pair_integrals(x,A,y,B,k,mutual=True,block=block)
    s,t,rep=edge_duffy(p,q,k,edge_order)
    return R-r+s,X-z+t,rep
