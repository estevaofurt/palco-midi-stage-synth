"""Discontinuous linear (P1) density on planar triangles, interior collocation.
Use analytic static constant subtraction and direct Duffy self integration.
Experimental reference: no continuity imposed across physical edges.
"""
import numpy as np
from scipy.linalg import solve
from numpy.polynomial.legendre import leggauss
from exterior_bem import elements,samples,field
from bem_static_split import laplace
from split_radiation import relative

COL=np.array([[2/3,1/6,1/6],[1/6,2/3,1/6],[1/6,1/6,2/3]])
CHECK=np.array([[.6,.3,.1],[.1,.6,.3],[.3,.1,.6],[.6,.1,.3],[.3,.6,.1],[.1,.3,.6]])

def targets(t,L):
    _,n,a=elements(t)
    return np.einsum('qa,tad->tqd',L,t).reshape(-1,3),np.repeat(n,len(L),axis=0),np.repeat(a/len(L),len(L)),np.repeat(np.arange(len(t)),len(L))

def shape(L):return 2*np.asarray(L)-1/3

def projected_shapes(t,x):
    a=t[:,1]-t[:,0];b=t[:,2]-t[:,0];d=x[:,None,:]-t[None,:,0,:]
    aa=np.sum(a*a,axis=1);bb=np.sum(b*b,axis=1);ab=np.sum(a*b,axis=1)
    da=np.einsum('btd,td->bt',d,a);db=np.einsum('btd,td->bt',d,b);det=aa*bb-ab*ab
    u=(da*bb-db*ab)/det;v=(db*aa-da*ab)/det
    return shape(np.stack([1-u-v,u,v],axis=-1))

def rule(order):
    z,w=leggauss(order);z=(z+1)/2;w=w/2
    u,v=np.meshgrid(z,z,indexing='ij')
    return u.ravel(),v.ravel(),(w[:,None]*w[None,:]).ravel()

def self_integral(x,t,S0,k,order):
    u,v,w=rule(max(order,12));out=np.zeros((len(x),3),complex)
    for j in range(3):
        a=t[:,j]-x;b=t[:,(j+1)%3]-x
        d=(1-v[None,:,None])*a[:,None,:]+v[None,:,None]*b[:,None,:]
        L=np.linalg.norm(d,axis=-1);jac=np.linalg.norm(np.cross(a,b),axis=1)
        E=np.eye(3);edge=(1-v[:,None])*shape(E[j])+v[:,None]*shape(E[(j+1)%3])
        S=u[None,:,None]*(edge[None,:,:]-S0[:,None,:])
        kernel=np.exp(-1j*k*u[None,:]*L)*w[None,:]*jac[:,None]/(4*np.pi*L)
        out+=np.einsum('bq,bqd->bd',kernel,S)
    return out

def operators(t,x,n,owner,k,order):
    t=np.asarray(t);x=np.asarray(x);owner=np.asarray(owner,int)
    y,w=samples(t,order);u,v,_=rule(order);Sy=shape(np.c_[1-u,u*(1-v),u*v])
    N=len(t);G=np.empty((len(x),3*N),complex);D=np.empty_like(G)
    for start in range(0,len(x),8):
        stop=min(start+8,len(x));xx=x[start:stop];nn=n[start:stop];ii=owner[start:stop]
        idx=np.arange(len(xx));S0=projected_shapes(t,xx)
        L0,grad=laplace(t,xx,ii)
        d=xx[:,None,None,:]-y[None,:,:,:];rad=np.linalg.norm(d,axis=-1);rad[idx,ii,:]=1.
        if np.any(rad<=0):raise ValueError('coincident nonself nodes')
        E=np.expm1(-1j*k*rad);g=1/(4*np.pi*rad)
        dot=np.einsum('btqd,bd->btq',d,nn);dg=-g*dot/rad**2
        delta=Sy[None,None,:,:]-S0[:,:,None,:]
        reg=g*E;regD=g*(-E-1j*k*rad*(1+E))*dot/rad**2
        V=L0[:,:,None]*S0+np.einsum('btq,btqd->btd',g*w[None,:,:],delta)+np.einsum('btq,qd->btd',reg*w[None,:,:],Sy)
        PV=np.einsum('btd,bd->bt',grad,nn)
        K=PV[:,:,None]*S0+np.einsum('btq,btqd->btd',dg*w[None,:,:],delta)+np.einsum('btq,qd->btd',regD*w[None,:,:],Sy)
        # Preserve the exact P0 constant part. Integrate only the
        # vanishing linear density difference by independent radial Duffy.
        sr=np.linalg.norm(xx[:,None,:]-y[ii],axis=-1)
        rem=np.full(sr.shape,-1j*k,complex)
        np.divide(np.expm1(-1j*k*sr),sr,out=rem,where=sr>0)
        const=L0[idx,ii]+np.sum(w[ii]*rem,axis=1)/(4*np.pi)
        V[idx,ii]=const[:,None]*S0[idx,ii]+self_integral(xx,t[ii],S0[idx,ii],k,order)
        K[idx,ii]=-.5*S0[idx,ii]
        G[start:stop]=V.reshape(len(xx),-1);D[start:stop]=K.reshape(len(xx),-1)
    return G,D

