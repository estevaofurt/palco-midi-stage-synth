"""Three-dimensional aperture flux and reciprocal free-space monopole reference.
Not the exterior Neumann problem: no finite solid scattering or lid reflection.
Convention exp(i omega t), free-space Green function exp(-ikr)/(4 pi r).
"""
import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.spatial.distance import cdist
from board_contour import hull
from ribbed_plate import quadrature
from aperture_modes import FluxBasis
from extended_flux_basis import ExtendedFluxBasis
from split_radiation import relative

class Panel:
    def __init__(self,xyz,normal,count):
        self.origin=xyz[0].copy()
        u=xyz[np.argmax(np.linalg.norm(xyz-self.origin,axis=1))]-self.origin
        u/=np.linalg.norm(u);v=np.cross(normal,u);v/=np.linalg.norm(v)
        self.axes=np.stack([u,v],axis=1)
        self.poly=hull(self.local(xyz));self.basis=(ExtendedFluxBasis(self.poly,count) if count in (28,36) else FluxBasis(self.poly,count))
    def local(self,x):return (x-self.origin)@self.axes
    def world(self,x):return self.origin+x@self.axes.T
    def samples(self,order):
        x,w=quadrature(self.poly,order)
        return x,self.world(x),w,self.basis(x)

def ports(model,C0,report,count,canonical=False):
    panels=[];cols=[]
    z,w=leggauss(5);z=(z+1)/2;w=w/2
    u,v=np.meshgrid(z,z,indexing='ij');u=u.ravel();v=v.ravel()
    lam=np.c_[1-u,u*(1-v),u*v];weight=(w[:,None]*w[None,:]).ravel()*u
    for i,(ids,normal,area) in enumerate(zip(model['apertureFaces'],report['portNormalsXYZ'],report['portAreasM2'])):
        panel=Panel(model['aperturePolygons'][i] if canonical else model['xyz'][np.unique(ids)],np.asarray(normal),count)
        assert abs(panel.basis.area-area)<1e-10
        C=np.zeros((len(model['xyz']),count))
        for face in ids:
            t=model['xyz'][face];jac=np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))
            S=panel.basis(panel.local(lam@t))
            C[face]+=lam.T@((jac*weight)[:,None]*S)
        np.testing.assert_allclose(C.sum(0),np.r_[1.,np.zeros(count-1)],atol=1e-10)
        np.testing.assert_allclose(C[:,0],C0[:,i],atol=1e-10)
        panels.append(panel);cols.append(C)
    assert len(panels)==report['ports']
    return panels,np.column_stack(cols)

def self_react(panel,samples,k,order):
    xy,_,w,S=samples
    z,wt=leggauss(order);z=(z+1)/2;wt=wt/2
    u,v=np.meshgrid(z,z,indexing='ij');u=u.ravel();v=v.ravel()
    W=(wt[:,None]*wt[None,:]).ravel()
    raw=np.zeros((len(k),S.shape[1],S.shape[1]))
    for x,weight,shape in zip(xy,w,S):
        q=np.zeros((len(k),S.shape[1]))
        for a,b in zip(panel.poly,np.roll(panel.poly,-1,axis=0)):
            A=a-x;B=b-x;det=A[0]*B[1]-A[1]*B[0];assert det>0
            d=(1-v[:,None])*A+v[:,None]*B;L=np.linalg.norm(d,axis=1)
            y=x+u[:,None]*d
            q+=(np.cos(k[:,None]*u*L)*(W*det/L)[None,:])@panel.basis(y)
        raw+=weight*shape[None,:,None]*q[:,None,:]
    return raw

def angular(x,A,k,order):
    mu,w=leggauss(order);phi=2*np.pi*np.arange(4*order)/(4*order)
    s=np.sqrt(1-mu**2)
    d=np.stack([s[:,None]*np.cos(phi),s[:,None]*np.sin(phi),np.broadcast_to(mu[:,None],(order,len(phi)))],axis=-1).reshape(-1,3)
    w=np.repeat(w*2*np.pi/len(phi),len(phi));G=np.zeros((A.shape[1],A.shape[1]),complex)
    for i in range(0,len(d),128):
        F=np.exp(1j*k*(d[i:i+128]@x.T))@A
        G+=F.conj().T@(w[i:i+128,None]*F)
    return G.real/(4*np.pi)

