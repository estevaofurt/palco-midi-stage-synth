"""Polygonal Kirchhoff-Love Ritz plate, with separately assembled bonded rib terms.
Boundary w=0 on polygon edges, slope unconstrained. Not the measured piano.
"""
import numpy as np
from scipy.linalg import eigh
from numpy.polynomial.legendre import leggauss,Legendre
from board_contour import properties

def quadrature(poly,order):
    _,c,_=properties(poly);z,w=leggauss(order);t=(z+1)/2;w=w/2
    u,v=np.meshgrid(t,t,indexing='ij');W=(w[:,None]*w[None,:]*u).ravel()
    pts=[];weights=[]
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        A=a-c;B=b-c;det=abs(A[0]*B[1]-A[1]*B[0])
        pts.append(c+u.ravel()[:,None]*((1-v.ravel()[:,None])*A+v.ravel()[:,None]*B))
        weights.append(W*det)
    return np.vstack(pts),np.concatenate(weights)

class Basis:
    def __init__(self,poly,degree):
        self.poly=np.asarray(poly);self.degree=degree
        _,c,_=properties(self.poly)
        a=self.poly;b=np.roll(a,-1,axis=0);e=b-a
        n=np.stack([-e[:,1],e[:,0]],axis=1)
        den=np.sum(n*(c-a),axis=1);assert min(den)>0
        self.n=n/den[:,None];self.a=a
        self.center=(self.poly.max(0)+self.poly.min(0))/2
        self.scale=2/(self.poly.max(0)-self.poly.min(0))
        self.indices=[(i,j) for i in range(degree+1) for j in range(degree+1-i)]
    def evaluate(self,xy):
        xy=np.atleast_2d(xy);count=len(xy)
        # Product of normalized affine distances: exactly zero on each edge.
        f=np.ones(count);x=np.zeros(count);y=x.copy();xx=x.copy();xy2=x.copy();yy=x.copy()
        for n,a in zip(self.n,self.a):
            z=(xy-a)@n;nx,ny=n
            xx,xy2,yy=xx*z+2*x*nx,xy2*z+x*ny+y*nx,yy*z+2*y*ny
            x,y=x*z+f*nx,y*z+f*ny;f=f*z
        p=(xy-self.center)*self.scale
        values=[]
        for axis in (0,1):
            values.append([np.stack([Legendre.basis(i).deriv(k)(p[:,axis])*self.scale[axis]**k for i in range(self.degree+1)],axis=1) for k in range(3)])
        X,Y=values;i,j=np.array(self.indices).T
        g=X[0][:,i]*Y[0][:,j];gx=X[1][:,i]*Y[0][:,j];gy=X[0][:,i]*Y[1][:,j]
        gxx=X[2][:,i]*Y[0][:,j];gxy=X[1][:,i]*Y[1][:,j];gyy=X[0][:,i]*Y[2][:,j]
        return (f[:,None]*g,xx[:,None]*g+2*x[:,None]*gx+f[:,None]*gxx,
                xy2[:,None]*g+x[:,None]*gy+y[:,None]*gx+f[:,None]*gxy,
                yy[:,None]*g+2*y[:,None]*gy+f[:,None]*gyy)
def gram(A,w,B=None):return A.T@(w[:,None]*(A if B is None else B))
def assemble(poly,ribs,plate,rib,degree,order):
    basis=Basis(poly,degree);xy,w=quadrature(poly,order)
    S,X,C,Y=basis.evaluate(xy)
    h=plate['thicknessM'];rho=plate['densityKgM3'];ex=plate['ExPa'];ey=plate['EyPa'];g=plate['GxyPa'];nu=plate['nuXY']
    assert min(h,rho,ex,ey,g)>0 and 1-nu*nu*ey/ex>0
    d=h**3/(12*(1-nu*nu*ey/ex));dx=d*ex;dy=d*ey;dxy=d*nu*ey;ds=g*h**3/12
    # Mass-orthogonalize sampled basis with SVD, report rank explicitly.
    _,sv,Vt=np.linalg.svd(np.sqrt(rho*h*w)[:,None]*S,full_matrices=False)
    keep=sv>sv[0]*1e-11;T=Vt[keep].T/sv[keep]
    S,X,C,Y=[a@T for a in (S,X,C,Y)]
    M=gram(S,rho*h*w);K=dx*gram(X,w)+dy*gram(Y,w)+dxy*(gram(X,w,Y)+gram(Y,w,X))+4*ds*gram(C,w)
    Mr=np.zeros_like(M);Kr=np.zeros_like(K);totalMass=0.
    z,wi=leggauss(order);t=(z+1)/2;wi=wi/2
    A=rib['widthM']*rib['heightM'];I=rib['widthM']*rib['heightM']**3/12
    assert min(A,I,rib['densityKgM3'],rib['youngAlongPa'])>0
    for q in ribs:
        a=np.array(q['startXYZ_m'][:2]);b=np.array(q['endXYZ_m'][:2]);L=float(np.linalg.norm(b-a));u=(b-a)/L
        R,Rxx,Rxy,Ryy=[v@T for v in basis.evaluate(a+t[:,None]*(b-a))]
        curvature=u[0]**2*Rxx+2*u[0]*u[1]*Rxy+u[1]**2*Ryy
        Mr+=gram(R,wi*L*rib['densityKgM3']*A);Kr+=gram(curvature,wi*L*rib['youngAlongPa']*I)
        totalMass+=L*rib['densityKgM3']*A
    for A in (M,K,Mr,Kr):A[:]=(A+A.T)/2
    for A in (Mr,Kr):assert min(np.linalg.eigvalsh(A))>=-1e-8*max(1.,np.linalg.norm(A,2))
    assert np.linalg.norm(M-np.eye(len(M)),2)<1e-5
    return dict(basis=basis,T=T,M=M,K=K,Mr=Mr,Kr=Kr,rank=int(sum(keep)),fullRank=len(sv),
       condition=float(sv[0]/sv[-1]),ribMassKg=totalMass,plateMassKg=float(sum(w)*rho*h),areaM2=float(sum(w)))
def response(model,points,freq,plate,withRibs):
    M=model['M']+(model['Mr'] if withRibs else 0)
    K=model['K']+(model['Kr'] if withRibs else 0)
    w2,U=eigh(K,M);assert min(w2)>0
    P=(model['basis'].evaluate(points)[0]@model['T']).T
    Q=U.T@P;alpha=plate['alphaPerS'];beta=plate['betaS'];Y=[]
    for f in freq:
        w=2*np.pi*f;Z=(Q.T*(1j*w/(w2-w*w+1j*w*(alpha+beta*w2))))@Q
        assert np.linalg.norm(Z-Z.T)<=1e-10*max(np.linalg.norm(Z),1e-30)
        H=(Z+Z.conj().T)/2;assert min(np.linalg.eigvalsh(H))>=-1e-10*max(np.linalg.norm(H),1e-30)
        Y.append(Z)
    return np.sqrt(w2)/(2*np.pi),np.array(Y)
