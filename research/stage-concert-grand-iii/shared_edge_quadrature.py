"""Joint Duffy quadrature for noncoplanar triangles sharing a complete edge.
The normal derivative has a weakly integrable edge singularity in the joint
four-dimensional integral. No distance cutoff or artificial offset is used.
Pairs sharing only vertices retain tensor quadrature and are audited separately.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss
from board_contour import properties
from rigid_scattering import normal_derivative
from split_radiation import relative

def gauss(order):
    z,w=leggauss(order)
    return (z+1)/2,w/2

def fan(poly,origin,axes):
    _,c,_=properties(poly);xyz=origin+np.asarray(poly)@axes.T
    center=origin+c@axes.T
    return [np.array([a,b,center]) for a,b in zip(xyz,np.roll(xyz,-1,axis=0))]

def jac(tri):
    return np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))

def points(tri,t,u):
    return (1-u[:,None])*((1-t[:,None])*tri[0]+t[:,None]*tri[1])+u[:,None]*tri[2]

def align(a,b):
    # Both triangles come from polygon fans: the first two vertices are the edge.
    if np.max(np.linalg.norm(a[:2]-b[:2],axis=1))<1e-10:return b
    if np.max(np.linalg.norm(a[:2]-b[[1,0]],axis=1))<1e-10:return b[[1,0,2]]
    return None

def joint_samples(a,b,order):
    """Partition u,v,|t-s| scaled to [0,1] into three max-coordinate
    sectors; r=z^2 resolves the remaining edge-root behavior. The edge
    coordinate t is split at s=t. All weights include physical Jacobians.
    """
    z,w=gauss(order)
    R,A,B=np.meshgrid(z,z,z,indexing='ij')
    r=R.ravel()**2;alpha=A.ravel();beta=B.ravel()
    wt=(w[:,None,None]*w[None,:,None]*w[None,None,:]).ravel()
    wt=wt*2*R.ravel()*r*r*jac(a)*jac(b)
    for t,tw in zip(z,w):
        T=np.full(len(r),t)
        for side in (0,1):
            span=t if side==0 else 1-t
            for u,v,h in ((r,r*alpha,r*beta),(r*alpha,r,r*beta),(r*alpha,r*beta,r)):
                s=t-span*h if side==0 else t+span*h
                yield points(a,T,u),points(b,s,v),wt*tw*span*(1-u)*(1-v)

def tensor_samples(tri,order,graded=True):
    z,w=gauss(order);u=z*z if graded else z
    du=2*z if graded else np.ones_like(z)
    T,U=np.meshgrid(z,u,indexing='ij')
    W=(w[:,None]*w[None,:]*du[None,:]).ravel()
    return points(tri,T.ravel(),U.ravel()),W*jac(tri)*(1-U.ravel())

def paired_derivative(x,y,normal,k):
    d=x-y;r=np.linalg.norm(d,axis=1)
    if min(r)<=0:raise ValueError('coincident quadrature nodes')
    return np.exp(-1j*k*r)/(4*np.pi*r)*(-1j*k-1/r)*(d@normal)/r

def shared_pair(a,b,screen_field,panel_field,normal,ks,order):
    ks=np.asarray(ks,float);result=None
    for x,y,w in joint_samples(a,b,order):
        S=screen_field(x);T=panel_field(y)
        if result is None:result=np.zeros((len(ks),S.shape[1],T.shape[1]),complex)
        for i,k in enumerate(ks):
            result[i]+=S.T@((w*paired_derivative(x,y,normal,k))[:,None]*T)
    return result

def regular_pair(a,b,screen_field,panel_field,normal,ks,order,graded=True):
    x,w=tensor_samples(a,order,graded);y,v=tensor_samples(b,order,graded)
    S=w[:,None]*screen_field(x);T=v[:,None]*panel_field(y)
    return np.array([S.T@(normal_derivative(x,np.broadcast_to(normal,x.shape),y,k)@T) for k in ks])

def assemble(basis,origin,axes,normal,panels,ks,order,use_joint=True):
    screen_field=lambda x:basis.evaluate((x-origin)@axes)[0]
    A=fan(basis.poly,origin,axes)
    out=[];pairs=0;blocks=[]
    for panel in panels:
        P=fan(panel.poly,panel.origin,panel.axes)
        panel_field=lambda y:panel.basis(panel.local(y))
        B=None;shared=0
        for a in A:
            for b in P:
                match=align(a,b)
                if match is not None:
                    pairs+=1;shared+=1
                if match is not None and use_joint:
                    v=shared_pair(a,match,screen_field,panel_field,normal,ks,order)
                else:
                    v=regular_pair(a,b,screen_field,panel_field,normal,ks,order)
                B=v if B is None else B+v
        out.append(B);blocks.append(shared)
    return np.concatenate(out,axis=2),dict(sharedPairs=pairs,perPanel=blocks,order=order,joint=use_joint)