def fit(t,V,k,order):
    x,n,w,owner=targets(t,COL);_,D=operators(t,x,n,owner,k,order)
    q=solve(D,-V,assume_a='gen')
    return q,dict(collocationResidual=relative(D@q,-V),coefficientNorm=float(np.linalg.norm(q)))

def source_samples(t,q,order):
    y,w=samples(t,order);u,v,_=rule(order);S=shape(np.c_[1-u,u*(1-v),u*v])
    Q=np.einsum('qa,tam->tqm',S,q.reshape(len(t),3,-1))
    return y.reshape(-1,3),(w[:,:,None]*Q).reshape(-1,q.shape[1])

def observe(t,q,points,k,order):
    y,Q=source_samples(t,q,order);out=[]
    for x in np.asarray(points):
        r=np.linalg.norm(x-y,axis=1);out.append((np.exp(-1j*k*r)/(4*np.pi*r))@Q)
    return np.asarray(out)

def far_gram(t,q,k,order=24,surface_order=5):
    y,Q=source_samples(t,q,surface_order);mu,w=leggauss(order);phi=2*np.pi*np.arange(4*order)/(4*order);s=np.sqrt(1-mu**2)
    dirs=np.stack([s[:,None]*np.cos(phi),s[:,None]*np.sin(phi),np.broadcast_to(mu[:,None],(order,len(phi)))],axis=-1).reshape(-1,3)
    wt=np.repeat(w*2*np.pi/len(phi),len(phi));R=np.zeros((q.shape[1],q.shape[1]),complex)
    for i in range(0,len(dirs),24):
        F=np.exp(1j*k*(dirs[i:i+24]@y.T))@Q;R+=F.conj().T@(wt[i:i+24,None]*F)
    return R/(4*np.pi)

def audit(t,q,V,k,points,order,rho=1.204,c=343.):
    x,n,w,owner=targets(t,CHECK);G,D=operators(t,x,n,owner,k,order)
    residual=np.sqrt(w)[:,None]*(D@q+V);target=np.sqrt(w)[:,None]*V
    Z=1j*rho*c*k*(V.T@(w[:,None]*(G@q)));P=1j*rho*c*k*observe(t,q,points,k,order)
    R=(Z+Z.conj().T)/2;expected=rho*c*k*k/(4*np.pi)*far_gram(t,q,k,surface_order=order)
    den=max(np.linalg.norm(Z),1e-30)
    rep=dict(heldoutResidual=float(np.linalg.norm(residual)/max(np.linalg.norm(target),1e-30)),
        heldoutWorstColumn=float(max(np.linalg.norm(residual,axis=0)/np.maximum(np.linalg.norm(target,axis=0),1e-30))),
        reciprocity=relative(Z,Z.T),powerRelative=relative(R,expected),
        passivityMinRelative=float(min(np.linalg.eigvalsh(R))/den))
    rep['gate']=max(rep['heldoutResidual'],rep['heldoutWorstColumn'])<=.05 and rep['reciprocity']<=.01 and rep['powerRelative']<=.01 and rep['passivityMinRelative']>=-1e-8
    return Z,P,rep