def load(panels,freq,outer,inner,angular_order,rho=1.204,c=343.,*,pair_block=None):
    if pair_block is not None and (not isinstance(pair_block,int) or isinstance(pair_block,bool) or pair_block<1):
        raise ValueError('invalid pair block')
    f=np.asarray(freq,dtype=float);omega=2*np.pi*f;k=omega/c
    if min(f)<=0 or min(rho,c)<=0:raise ValueError('positive medium and frequencies')
    samples=[p.samples(outer) for p in panels];N=sum(p.basis.count for p in panels)
    offsets=np.r_[0,np.cumsum([p.basis.count for p in panels])]
    X=np.zeros((len(f),N,N));R=np.zeros_like(X)
    # Real part uses its smooth sinc limit, including coincident nodes.
    # Reactive self integrals use radial Duffy; mutual integrals use tensor
    # Gauss quadrature. Retain unsymmetrized self terms for independent audit.
    for i,(p,si) in enumerate(zip(panels,samples)):
        _,x,w,S=si;A=w[:,None]*S;I=slice(offsets[i],offsets[i+1])
        X[:,I,I]=self_react(p,si,k,inner)
        for j in range(i,len(panels)):
            _,y,v,T=samples[j];B=v[:,None]*T;J=slice(offsets[j],offsets[j+1])
            if pair_block is None:
                D=cdist(x,y)
                if i!=j:assert min(D.ravel())>0
                for l,kl in enumerate(k):
                    R[l,I,J]=A.T@(np.sinc(kl*D/np.pi)@B)
                    if i!=j:X[l,I,J]=A.T@((np.cos(kl*D)/D)@B)
            else:
                from exterior_pair_stream import pair_integrals
                rr,xx,_=pair_integrals(x,A,y,B,k,mutual=i!=j,block=pair_block)
                R[:,I,J]=rr
                if i!=j:X[:,I,J]=xx
            if i!=j:
                R[:,J,I]=R[:,I,J].transpose(0,2,1);X[:,J,I]=X[:,I,J].transpose(0,2,1)
    xyz=np.vstack([s[1] for s in samples]);A=np.zeros((len(xyz),N));start=0
    for i,(_,x,w,S) in enumerate(samples):
        A[start:start+len(x),offsets[i]:offsets[i+1]]=w[:,None]*S;start+=len(x)
    out=[]
    for l,kl in enumerate(k):
        # Independent spherical far-field Gram, not eigenvalue clipping.
        G=angular(xyz,A,kl,angular_order)
        r=rho*omega[l]*kl/(4*np.pi)*G
        x=rho*omega[l]/(4*np.pi)*(X[l]+X[l].T)/2
        Z=r+1j*x
        asym=relative(X[l],X[l].T);gram=relative(G,R[l])
        pas=float(min(np.linalg.eigvalsh(r))/max(np.linalg.norm(Z),1e-30))
        rep=dict(gramVsSurface=gram,reactiveAsymmetry=asym,passivityMinRelative=pas,reciprocity=relative(Z,Z.T))
        # The raw reactive asymmetry remains visible; no silent claim of raw convergence.
        rep['gate']=gram<=1e-8 and asym<=.001 and pas>=-1e-10 and rep['reciprocity']<=1e-8
        out.append((Z,rep))
    return out

def pressure(panels,U,points,f,order,rho=1.204,c=343.):
    """Free-space source pressure at independent exterior points only."""
    omega=2*np.pi*f;P=[];points=np.atleast_2d(points)
    for panel in panels:
        _,x,w,S=panel.samples(order);D=cdist(points,x)
        if min(D.ravel())<=1e-12:raise ValueError('observer on quadrature node')
        P.append((np.exp(-1j*omega*D/c)/D)@(w[:,None]*S))
    return 1j*rho*omega/(4*np.pi)*np.column_stack(P)@U
