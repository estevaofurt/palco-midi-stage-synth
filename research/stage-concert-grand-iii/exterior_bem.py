"""Experimental P0 collocation BEM for exterior prescribed normal velocity.
Single layer, exterior derivative trace (-I/2+K'), exp(i omega t).
No internal equivalent sources, no damping or post-hoc symmetrization.
Not a combined-field formulation; interior resonances are a limitation.
"""
import numpy as np
from scipy.linalg import solve
from numpy.polynomial.legendre import leggauss
from split_radiation import relative

def elements(t):
    t=np.asarray(t,float)
    d=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);area=np.linalg.norm(d,axis=1)/2
    if np.any(area<=0):raise ValueError('degenerate surface triangle')
    return t.mean(1),d/(2*area[:,None]),area

def subdivide(t,project=None):
    a,b,c=t.transpose(1,0,2);ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2
    if project is not None:ab,bc,ca=[project(x) for x in (ab,bc,ca)]
    return np.stack([np.stack([a,ab,ca],axis=1),np.stack([ab,b,bc],axis=1),
        np.stack([ca,bc,c],axis=1),np.stack([ab,bc,ca],axis=1)],axis=1).reshape(-1,3,3)

def gauss(order):
    z,w=leggauss(order);return (z+1)/2,w/2

def samples(t,order):
    z,w=gauss(order);u,v=np.meshgrid(z,z,indexing='ij');u=u.ravel();v=v.ravel()
    L=np.c_[1-u,u*(1-v),u*v];_,_,area=elements(t)
    return np.einsum('qa,tad->tqd',L,t),2*area[:,None]*(u*(w[:,None]*w[None,:]).ravel())[None,:]

def topology(t):
    # Coordinates are shared by midpoint refinement; round only topology keys.
    _,ids=np.unique(np.round(t.reshape(-1,3),12),axis=0,return_inverse=True)
    ids=ids.reshape(-1,3);e=ids[:,[0,1,1,2,2,0]].reshape(-1,2)
    key=np.sort(e,axis=1);_,inv,count=np.unique(key,axis=0,return_inverse=True,return_counts=True)
    balance=np.bincount(inv,weights=np.where(e[:,0]<e[:,1],1.,-1.))
    volume=float(np.sum(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])))/6)
    return dict(closed=bool(np.all(count==2)),oriented=bool(np.all(balance==0)),volume=volume,
        gate=bool(np.all(count==2) and np.all(balance==0) and volume>0))

def self_potential(x,t,k,order):
    """Exact radial cancellation of the weak 1/r singularity.
    x is strictly inside its flat source element.
    """
    z,w=gauss(order);u,v=np.meshgrid(z,z,indexing='ij');u=u.ravel();v=v.ravel()
    weight=(w[:,None]*w[None,:]).ravel();result=np.zeros(len(x),complex)
    for j in range(3):
        a=t[:,j]-x;b=t[:,(j+1)%3]-x
        d=(1-v[None,:,None])*a[:,None,:]+v[None,:,None]*b[:,None,:]
        L=np.linalg.norm(d,axis=2);jac=np.linalg.norm(np.cross(a,b),axis=1)
        result+=np.sum(np.exp(-1j*k*u[None,:]*L)*weight[None,:]*jac[:,None]/(4*np.pi*L),axis=1)
    return result

def operators(t,x,n,owner,k,order,derivative=True):
    """Boundary traces for arbitrary strictly interior target points.
    owner gives the source triangle containing each target. Other triangles
    use ordinary positive Gauss-Duffy quadrature; convergence must be audited.
    """
    t=np.asarray(t);x=np.asarray(x);n=np.asarray(n);owner=np.asarray(owner,int)
    y,w=samples(t,order);N=len(t);G=np.empty((len(x),N),complex)
    D=np.empty_like(G) if derivative else None
    for start in range(0,len(x),16):
        stop=min(start+16,len(x));xx=x[start:stop];nn=n[start:stop];ii=owner[start:stop]
        dx=xx[:,None,None,:]-y[None,:,:,:];rad=np.linalg.norm(dx,axis=-1)
        j=np.arange(len(xx));rad[j,ii,:]=1.
        if np.any(rad<=0):raise ValueError('coincident nonself quadrature points')
        g=np.exp(-1j*k*rad)/(4*np.pi*rad)
        v=np.sum(g*w[None,:,:],axis=-1)
        v[j,ii]=self_potential(xx,t[ii],k,max(order,12))
        G[start:stop]=v
        if derivative:
            dot=np.einsum('btqd,bd->btq',dx,nn)
            val=np.sum(g*(-1j*k-1/rad)*dot/rad*w[None,:,:],axis=-1)
            # K' vanishes on a flat self element; exterior jump is -1/2.
            val[j,ii]=-.5
            D[start:stop]=val
    return G,D

def fit(t,V,k,order):
    x,n,area=elements(t)
    _,D=operators(t,x,n,np.arange(len(t)),k,order)
    q=solve(D,-V,assume_a='gen')
    return q,dict(collocationResidual=relative(D@q,-V),coefficientNorm=float(np.linalg.norm(q)))

def field(t,q,points,k,order):
    y,w=samples(t,order);out=[]
    for pt in np.asarray(points):
        d=np.linalg.norm(pt-y,axis=-1)
        if min(d.ravel())<=0:raise ValueError('observer on quadrature node')
        out.append(np.sum(np.exp(-1j*k*d)/(4*np.pi*d)*w,axis=1)@q)
    return np.array(out)

def far_gram(t,q,k,order=24,surface_order=5):
    y,w=samples(t,surface_order);y=y.reshape(-1,3)
    coeff=(w[:,:,None]*q[:,None,:]).reshape(len(y),q.shape[1])
    mu,wt=leggauss(order);phi=2*np.pi*np.arange(4*order)/(4*order);s=np.sqrt(1-mu**2)
    dirs=np.stack([s[:,None]*np.cos(phi),s[:,None]*np.sin(phi),np.broadcast_to(mu[:,None],(order,len(phi)))],axis=-1).reshape(-1,3)
    wt=np.repeat(wt*2*np.pi/len(phi),len(phi))
    R=np.zeros((q.shape[1],q.shape[1]),complex)
    for i in range(0,len(dirs),24):
        F=np.exp(1j*k*(dirs[i:i+24]@y.T))@coeff
        R+=F.conj().T@(wt[i:i+24,None]*F)
    return R/(4*np.pi)

def heldout(t):
    # Three positive degree-2 triangle points, not collocation centroids.
    L=np.array([[2/3,1/6,1/6],[1/6,2/3,1/6],[1/6,1/6,2/3]])
    _,n,area=elements(t);x=np.einsum('qa,tad->tqd',L,t).reshape(-1,3)
    return x,np.repeat(n,3,axis=0),np.repeat(area/3,3),np.repeat(np.arange(len(t)),3)

def audit(t,q,V,k,points,order,rho=1.204,c=343.):
    x,n,w,owner=heldout(t)
    G,D=operators(t,x,n,owner,k,order)
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
