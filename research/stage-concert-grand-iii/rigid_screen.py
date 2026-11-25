"""Galerkin hypersingular equation for a planar zero-thickness rigid screen.
Pressure jump in a continuous edge-vanishing basis. Outgoing exp(i omega t).
W = integral G (grad u.grad v - k^2 u v); d_n D = -W.
This isolated screen is not yet an aperture/cabinet coupling.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss,Legendre
from scipy.linalg import cholesky,solve_triangular
from ribbed_plate import quadrature
from board_contour import properties
from rigid_scattering import green,normal_derivative
from split_radiation import relative

class ScreenBasis:
    def __init__(self,poly,degree):
        self.poly=np.asarray(poly,float);self.degree=degree
        _,c,_=properties(self.poly)
        e=np.roll(self.poly,-1,axis=0)-self.poly
        n=np.c_[-e[:,1],e[:,0]]
        self.normals=n/np.sum(n*(c-self.poly),axis=1)[:,None]
        self.center=c;self.scale=2/np.ptp(self.poly,axis=0)
        self.indices=np.array([(i,d-i) for d in range(degree+1) for i in range(d+1)])
        q,w=quadrature(self.poly,max(10,degree+5))
        V,_,_=self.raw(q);L=cholesky(V.T@(w[:,None]*V),lower=True)
        self.T=solve_triangular(L.T,np.eye(len(L)),lower=False)
    def raw(self,q):
        q=np.atleast_2d(q);f=np.ones(len(q));gx=np.zeros(len(q));gy=gx.copy()
        for n,a in zip(self.normals,self.poly):
            z=(q-a)@n;gx,gy=gx*z+f*n[0],gy*z+f*n[1];f=f*z
        t=(q-self.center)*self.scale
        val=[];der=[]
        for j in (0,1):
            val.append(np.stack([Legendre.basis(i)(t[:,j]) for i in range(self.degree+1)],axis=1))
            der.append(np.stack([Legendre.basis(i).deriv()(t[:,j])*self.scale[j] for i in range(self.degree+1)],axis=1))
        i,j=self.indices.T
        g=val[0][:,i]*val[1][:,j]
        return f[:,None]*g,gx[:,None]*g+f[:,None]*der[0][:,i]*val[1][:,j],gy[:,None]*g+f[:,None]*val[0][:,i]*der[1][:,j]
    def evaluate(self,q):
        return tuple(x@self.T for x in self.raw(q))

def operator(basis,k,outer,inner):
    x,w=quadrature(basis.poly,outer);V,X,Y=basis.evaluate(x)
    z,t=leggauss(inner);z=(z+1)/2;t=t/2
    u,v=np.meshgrid(z,z,indexing='ij');u=u.ravel();v=v.ravel()
    wt=(t[:,None]*t[None,:]).ravel()
    N=V.shape[1];W=np.zeros((N,N),complex)
    for pt,weight,a,b,c in zip(x,w,V,X,Y):
        iv=np.zeros(N,complex);ix=iv.copy();iy=iv.copy()
        for p,q in zip(basis.poly,np.roll(basis.poly,-1,axis=0)):
            A=p-pt;B=q-pt;det=A[0]*B[1]-A[1]*B[0];assert det>0
            d=(1-v[:,None])*A+v[:,None]*B;L=np.linalg.norm(d,axis=1)
            G=wt*det*np.exp(-1j*k*u*L)/(4*np.pi*L)
            S,Sx,Sy=basis.evaluate(pt+u[:,None]*d)
            iv+=G@S;ix+=G@Sx;iy+=G@Sy
        W+=weight*(np.outer(b,ix)+np.outer(c,iy)-k*k*np.outer(a,iv))
    return W

def geometry(poly,angle,height):
    a=np.deg2rad(angle);h=poly[:,0].min()
    origin=np.array([h,0.,height]);axes=np.array([[np.cos(a),0.],[0.,1.],[np.sin(a),0.]])
    normal=np.cross(axes[:,0],axes[:,1])
    local=np.asarray(poly)-[h,0.]
    return local,origin,axes,normal

def coupling(basis,origin,axes,normal,points,k,order):
    x,w=basis.samples(order) if hasattr(basis,'samples') else quadrature(basis.poly,order);xyz=origin+x@axes.T
    S=basis.evaluate(x)[0]
    D=normal_derivative(xyz,np.broadcast_to(normal,xyz.shape),points,k)
    return S.T@(w[:,None]*D)

def far_gram(basis,origin,axes,normal,sources,coeff,k,order=28):
    xy,w=basis.samples(order) if hasattr(basis,'samples') else quadrature(basis.poly,order);xyz=origin+xy@axes.T;A=w[:,None]*basis.evaluate(xy)[0]
    mu,t=leggauss(order);phi=2*np.pi*np.arange(4*order)/(4*order);s=np.sqrt(1-mu*mu)
    dirs=np.stack([s[:,None]*np.cos(phi),s[:,None]*np.sin(phi),np.broadcast_to(mu[:,None],(order,len(phi)))],axis=-1).reshape(-1,3)
    weights=np.repeat(t*2*np.pi/len(phi),len(phi));R=np.zeros((len(sources),len(sources)),complex)
    for i in range(0,len(dirs),128):
        d=dirs[i:i+128]
        F=np.exp(1j*k*(d@sources.T))+1j*k*(d@normal)[:,None]*(np.exp(1j*k*(d@xyz.T))@A@coeff)
        R+=F.conj().T@(weights[i:i+128,None]*F)
    return R/(4*np.pi)

def solve_screen(poly,origin,axes,normal,sources,observers,k,degree,outer,inner,rho=1.204,c=343.):
    basis=ScreenBasis(poly,degree+1)
    W=operator(basis,k,outer,inner)
    B=coupling(basis,origin,axes,normal,sources,k,max(outer,16))
    J=coupling(basis,origin,axes,normal,observers,k,max(outer,16))
    N=(degree+1)*(degree+2)//2
    # Solve in nested subspace; test residual in next polynomial degree.
    A=W[:N,:N];q=np.linalg.solve(A,B[:N])
    near=J[:N].T@q;Gsc=B[:N].T@q
    D=np.linalg.norm(sources[:,None,:]-sources[None,:,:],axis=-1)
    G=np.zeros(D.shape,complex);idx=D>0
    G[idx]=np.exp(-1j*k*D[idx])/(4*np.pi*D[idx]);G[np.diag_indices(len(D))]=-1j*k/(4*np.pi)
    Z=1j*rho*c*k*(G+Gsc)
    R=(Z+Z.conj().T)/2
    coeff=np.pad(q,((0,len(W)-N),(0,0)))
    expected=rho*c*k*k/(4*np.pi)*far_gram(basis,origin,axes,normal,sources,coeff,k)
    rep=dict(modes=N,condition=float(np.linalg.cond(A)),rawReciprocity=relative(A,A.T),
        weakResidual=relative(W@coeff,B),reciprocity=relative(Z,Z.T),powerRelative=relative(R,expected),
        passivityMinRelative=float(min(np.linalg.eigvalsh(R))/max(np.linalg.norm(R),1e-30)))
    rep['gate']=rep['rawReciprocity']<=.001 and rep['weakResidual']<=.05 and rep['reciprocity']<=.001 and rep['powerRelative']<=.01 and rep['passivityMinRelative']>=-1e-8
    return near,Z,rep
