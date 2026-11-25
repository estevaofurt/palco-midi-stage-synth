"""Duffy integration on pairs of fan triangles meeting at one vertex.
Radial coordinates r,t from the shared vertex are split into the
two sectors r>=t and t>=r. The product Jacobian r*t*R removes
the integrable 1/R kernel singularity without smoothing the kernel.
"""
import numpy as np
from scipy.spatial.distance import cdist
from exterior_shared_edge import gauss,fan_triangle,tensor_triangle
from exterior_pair_stream import pair_integrals
from split_radiation import relative

def contacts(p,q,tol=1e-9):
    rows=[]
    for i in range(len(p.poly)):
        x=np.asarray(fan_triangle(p,i))
        for j in range(len(q.poly)):
            y=np.asarray(fan_triangle(q,j))
            ids=np.argwhere(cdist(x,y)<tol)
            if len(ids):
                if len(ids)>2 or len(np.unique(ids[:,0]))!=len(ids) or len(np.unique(ids[:,1]))!=len(ids):
                    raise ValueError('overlapping or ambiguous fan triangles')
                rows.append((i,j,len(ids),ids.tolist()))
    return rows

def vertex_duffy(p,q,i,j,k,order):
    x=np.asarray(fan_triangle(p,i));y=np.asarray(fan_triangle(q,j))
    ids=np.argwhere(cdist(x,y)<1e-9)
    if len(ids)!=1:raise ValueError('exactly one shared vertex required')
    a,b=ids[0];x=np.roll(x,-int(a),axis=0);y=np.roll(y,-int(b),axis=0)
    J=np.linalg.norm(np.cross(x[1]-x[0],x[2]-x[0]))*np.linalg.norm(np.cross(y[1]-y[0],y[2]-y[0]))
    k=np.asarray(k,float)
    if J<=0 or k.ndim!=1 or not len(k) or not np.isfinite(k).all() or np.any(k<=0):raise ValueError('invalid geometry or wave numbers')
    z,w=gauss(order);R,U,V=np.meshgrid(z,z,z,indexing='ij')
    R=R.ravel();U=U.ravel();V=V.ravel()
    W=(w[:,None,None]*w[None,:,None]*w[None,None,:]).ravel()
    S=np.zeros((len(k),p.basis.count,q.basis.count));X=np.zeros_like(S);area=0.
    # V is the first triangle's angular coordinate, s the second.
    A=(1-V[:,None])*(x[1]-x[0])+V[:,None]*(x[2]-x[0])
    for s,ws in zip(z,w):
        B=(1-s)*(y[1]-y[0])+s*(y[2]-y[0])
        for r,t in ((R,R*U),(R*U,R)):
            a=x[0]+r[:,None]*A;b=y[0]+t[:,None]*B
            D=np.linalg.norm(a-b,axis=1)
            if D.min()<=0:raise ValueError('coincident transformed nodes')
            wt=J*ws*W*r*t*R;area+=wt.sum()
            P=p.basis(p.local(a));Q=q.basis(q.local(b))
            for f,kl in enumerate(k):
                S[f]+=P.T@((wt*np.sinc(kl*D/np.pi))[:,None]*Q)
                X[f]+=P.T@((wt*np.cos(kl*D)/D)[:,None]*Q)
    if abs(area-J/4)>1e-10*J or not np.isfinite(X).all() or not np.isfinite(S).all():raise ValueError('vertex integral failed area audit')
    return S,X,dict(areaProduct=float(area),expectedAreaProduct=float(J/4))

def vertex_delta(p,q,k,outer,order,*,block=64):
    """Return only the reactive delta relative to the same tensor rule.
    Keep edge-sharing pairs and all resistive blocks untouched.
    """
    k=np.asarray(k,float);X=np.zeros((len(k),p.basis.count,q.basis.count))
    rows=[];smooth=np.zeros_like(X);reference=np.zeros_like(X)
    for i,j,n,_ in contacts(p,q):
        if n!=1:continue
        a,A=tensor_triangle(p,i,outer);b,B=tensor_triangle(q,j,outer)
        R,Z,_=pair_integrals(a,A,b,B,k,mutual=True,block=block)
        S,Y,rep=vertex_duffy(p,q,i,j,k,order)
        X+=Y-Z;smooth+=S-R;reference+=R
        rows.append(dict(firstTriangle=i,secondTriangle=j,
            smoothRelative=[relative(s,r) for s,r in zip(S,R)],**rep))
    return X,dict(vertexPairs=len(rows),pairs=rows,
        smoothControlMaximum=max((v for row in rows for v in row['smoothRelative']),default=0.),
        aggregateSmoothRelative=[float(np.linalg.norm(d)/max(np.linalg.norm(r),1e-30)) for d,r in zip(smooth,reference)])
