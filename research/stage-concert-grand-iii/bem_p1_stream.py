"""Memory-conscious P1 operator application; same discrete equations.
Derivative-only assembly skips the pressure matrix and singular pressure
self integral. Surface audit streams blocks instead of storing full traces.
Experimental until compared numerically with the existing solver.
"""
import numpy as np
from scipy.linalg import solve
from exterior_bem import samples
from bem_linear import COL,targets,shape,rule,projected_shapes,operators,observe,far_gram
from bem_static_split import laplace
from bem_oversampled import audit_targets
from split_radiation import relative

def derivative(t,x,n,owner,k,order):
    t=np.asarray(t);x=np.asarray(x);owner=np.asarray(owner,int)
    y,w=samples(t,order);u,v,_=rule(order);Sy=shape(np.c_[1-u,u*(1-v),u*v])
    N=len(t);D=np.empty((len(x),3*N),complex)
    for start in range(0,len(x),8):
        stop=min(start+8,len(x));xx=x[start:stop];nn=n[start:stop];ii=owner[start:stop]
        idx=np.arange(len(xx));S0=projected_shapes(t,xx)
        _,grad=laplace(t,xx,ii)
        d=xx[:,None,None,:]-y[None,:,:,:];rad=np.linalg.norm(d,axis=-1);rad[idx,ii,:]=1.
        if np.any(rad<=0):raise ValueError('coincident nonself nodes')
        E=np.expm1(-1j*k*rad);g=1/(4*np.pi*rad)
        dot=np.einsum('btqd,bd->btq',d,nn);dg=-g*dot/rad**2
        delta=Sy[None,None,:,:]-S0[:,:,None,:]
        regD=g*(-E-1j*k*rad*(1+E))*dot/rad**2
        PV=np.einsum('btd,bd->bt',grad,nn)
        K=PV[:,:,None]*S0+np.einsum('btq,btqd->btd',dg*w[None,:,:],delta)+np.einsum('btq,qd->btd',regD*w[None,:,:],Sy)
        K[idx,ii]=-.5*S0[idx,ii]
        D[start:stop]=K.reshape(len(xx),-1)
    return D

def fit(t,V,k,order):
    x,n,w,owner=targets(t,COL);D=derivative(t,x,n,owner,k,order)
    q=solve(D,-V,assume_a='gen')
    return q,dict(collocationResidual=relative(D@q,-V),coefficientNorm=float(np.linalg.norm(q)))

def trace(t,q,x,n,owner,k,order,batch=24):
    if batch<1:raise ValueError('batch must be positive')
    P=np.empty((len(x),q.shape[1]),complex);U=np.empty_like(P)
    for start in range(0,len(x),batch):
        sl=slice(start,min(start+batch,len(x)))
        G,D=operators(t,x[sl],n[sl],owner[sl],k,order)
        P[sl]=G@q;U[sl]=-D@q
    return P,U

def audit(t,q,V,k,points,order,rho=1.204,c=343.,batch=24):
    x,n,w,owner=audit_targets(t);p,u=trace(t,q,x,n,owner,k,order,batch)
    R=np.sqrt(w)[:,None]*(V-u);T=np.sqrt(w)[:,None]*V
    Z=1j*rho*c*k*(V.T@(w[:,None]*p));P=1j*rho*c*k*observe(t,q,points,k,order)
    H=(Z+Z.conj().T)/2;expected=rho*c*k*k/(4*np.pi)*far_gram(t,q,k,surface_order=order)
    den=max(np.linalg.norm(Z),1e-30)
    rep=dict(heldoutResidual=float(np.linalg.norm(R)/max(np.linalg.norm(T),1e-30)),
        heldoutWorstColumn=float(max(np.linalg.norm(R,axis=0)/np.maximum(np.linalg.norm(T,axis=0),1e-30))),
        reciprocity=relative(Z,Z.T),powerRelative=relative(H,expected),
        passivityMinRelative=float(min(np.linalg.eigvalsh(H))/den))
    rep['gate']=max(rep['heldoutResidual'],rep['heldoutWorstColumn'])<=.05 and rep['reciprocity']<=.01 and rep['powerRelative']<=.01 and rep['passivityMinRelative']>=-1e-8
    # Storage of full trace matrices only, not process peak RSS.
    rep['denseTraceMatrixBytes']=int(2*len(x)*len(q)*np.dtype(complex).itemsize)
    rep['streamTraceMatrixBytes']=int(2*min(batch,len(x))*len(q)*np.dtype(complex).itemsize)
    return Z,P,rep
