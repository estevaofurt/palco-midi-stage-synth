"""Analytic Laplace triangle integration plus regular Helmholtz remainder.
Constant density on a flat triangle. No post-hoc reciprocity projection.
"""
import numpy as np
from scipy.linalg import solve
from exterior_bem import elements,samples,heldout,field,far_gram
from split_radiation import relative

def laplace(t,x,owner=None):
    """Integrals of 1/(4*pi*r) and its target gradient.
    Self gradient is the principal value, not the exterior jump.
    """
    t=np.asarray(t,float);x=np.atleast_2d(x)
    _,n,area=elements(t);v=t[None,:,:,:]-x[:,None,None,:]
    r=np.linalg.norm(v,axis=-1)
    if np.any(r<=0):raise ValueError('target at triangle vertex')
    h=-np.einsum('btd,td->bt',v[:,:,0,:],n)
    a,b,c=v.transpose(2,0,1,3)
    ra,rb,rc=r.transpose(2,0,1)
    den=ra*rb*rc+np.sum(a*b,axis=-1)*rc+np.sum(b*c,axis=-1)*ra+np.sum(c*a,axis=-1)*rb
    omega=2*np.arctan2(2*area[None,:]*h,den)
    # Coplanar target: principal-value normal derivative is zero.
    scale=np.max(np.linalg.norm(t-np.roll(t,-1,axis=1),axis=-1),axis=1)
    omega=np.where(abs(h)<=32*np.finfo(float).eps*scale[None,:],0.,omega)
    if owner is not None:omega[np.arange(len(x)),owner]=0.
    S=-h*omega;grad=-omega[:,:,None]*n[None,:,:]
    for j in range(3):
        a0=t[:,j];b0=t[:,(j+1)%3];edge=b0-a0
        L=np.linalg.norm(edge,axis=1);out=np.cross(edge/L[:,None],n)
        ratio=L[None,:]/(r[:,:,j]+r[:,:,(j+1)%3])
        if np.any(ratio>=1):raise ValueError('target on edge or unresolved edge distance')
        I=2*np.arctanh(ratio)
        d=np.einsum('btd,td->bt',v[:,:,j,:],out)
        S+=d*I;grad-=I[:,:,None]*out[None,:,:]
    return S/(4*np.pi),grad/(4*np.pi)

def operators(t,x,n,owner,k,order):
    t=np.asarray(t);x=np.asarray(x);n=np.asarray(n);owner=np.asarray(owner,int)
    y,w=samples(t,order);G=np.empty((len(x),len(t)),complex);D=np.empty_like(G)
    for start in range(0,len(x),12):
        stop=min(start+12,len(x));xx=x[start:stop];nn=n[start:stop];ii=owner[start:stop]
        s,g=laplace(t,xx,ii)
        dx=xx[:,None,None,:]-y[None,:,:,:];rad=np.linalg.norm(dx,axis=-1);kr=k*rad
        E=np.expm1(-1j*kr)
        gp=np.full(rad.shape,-1j*k,dtype=complex)
        np.divide(E,rad,out=gp,where=rad>0)
        factor=-E-1j*kr*(1+E)
        small=abs(kr)<1e-3;v=kr[small]
        factor[small]=-v*v/2+1j*v**3/3+v**4/8
        # Divide by r² first; the remaining directional cosine is bounded.
        f=np.zeros(rad.shape,complex);np.divide(factor,rad**2,out=f,where=rad>0)
        dot=np.einsum('btqd,bd->btq',dx,nn)
        cosine=np.zeros(rad.shape);np.divide(dot,rad,out=cosine,where=rad>0)
        S=s+np.sum(w[None,:,:]*gp,axis=-1)/(4*np.pi)
        N=np.einsum('btd,bd->bt',g,nn)+np.sum(w[None,:,:]*f*cosine,axis=-1)/(4*np.pi)
        N[np.arange(len(xx)),ii]=-.5
        G[start:stop]=S;D[start:stop]=N
    return G,D

def fit(t,V,k,order):
    x,n,_=elements(t)
    _,D=operators(t,x,n,np.arange(len(t)),k,order)
    q=solve(D,-V,assume_a='gen')
    return q,dict(collocationResidual=relative(D@q,-V),coefficientNorm=float(np.linalg.norm(q)))

def audit(t,q,V,k,points,order,rho=1.204,c=343.):
    x,n,w,owner=heldout(t);G,D=operators(t,x,n,owner,k,order)
    residual=np.sqrt(w)[:,None]*(D@q+V);target=np.sqrt(w)[:,None]*V
    Z=1j*rho*c*k*(V.T@(w[:,None]*(G@q)))
    P=1j*rho*c*k*field(t,q,points,k,order)
    R=(Z+Z.conj().T)/2;expected=rho*c*k*k/(4*np.pi)*far_gram(t,q,k,surface_order=order)
    den=max(np.linalg.norm(Z),1e-30)
    rep=dict(heldoutResidual=float(np.linalg.norm(residual)/max(np.linalg.norm(target),1e-30)),
        heldoutWorstColumn=float(max(np.linalg.norm(residual,axis=0)/np.maximum(np.linalg.norm(target,axis=0),1e-30))),
        reciprocity=relative(Z,Z.T),powerRelative=relative(R,expected),
        passivityMinRelative=float(min(np.linalg.eigvalsh(R))/den))
    rep['gate']=max(rep['heldoutResidual'],rep['heldoutWorstColumn'])<=.05 and rep['reciprocity']<=.01 and rep['powerRelative']<=.01 and rep['passivityMinRelative']>=-1e-8
    return Z,P,rep
