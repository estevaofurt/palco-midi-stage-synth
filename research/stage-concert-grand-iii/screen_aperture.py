"""Experimental finite-screen correction of the free-space aperture reference.
Not the complete exterior Neumann problem: rim, board and lower radiation absent.
No projection of the corrected impedance onto passive or symmetric matrices.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss
from rigid_scattering import normal_derivative
from lid_exterior import pressure
from split_radiation import relative

def sample_panels(panels,order):
    parts=[p.samples(order) for p in panels]
    n=sum(p.basis.count for p in panels)
    xyz=np.concatenate([v[1] for v in parts]);A=np.zeros((len(xyz),n))
    start=col=0
    for _,x,w,S in parts:
        A[start:start+len(x),col:col+S.shape[1]]=w[:,None]*S
        start+=len(x);col+=S.shape[1]
    return xyz,A

def screen_samples(basis,origin,axes,order):
    xy,w=basis.samples(order);xyz=origin+xy@axes.T
    return xyz,w[:,None]*basis.evaluate(xy)[0]

def interaction(x,S,y,T,normal,k):
    """Projection of incident normal derivative onto screen jump basis."""
    B=np.zeros((S.shape[1],T.shape[1]),complex)
    for i in range(0,len(x),64):
        q=x[i:i+64]
        D=normal_derivative(q,np.broadcast_to(normal,q.shape),y,k)
        B+=S[i:i+64].T@(D@T)
    return B

def gram(x,S,y,T,normal,Q,k,order):
    mu,w=leggauss(order);phi=2*np.pi*np.arange(4*order)/(4*order)
    s=np.sqrt(1-mu**2)
    d=np.stack([s[:,None]*np.cos(phi),s[:,None]*np.sin(phi),np.broadcast_to(mu[:,None],(order,len(phi)))],axis=-1).reshape(-1,3)
    w=np.repeat(w*2*np.pi/len(phi),len(phi))
    R=np.zeros((T.shape[1],T.shape[1]),complex)
    for i in range(0,len(d),64):
        u=d[i:i+64]
        F=np.exp(1j*k*(u@y.T))@T+1j*k*(u@normal)[:,None]*(np.exp(1j*k*(u@x.T))@S@Q)
        R+=F.conj().T@(w[i:i+64,None]*F)
    return R/(4*np.pi)

def correction(basis,W,origin,axes,normal,panels,Z0,f,degree,screen_order,panel_order,angular_order=24,rho=1.204,c=343.,interaction_block=None,subspace=None):
    k=2*np.pi*f/c
    x,S=screen_samples(basis,origin,axes,screen_order);y,T=sample_panels(panels,panel_order)
    B=interaction(x,S,y,T,normal,k) if interaction_block is None else np.asarray(interaction_block)
    if B.shape!=(S.shape[1],T.shape[1]) or not np.isfinite(B).all():raise ValueError('invalid interaction block')
    N=(degree+1)*(degree+2)//2;Ntest=(degree+2)*(degree+3)//2
    if subspace is not None:N,Ntest=subspace
    if not 0<N<Ntest<=len(W) or W.shape!=(S.shape[1],S.shape[1]):raise ValueError('independent test space required')
    q=np.linalg.solve(W[:N,:N],B[:N]);Q=np.pad(q,((0,len(W)-N),(0,0)))
    delta=1j*rho*c*k*(B[:N].T@q);Z=Z0+delta;R=(Z+Z.conj().T)/2
    expected=rho*c*k*k/(4*np.pi)*gram(x,S,y,T,normal,Q,k,angular_order)
    rep=dict(rawScreenReciprocity=relative(W[:N,:N],W[:N,:N].T),
        weakResidual=relative(W[:Ntest,:N]@q,B[:Ntest]),
        reciprocity=relative(Z,Z.T),powerRelative=relative(R,expected),
        passivityMinRelative=float(min(np.linalg.eigvalsh(R))/max(np.linalg.norm(Z),1e-30)),
        correctionRelative=float(np.linalg.norm(delta)/max(np.linalg.norm(Z0),1e-30)))
    rep['gate']=rep['rawScreenReciprocity']<=.001 and rep['weakResidual']<=.05 and rep['reciprocity']<=.001 and rep['powerRelative']<=.01 and rep['passivityMinRelative']>=-1e-8
    return Z,Q,rep

def observe(basis,Q,origin,axes,normal,panels,U,points,f,order,rho=1.204,c=343.):
    x,S=screen_samples(basis,origin,axes,order)
    k=2*np.pi*f/c
    D=normal_derivative(x,np.broadcast_to(normal,x.shape),np.asarray(points),k)
    return pressure(panels,U,points,f,order,rho,c)+1j*rho*c*k*(D.T@S@Q@U)
