"""Pairwise Galerkin integration of the reciprocal weak screen operator.
Integrate unordered triangle pairs directly, adding both oriented bilinear
terms at each quadrature batch. No post-hoc matrix symmetrization.
Independent directional quadrature remains a separate convergence reference.
"""
import numpy as np
from board_contour import properties
from shared_edge_quadrature import gauss,joint_samples
from split_radiation import relative

def tri_points(t,s,u):
    return (1-u[:,None])*((1-s[:,None])*t[0]+s[:,None]*t[1])+u[:,None]*t[2]

def jac(t):
    a,b=t[1:]-t[0]
    return abs(a[0]*b[1]-a[1]*b[0])

def self_samples(t,order):
    """Split the square of triangle parameter pairs by the two coordinate
    orderings; integrate half the pair domain, with two Duffy sectors.
    Outer minimum depth u=z² resolves the physical edge gradient.
    """
    z,w=gauss(order);R,A=np.meshgrid(z,z,indexing='ij')
    r=R.ravel()**2;a=A.ravel()
    wt=(w[:,None]*w[None,:]).ravel()*2*R.ravel()*r*jac(t)**2
    for s,sw in zip(z,w):
        for v,vw in zip(z,w):
            u=v*v
            for h,j in ((r,r*a),(r*a,r)):
                s0=np.full(len(r),s);u0=np.full(len(r),u)
                s1=s+(1-s)*h;u1=u+(1-u)*j
                W=wt*sw*vw*2*v*(1-s)*(1-u)*(1-u0)*(1-u1)
                yield tri_points(t,s0,u0),tri_points(t,s1,u1),W
                yield tri_points(t,s0,u1),tri_points(t,s1,u0),W

def vertex_samples(a,b,order):
    """Triangles sharing only their fan center (last vertex)."""
    z,w=gauss(order);R,T,S=np.meshgrid(z,z,z,indexing='ij')
    r=R.ravel()**2;t=T.ravel();s=S.ravel()
    wt=(w[:,None,None]*w[None,:,None]*w[None,None,:]).ravel()*2*R.ravel()*r*jac(a)*jac(b)
    for q,qw in zip(z,w):
        for u,v in ((r,r*q),(r*q,r)):
            yield tri_points(a,t,1-u),tri_points(b,s,1-v),wt*qw*u*v

def common_edge(a,b):
    pairs=[(i,j) for i in range(3) for j in range(3) if np.linalg.norm(a[i]-b[j])<1e-12]
    if len(pairs)!=2:return None
    i,j=zip(*pairs)
    aa=a[[*i,next(k for k in range(3) if k not in i)]]
    bb=b[[*j,next(k for k in range(3) if k not in j)]]
    return aa,bb

def pair_samples(a,b,order,same=False):
    if same:
        yield from self_samples(a,order);return
    match=common_edge(a,b)
    if match is None:
        yield from vertex_samples(a,b,order);return
    aa,bb=match
    for x,y,w in joint_samples(np.c_[aa,np.zeros(3)],np.c_[bb,np.zeros(3)],order):
        yield x[:,:2],y[:,:2],w

def operators(basis,ks,order):
    ks=np.atleast_1d(ks);_,c,_=properties(basis.poly)
    tris=[np.array([a,b,c]) for a,b in zip(basis.poly,np.roll(basis.poly,-1,axis=0))]
    N=basis.evaluate(c[None,:])[0].shape[1]
    W=np.zeros((len(ks),N,N),complex)
    measure=0.;counts=dict(selfPairs=0,edgePairs=0,vertexPairs=0)
    for i,a in enumerate(tris):
        for j in range(i,len(tris)):
            b=tris[j];same=i==j
            counts['selfPairs' if same else 'edgePairs' if common_edge(a,b) is not None else 'vertexPairs']+=1
            for x,y,w in pair_samples(a,b,order,same):
                d=np.linalg.norm(x-y,axis=1)
                if min(d)<=0:raise ValueError('coincident quadrature nodes')
                V,X,Y=basis.evaluate(x);v,xx,yy=basis.evaluate(y)
                measure+=2*float(w.sum())
                for l,k in enumerate(ks):
                    g=w*np.exp(-1j*k*d)/(4*np.pi*d)
                    A=X.T@(g[:,None]*xx)+Y.T@(g[:,None]*yy)-k*k*(V.T@(g[:,None]*v))
                    W[l]+=A+A.T
    area=properties(basis.poly)[0]
    return W,dict(**counts,measureRelative=abs(measure-area**2)/area**2,
        reciprocity=max(relative(w,w.T) for w in W),order=order)
