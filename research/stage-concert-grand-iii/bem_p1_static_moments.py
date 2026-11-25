"""Analytic Laplace first moments on flat triangles, P1 basis.
Use surface integration by parts: integral (y-x_projected)/r dA
equals the sum of outward conormals times integral r ds.
Differentiate the edge integrals analytically in target coordinates.
Only the regular Helmholtz remainder uses numerical quadrature.
"""
import numpy as np
from exterior_bem import elements,samples
from bem_static_split import laplace
from bem_linear import shape,rule,projected_shapes,observe,far_gram
from bem_oversampled import audit_targets
from bem_weak_p1_refined import quadrature
from scipy.linalg import solve
from split_radiation import relative

def gradients(t):
    a=t[:,1]-t[:,0];b=t[:,2]-t[:,0]
    aa=np.sum(a*a,axis=1);bb=np.sum(b*b,axis=1);ab=np.sum(a*b,axis=1);det=aa*bb-ab*ab
    g1=2*(bb[:,None]*a-ab[:,None]*b)/det[:,None]
    g2=2*(aa[:,None]*b-ab[:,None]*a)/det[:,None]
    return np.stack([-g1-g2,g1,g2],axis=1)

def static(t,x,owner=None):
    t=np.asarray(t,float);x=np.atleast_2d(x)
    S,g=laplace(t,x,owner);S0=projected_shapes(t,x);H=gradients(t)
    _,n,_=elements(t)
    v=t[None,:,:,:]-x[:,None,None,:];r=np.linalg.norm(v,axis=-1)
    # A coefficient C=edge conormal dot tangential shape gradient.
    G=S[:,:,None]*S0
    dG=g[:,:,None,:]*S0[:,:,:,None]+S[:,:,None,None]*H[None,:,:,:]
    for j in range(3):
        e=t[:,(j+1)%3]-t[:,j];L=np.linalg.norm(e,axis=1);e=e/L[:,None]
        out=np.cross(e,n);C=np.einsum('tad,td->ta',H,out)/(4*np.pi)
        a=v[:,:,j,:];s0=np.einsum('btd,td->bt',a,e);s1=s0+L[None,:]
        perp=a-s0[:,:,None]*e[None,:,:];d2=np.sum(perp*perp,axis=-1)
        r0=r[:,:,j];r1=r[:,:,(j+1)%3]
        ratio=L[None,:]/(r0+r1)
        if np.any(ratio>=1):raise ValueError('unresolved edge distance')
        I=2*np.arctanh(ratio)
        J=.5*(s1*r1-s0*r0+d2*I)
        dJ=-e[None,:,:]*(r1-r0)[:,:,None]-perp*I[:,:,None]
        G+=J[:,:,None]*C[None,:,:]
        dG+=dJ[:,:,None,:]*C[None,:,:,None]
    return G,dG

def source_quadrature(t,order):
    y,w=samples(t,order);u,v,_=rule(order);Sy=shape(np.c_[1-u,u*(1-v),u*v])
    return y,w,Sy

def operators(t,x,n,owner,k,order,derivative_only=False):
    return _operators(t,x,n,owner,k,source_quadrature(t,order),derivative_only)

def _operators(t,x,n,owner,k,source,derivative_only=False):
    t=np.asarray(t);x=np.asarray(x);n=np.asarray(n);owner=np.asarray(owner,int)
    y,w,Sy=source
    N=len(t);D=np.empty((len(x),3*N),complex);G=None if derivative_only else np.empty_like(D)
    for start in range(0,len(x),8):
        stop=min(start+8,len(x));xx=x[start:stop];nn=n[start:stop];ii=owner[start:stop]
        idx=np.arange(len(xx));S,grad=static(t,xx,ii)
        d=xx[:,None,None,:]-y[None,:,:,:];rad=np.linalg.norm(d,axis=-1);kr=k*rad;E=np.expm1(-1j*kr)
        factor=-E-1j*kr*(1+E);small=abs(kr)<1e-3;z=kr[small]
        factor[small]=-z*z/2+1j*z**3/3+z**4/8
        f=np.zeros(rad.shape,complex);np.divide(factor,rad**2,out=f,where=rad>0)
        dot=np.einsum('btqd,bd->btq',d,nn);cos=np.zeros_like(rad);np.divide(dot,rad,out=cos,where=rad>0)
        K=np.einsum('btad,bd->bta',grad,nn)+np.einsum('btq,qa->bta',w[None,:,:]*f*cos/(4*np.pi),Sy)
        K[idx,ii]=-.5*projected_shapes(t,xx)[idx,ii]
        D[start:stop]=K.reshape(len(xx),-1)
        if not derivative_only:
            rem=np.full(rad.shape,-1j*k,complex);np.divide(E,rad,out=rem,where=rad>0)
            V=S+np.einsum('btq,qa->bta',w[None,:,:]*rem/(4*np.pi),Sy)
            G[start:stop]=V.reshape(len(xx),-1)
    return G,D

def fit(t,k,outer,inner,velocity):
    x,w,L=quadrature(t,outer);_,n,a=elements(t);N=len(t);owner=np.arange(N)
    D=np.zeros((N,3,3*N),complex);B=None
    for j in range(len(L)):
        _,K=operators(t,x[:,j],n,owner,k,inner,True);V=velocity(x[:,j],owner)
        W=w[:,j,None]*L[j][None,:]
        if B is None:B=np.zeros((N,3,V.shape[1]))
        D+=W[:,:,None]*K[:,None,:];B+=W[:,:,None]*V[:,None,:]
    D=D.reshape(3*N,3*N);B=B.reshape(3*N,-1);sc=np.repeat(np.sqrt(a),3)
    q=solve(D/sc[:,None]/sc[None,:],-B/sc[:,None],assume_a='gen')/sc[:,None]
    return q,dict(weakResidual=relative(D@q,-B),unknowns=len(q))

def audit(t,q,V,k,points,order,rho=1.204,c=343.):
    x,n,w,o=audit_targets(t);P=np.empty((len(x),q.shape[1]),complex);U=np.empty_like(P)
    for i in range(0,len(x),24):
        sl=slice(i,min(i+24,len(x)));G,D=operators(t,x[sl],n[sl],o[sl],k,order)
        P[sl]=G@q;U[sl]=-D@q
    R=np.sqrt(w)[:,None]*(U-V);T=np.sqrt(w)[:,None]*V
    Z=1j*rho*c*k*V.T@(w[:,None]*P);P=1j*rho*c*k*observe(t,q,points,k,order)
    H=(Z+Z.conj().T)/2;F=rho*c*k*k/(4*np.pi)*far_gram(t,q,k,surface_order=order)
    rep=dict(heldoutResidual=float(np.linalg.norm(R)/max(np.linalg.norm(T),1e-30)),
        heldoutWorstColumn=float(max(np.linalg.norm(R,axis=0)/np.maximum(np.linalg.norm(T,axis=0),1e-30))),
        reciprocity=relative(Z,Z.T),powerRelative=relative(H,F),
        passivityMinRelative=float(np.linalg.eigvalsh(H).min()/max(np.linalg.norm(Z),1e-30)))
    rep['gate']=max(rep['heldoutResidual'],rep['heldoutWorstColumn'])<=.05 and rep['reciprocity']<=.01 and rep['powerRelative']<=.01 and rep['passivityMinRelative']>=-1e-8
    return Z,P,rep
