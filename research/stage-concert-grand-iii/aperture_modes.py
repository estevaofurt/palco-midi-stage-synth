"""Nested finite-aperture flux modes with reciprocal pressure coupling.
Planar roof opening only; exterior is an infinite baffle, not a tilted lid.
"""
import numpy as np
from scipy.linalg import cholesky,solve_triangular,solve
from numpy.polynomial.legendre import leggauss
from board_contour import properties
from ribbed_plate import quadrature
from vented_cavity import clip_x
from closed_cavity import response as cavity
from split_radiation import split_load,relative

class FluxBasis:
    def __init__(self,poly,count):
        if count not in (1,3,6,10):raise ValueError('nested complete polynomial degrees 0 through 3')
        self.area,self.center,_=properties(poly);self.span=np.ptp(poly,axis=0);self.count=count
        xy,w=quadrature(poly,8);Q=self.raw(xy);G=Q.T@(w[:,None]*Q)/self.area
        L=cholesky((G+G.T)/2,lower=True)
        self.T=solve_triangular(L.T,np.eye(count),lower=False)
    def raw(self,xy):
        x,y=(2*(xy-self.center)/self.span).T
        return np.stack([np.ones(len(x)),x,y,x*x,x*y,y*y,x**3,x*x*y,x*y*y,y**3],axis=1)[:,:self.count]
    def __call__(self,xy,poly=None):return self.raw(xy)@self.T/self.area

def aperture_modes(model,poly,cut,count):
    ap=clip_x(np.asarray(poly),cut);basis=FluxBasis(ap,count);xy=model['xy'];tri=model['tri'];top=len(model['xyz'])-len(xy)
    C=np.zeros((len(model['xyz']),count));total=0.
    z,w=leggauss(5);z=(z+1)/2;w=w/2
    u,v=np.meshgrid(z,z,indexing='ij');u=u.ravel();v=v.ravel()
    lam=np.stack([1-u,u*(1-v),u*v],axis=1);weights=(w[:,None]*w[None,:]).ravel()*u
    for ids in tri:
        t=xy[ids];part=clip_x(t,cut)
        if len(part)<3:continue
        J=(t[1:]-t[0]).T
        for j in range(1,len(part)-1):
            p=np.array([part[0],part[j],part[j+1]])
            jac=abs(np.linalg.det((p[1:]-p[0]).T))
            if jac==0:continue
            q=lam@p;v=np.linalg.solve(J,(q-t[0]).T).T;N=np.c_[1-v.sum(1),v]
            C[top+ids]+=N.T@((jac*weights)[:,None]*basis(q));total+=jac/2
    assert abs(total-basis.area)<1e-10
    np.testing.assert_allclose(C.sum(0),np.r_[1.,np.zeros(count-1)],atol=1e-10)
    return ap,basis,C

def response(model,C,s,points,Zext):
    m=C.shape[1];n=model['B'].shape[1]
    assert Zext.shape==(m,m)
    Rext=(Zext+Zext.conj().T)/2;norm=max(np.linalg.norm(Zext),1e-30)
    if min(np.linalg.eigvalsh(Rext)) < -1e-10*norm:raise ValueError('active exterior')
    if relative(Zext,Zext.T)>1e-8:raise ValueError('nonreciprocal exterior')
    q=dict(model,B=np.column_stack([model['B'],C]))
    Z,P,report=cavity(q,s,points)
    U=solve(Z[n:,n:]+Zext,Z[n:,:n]);Q=np.vstack([np.eye(n),-U])
    Ze=Z[:n]@Q;Pe=P@Q;pc=Z[n:]@Q
    R=(Ze+Ze.conj().T)/2;H=(Z+Z.conj().T)/2
    air=U.conj().T@Rext@U;expected=Q.conj().T@H@Q+air
    den=max(np.linalg.norm(Ze),1e-30)
    metrics=dict(cavity=report,reciprocity=relative(Ze,Ze.T),
       powerRelative=float(np.linalg.norm(R-expected)/den),
       pressureContinuity=relative(pc,Zext@U),
       passivityMinRelative=float(min(np.linalg.eigvalsh(R))/den),
       exteriorPowerTrace=float(np.trace(air).real/2))
    metrics['gate']=report['gate'] and metrics['reciprocity']<=1e-8 and metrics['powerRelative']<=1e-8 and metrics['pressureContinuity']<=1e-8 and metrics['passivityMinRelative']>=-1e-8
    return Ze,Pe,U,metrics

def exterior(ap,basis,freq,outer,inner,angle,rho,c):
    # Observer here is only a required dummy coordinate for the common split routine;
    # the actual cavity microphones are evaluated by cavity.response, not this map.
    p=[[basis.center[0],basis.center[1],.2]]
    return [(z,report) for z,_,report in split_load(ap,basis,freq,p,outer,inner,angle,rho,c)]
