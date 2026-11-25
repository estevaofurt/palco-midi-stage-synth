"""Edge-enriched Galerkin screen: sqrt(product of normalized edge distances).
Graded quadrature toward each straight edge, no empirical material parameters.
Corner singular exponents are not independently resolved.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss,legvander
from scipy.linalg import cholesky,solve_triangular
from board_contour import properties
from rigid_screen import coupling,far_gram
from split_radiation import relative

def rule(order):
    z,w=leggauss(order);z=(z+1)/2;w=w/2
    # Fan radial endpoint u=1 is on the polygon edge.
    u=1-(1-z)**2;du=2*(1-z)
    U,V=np.meshgrid(u,z,indexing='ij')
    return U.ravel(),V.ravel(),(w[:,None]*du[:,None]*w[None,:]).ravel()

def graded(poly,order):
    _,c,_=properties(poly);u,v,w=rule(order);P=[];W=[]
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        A=a-c;B=b-c;det=A[0]*B[1]-A[1]*B[0];assert det>0
        P.append(c+u[:,None]*((1-v[:,None])*A+v[:,None]*B))
        W.append(w*u*det)
    return np.vstack(P),np.concatenate(W)

class EdgeBasis:
    def __init__(self,poly,degree):
        self.poly=np.asarray(poly,float);self.degree=degree
        _,c,_=properties(self.poly);e=np.roll(self.poly,-1,axis=0)-self.poly
        n=np.c_[-e[:,1],e[:,0]]
        self.normals=n/np.sum(n*(c-self.poly),axis=1)[:,None]
        self.center=c;self.scale=2/np.ptp(self.poly,axis=0)
        self.indices=np.array([(i,d-i) for d in range(degree+1) for i in range(d+1)])
        q,w=self.samples(max(12,degree+6))
        V,_,_=self.raw(q);G=V.T@(w[:,None]*V)
        L=cholesky((G+G.T)/2,lower=True)
        self.T=solve_triangular(L.T,np.eye(len(L)),lower=False)
    def samples(self,order):
        return graded(self.poly,order)
    def raw(self,q):
        q=np.atleast_2d(q)
        f=np.ones(len(q));fx=np.zeros(len(q));fy=fx.copy()
        for n,a in zip(self.normals,self.poly):
            z=(q-a)@n
            if np.any(z<=0):raise ValueError('edge gradient requires strictly interior nodes')
            fx,fy=fx*z+f*n[0],fy*z+f*n[1];f=f*z
        root=np.sqrt(f);fx=fx/(2*root);fy=fy/(2*root)
        t=(q-self.center)*self.scale;vals=[];ders=[]
        for j in (0,1):
            P=legvander(t[:,j],self.degree);D=np.zeros_like(P)
            if self.degree>=1:D[:,1]=1.
            for k in range(2,self.degree+1):
                D[:,k]=D[:,k-2]+(2*k-1)*P[:,k-1]
            vals.append(P);ders.append(D*self.scale[j])
        i,j=self.indices.T
        g=vals[0][:,i]*vals[1][:,j]
        return root[:,None]*g,fx[:,None]*g+root[:,None]*ders[0][:,i]*vals[1][:,j],fy[:,None]*g+root[:,None]*vals[0][:,i]*ders[1][:,j]
    def evaluate(self,q):
        return tuple(x@self.T for x in self.raw(q))

def operators(basis,k,outer,inner):
    """Independent unsymmetrized bilinear operators, reuse geometry across k."""
    k=np.atleast_1d(k);x,w=basis.samples(outer);V,X,Y=basis.evaluate(x)
    u,v,wt=rule(inner);N=V.shape[1];W=np.zeros((len(k),N,N),complex)
    for pt,weight,a,b,c in zip(x,w,V,X,Y):
        iv=np.zeros((len(k),N),complex);ix=iv.copy();iy=iv.copy()
        for p,q in zip(basis.poly,np.roll(basis.poly,-1,axis=0)):
            A=p-pt;B=q-pt;det=A[0]*B[1]-A[1]*B[0];assert det>0
            d=(1-v[:,None])*A+v[:,None]*B;L=np.linalg.norm(d,axis=1)
            G=np.exp(-1j*k[:,None]*(u*L)[None,:])*(wt*det/(4*np.pi*L))[None,:]
            S,Sx,Sy=basis.evaluate(pt+u[:,None]*d)
            iv+=G@S;ix+=G@Sx;iy+=G@Sy
        W+=weight*(b[None,:,None]*ix[:,None,:]+c[None,:,None]*iy[:,None,:]-k[:,None,None]**2*a[None,:,None]*iv[:,None,:])
    return W

def solve(basis,W,k,origin,axes,normal,sources,observers,degree,order,rho=1.204,c=343.):
    B=coupling(basis,origin,axes,normal,sources,k,order)
    J=coupling(basis,origin,axes,normal,observers,k,order)
    N=(degree+1)*(degree+2)//2;Ntest=(degree+2)*(degree+3)//2
    if Ntest>len(W):raise ValueError('one additional degree required')
    A=W[:N,:N];q=np.linalg.solve(A,B[:N])
    near=J[:N].T@q;Gsc=B[:N].T@q
    D=np.linalg.norm(sources[:,None,:]-sources[None,:,:],axis=-1)
    G=np.zeros(D.shape,complex);idx=D>0
    G[idx]=np.exp(-1j*k*D[idx])/(4*np.pi*D[idx])
    G[np.diag_indices(len(D))]=-1j*k/(4*np.pi)
    Z=1j*rho*c*k*(G+Gsc);R=(Z+Z.conj().T)/2
    coeff=np.pad(q,((0,len(W)-N),(0,0)))
    expected=rho*c*k*k/(4*np.pi)*far_gram(basis,origin,axes,normal,sources,coeff,k,order=max(order,28))
    rep=dict(modes=N,condition=float(np.linalg.cond(A)),rawReciprocity=relative(A,A.T),
        weakResidual=relative(W[:Ntest,:N]@q,B[:Ntest]),reciprocity=relative(Z,Z.T),
        powerRelative=relative(R,expected),passivityMinRelative=float(min(np.linalg.eigvalsh(R))/max(np.linalg.norm(R),1e-30)))
    rep['gate']=rep['rawReciprocity']<=.001 and rep['weakResidual']<=.05 and rep['reciprocity']<=.001 and rep['powerRelative']<=.01 and rep['passivityMinRelative']>=-1e-8
    return near,Z,rep
