"""Separated vertical Neumann modes for a rigid closed prismatic cavity.
Independent planar P1 FEM, exact cosine height functions. No open lid claims.
High vertical modes may use an explicitly audited static inertance tail.
"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu
from closed_cavity import mesh
from board_contour import properties

def build(poly,n,height,field,c=343.,rho=1.204,*,field_order=4,boundary_n=None):
    if not isinstance(field_order,int) or field_order<2:raise ValueError('invalid trace quadrature order')
    xy,tri,_,_=mesh(poly,n,1,height,boundary_n=boundary_n);N=len(xy)
    t=xy[tri];J=np.transpose(t[:,1:]-t[:,:1],(0,2,1))
    A=abs(np.linalg.det(J))/2;inv=np.linalg.inv(J)
    grad=np.einsum('ij,tjk->tik',np.vstack([-np.ones(2),np.eye(2)]),inv)
    K=A[:,None,None]*(grad@np.transpose(grad,(0,2,1)))
    M=A[:,None,None]*(np.ones((3,3))+np.eye(3))/12
    i=np.repeat(tri,3,axis=1).ravel();j=np.tile(tri,(1,3)).ravel()
    K=coo_matrix((K.ravel(),(i,j)),shape=(N,N)).tocsc()
    M=coo_matrix((M.ravel(),(i,j)),shape=(N,N)).tocsc()
    z,w=np.polynomial.legendre.leggauss(field_order);z=(z+1)/2;w=w/2
    u,v=np.meshgrid(z,z,indexing='ij');u=u.ravel();v=v.ravel()
    lam=np.c_[1-u,u*(1-v),u*v];weight=(w[:,None]*w[None,:]).ravel()*u
    B=np.zeros((N,field(xy[:1]).shape[1]))
    for ids,a,tt in zip(tri,A,t):B[ids]+=lam.T@((2*a*weight)[:,None]*field(lam@tt))
    assert abs(A.sum()-properties(poly)[0])<1e-10
    assert np.linalg.norm(K@np.ones(N))<1e-9
    return dict(xy=xy,tri=tri,M=M,K=K,B=B,height=height,c=c,rho=rho,area=float(A.sum()))

def observer(m,points):
    points=np.asarray(points,float);xy=m['xy'];tri=m['tri'];t=xy[tri]
    J=np.transpose(t[:,1:]-t[:,:1],(0,2,1));inv=np.linalg.inv(J)
    O=np.zeros((len(points),len(xy)))
    if np.any(points[:,2]<-1e-10) or np.any(points[:,2]>m['height']+1e-10):
        raise ValueError('observer outside prism')
    for i,p in enumerate(points):
        v=np.einsum('tij,tj->ti',inv,p[:2]-t[:,0]);lam=np.c_[1-v.sum(1),v]
        ids=np.flatnonzero(lam.min(1)>=-1e-10)
        if not len(ids):raise ValueError('observer outside prism')
        j=ids[0];O[i,tri[j]]=lam[j]
    return O

def tail_sum(height,z,cut):
    """Sum (2/h) cos(m*pi*z/h)/(m*pi/h)^2 over m>cut."""
    z=np.asarray(z,float);theta=np.pi*z/height
    m=np.arange(1,cut+1,dtype=float)
    total=np.pi**2/6-np.pi*theta/2+theta**2/4
    partial=np.sum(np.cos(theta[...,None]*m)/m**2,axis=-1)
    return 2*height/np.pi**2*(total-partial)

def response(m,s,points,cut,tail=True):
    if s.real<0 or abs(s)==0 or cut<0:raise ValueError('invalid Laplace sample or cutoff')
    h,c,rho=m['height'],m['c'],m['rho'];K,M,B=m['K'],m['M'],m['B']
    O=observer(m,points);z=np.asarray(points)[:,2]
    Z=np.zeros((B.shape[1],B.shape[1]),complex);P=np.zeros((len(z),B.shape[1]),complex)
    energy=np.zeros_like(Z);res=0.
    for j in range(cut+1):
        mu=(j*np.pi/h)**2;v0=1/np.sqrt(h) if j==0 else np.sqrt(2/h)
        A=K+(mu+s*s/c**2)*M
        X=splu(A.astype(complex)).solve(B.astype(complex))
        Z+=v0*v0*(B.T@X)
        P+=v0*v0*np.cos(j*np.pi*z/h)[:,None]*(O@X)
        energy+=v0*v0*(X.conj().T@((K+mu*M)@X)+abs(s/c)**2*X.conj().T@(M@X))
        res=max(res,float(np.linalg.norm(A@X-B)/max(np.linalg.norm(B),1e-30)))
    tailZ=np.zeros_like(Z)
    if tail:
        Y=splu(M).solve(B);t0=float(tail_sum(h,0.,cut))
        tailZ=t0*(B.T@Y);Z+=tailZ
        P+=tail_sum(h,z,cut)[:,None]*(O@Y)
        # Static high-mode approximation is a positive inertance for z=0.
        energy+=tailZ
    Z*=rho*s;P*=rho*s
    H=(Z+Z.conj().T)/2;den=max(np.linalg.norm(Z),1e-30)
    rec=float(np.linalg.norm(Z-Z.T)/den)
    power=float(np.linalg.norm(H-rho*s.real*energy)/den)
    pas=float(min(np.linalg.eigvalsh(H))/den)
    rep=dict(reciprocity=rec,powerRelative=power,passivityMinRelative=pas,residual=res,
        tailRelative=float(np.linalg.norm(rho*s*tailZ)/den),verticalCutoff=cut,tail=tail)
    rep['gate']=rec<=1e-8 and power<=1e-8 and pas>=-1e-8 and res<=1e-8
    return Z,P,rep
