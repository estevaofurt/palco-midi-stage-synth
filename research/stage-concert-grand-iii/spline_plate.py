"""Local C2 cubic tensor splines on a clipped polygon, with exact essential w=0.
Alternative Ritz space; same plate/rib physical model as G3.05b.
"""
import numpy as np
from scipy.interpolate import BSpline
from scipy.linalg import eigh
from numpy.polynomial.legendre import leggauss
from board_contour import properties
from ribbed_plate import gram,quadrature

def clip(poly,axis,bound,sign):
    out=[]
    if len(poly)==0:return np.empty((0,2))
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        u=sign*(a[axis]-bound);v=sign*(b[axis]-bound)
        if u>=0:out.append(a)
        if (u>=0)!=(v>=0):out.append(a+(b-a)*u/(u-v))
    if len(out)<3:return np.empty((0,2))
    # Remove duplicates at coincident clipping boundaries.
    out=np.array(out);keep=np.linalg.norm(out-np.roll(out,1,axis=0),axis=1)>1e-13
    return out[keep]

class LocalBasis:
    def __init__(self,poly,cells,essential=True):
        self.poly=np.asarray(poly);self.cells=cells;self.essential=essential
        _,c,_=properties(self.poly)
        a=self.poly;e=np.roll(a,-1,axis=0)-a;n=np.stack([-e[:,1],e[:,0]],axis=1)
        self.n=n/np.sum(n*(c-a),axis=1)[:,None];self.a=a
        self.low=self.poly.min(0);self.high=self.poly.max(0)
        self.grids=[np.linspace(l,h,cells+1) for l,h in zip(self.low,self.high)]
        self.naxis=cells+3;self.size=self.naxis**2;self.spl=[]
        for g in self.grids:
            knots=np.r_[[g[0]]*4,g[1:-1],[g[-1]]*4]
            s=BSpline(knots,np.eye(self.naxis),3,extrapolate=False)
            self.spl.append([s,s.derivative(1),s.derivative(2)])
    def evaluate(self,points,ids=None,gradients=False):
        p=np.clip(np.atleast_2d(points),self.low,self.high)
        f=np.ones(len(p));x=np.zeros(len(p));y=x.copy();xx=x.copy();xy=x.copy();yy=x.copy()
        if self.essential:
            for n,a in zip(self.n,self.a):
                z=(p-a)@n;nx,ny=n
                xx,xy,yy=xx*z+2*x*nx,xy*z+x*ny+y*nx,yy*z+2*y*ny
                x,y=x*z+f*nx,y*z+f*ny;f=f*z
        if ids is None:ids=np.arange(self.size)
        i,j=np.divmod(ids,self.naxis)
        X=[[s(p[:,0])[:,i] for s in self.spl[0]]][0]
        Y=[[s(p[:,1])[:,j] for s in self.spl[1]]][0]
        g=X[0]*Y[0];gx=X[1]*Y[0];gy=X[0]*Y[1]
        gxx=X[2]*Y[0];gxy=X[1]*Y[1];gyy=X[0]*Y[2]
        F=f[:,None];A=x[:,None];B=y[:,None]
        result=(F*g,xx[:,None]*g+2*A*gx+F*gxx,xy[:,None]*g+A*gy+B*gx+F*gxy,yy[:,None]*g+2*B*gy+F*gyy)
        if gradients:return result+(A*g+F*gx,B*g+F*gy)
        return result
    def patches(self,order):
        for i in range(self.cells):
            for j in range(self.cells):
                p=self.poly.copy()
                for axis,k in ((0,i),(1,j)):
                    p=clip(p,axis,self.grids[axis][k],1)
                    p=clip(p,axis,self.grids[axis][k+1],-1)
                    if len(p)<3:break
                if len(p)<3:continue
                area,_,_=properties(p)
                if area<1e-14:continue
                xy,w=quadrature(p,order)
                ids=np.array([a*self.naxis+b for a in range(i,i+4) for b in range(j,j+4)])
                yield xy,w,ids
    def line(self,a,b,order):
        # Subdivide at every knot crossing, exact polynomial quadrature per piece.
        d=b-a;L=float(np.linalg.norm(d));assert L>0
        cuts=[0.,1.]
        for axis,g in enumerate(self.grids):
            if abs(d[axis])>1e-14:cuts.extend(t for t in (g-a[axis])/d[axis] if 1e-12<t<1-1e-12)
        z,w=leggauss(order);t=(z+1)/2;w=w/2
        cuts=sorted(set(cuts))
        for l,h in zip(cuts,cuts[1:]):
            if h-l>1e-12:yield a+(l+(h-l)*t[:,None])*d,w*(h-l)*L

def assemble(poly,ribs,plate,rib,cells,order,essential=True):
    basis=LocalBasis(poly,cells,essential);n=basis.size
    M=np.zeros((n,n));K=np.zeros_like(M);Mr=np.zeros_like(M);Kr=np.zeros_like(M)
    h=plate['thicknessM'];rho=plate['densityKgM3'];ex=plate['ExPa'];ey=plate['EyPa'];g=plate['GxyPa'];nu=plate['nuXY']
    d=h**3/(12*(1-nu*nu*ey/ex));dx=d*ex;dy=d*ey;dxy=d*nu*ey;ds=g*h**3/12
    area=0.
    for xy,w,ids in basis.patches(order):
        S,X,C,Y=basis.evaluate(xy,ids);a=np.ix_(ids,ids);area+=float(sum(w))
        M[a]+=gram(S,rho*h*w)
        K[a]+=dx*gram(X,w)+dy*gram(Y,w)+dxy*(gram(X,w,Y)+gram(Y,w,X))+4*ds*gram(C,w)
    A=rib['widthM']*rib['heightM'];I=rib['widthM']*rib['heightM']**3/12;rm=0.
    for q in ribs:
        a=np.array(q['startXYZ_m'][:2]);b=np.array(q['endXYZ_m'][:2]);L=float(np.linalg.norm(b-a));u=(b-a)/L
        rm+=L*rib['densityKgM3']*A
        for xy,w in basis.line(a,b,order):
            R,X,C,Y=basis.evaluate(xy)
            curv=u[0]**2*X+2*u[0]*u[1]*C+u[1]**2*Y
            Mr+=gram(R,w*rib['densityKgM3']*A);Kr+=gram(curv,w*rib['youngAlongPa']*I)
    # Remove basis functions with no interior support, never silently drop nonzero rank.
    active=np.flatnonzero(np.diag(M)>0);scale=1/np.sqrt(np.diag(M)[active])
    m=M[np.ix_(active,active)]*scale[:,None]*scale[None,:]
    d,U=eigh((m+m.T)/2);assert min(d)>0
    keep=d>d[-1]*1e-11
    T=np.zeros((n,int(sum(keep))));T[active,:]=scale[:,None]*U[:,keep]/np.sqrt(d[keep])
    def project(A):
        B=T.T@A@T;return (B+B.T)/2
    MM,KK,RR,SS=map(project,(M,K,Mr,Kr))
    assert np.linalg.norm(MM-np.eye(len(MM)),2)<1e-5
    return dict(basis=basis,T=T,M=MM,K=KK,Mr=RR,Kr=SS,rank=int(sum(keep)),fullRank=len(active),
      condition=float(d[-1]/d[0]),areaM2=area,plateMassKg=area*rho*h,ribMassKg=rm)

def rim_matrices(model,kz,kt,order):
    """Elastic line restraint to an immovable datum; no physical rim mass yet."""
    if min(kz,kt)<0:raise ValueError('passive stiffness required')
    b=model['basis'];T=model['T'];n=T.shape[1];Z=np.zeros((n,n));R=np.zeros_like(Z)
    for a,c in zip(b.poly,np.roll(b.poly,-1,axis=0)):
        d=c-a;normal=np.array([-d[1],d[0]])/np.linalg.norm(d)
        for xy,w in b.line(a,c,order):
            S,_,_,_,X,Y=b.evaluate(xy,gradients=True)
            Z+=kz*gram(S@T,w);R+=kt*gram((normal[0]*X+normal[1]*Y)@T,w)
    return (Z+Z.T)/2,(R+R.T)/2
