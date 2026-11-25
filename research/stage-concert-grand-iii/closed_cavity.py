"""Closed rigid-wall upper cavity, conforming P1 tetrahedral potential FEM.
Positive board velocity is into the upper fluid. No damping or open-lid claims.
"""
import numpy as np
from scipy.spatial import Delaunay
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu
from board_contour import properties,margins

def mesh(poly,n,nz,height):
    poly=np.asarray(poly);lo=poly.min(0);hi=poly.max(0)
    assert n>=2 and nz>=1 and height>0
    x,y=np.meshgrid(*[np.linspace(a,b,n+1) for a,b in zip(lo,hi)])
    grid=np.stack([x.ravel(),y.ravel()],axis=1)
    h=max(hi-lo)/n
    # Avoid tiny cut triangles between interior grid points and perimeter nodes.
    grid=grid[margins(poly,grid)>.15*h]
    boundary=[]
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        steps=max(1,int(np.ceil(np.linalg.norm(b-a)/h)))
        boundary.extend(a+(b-a)*j/steps for j in range(steps))
    xy=np.vstack([boundary,grid]);tri=Delaunay(xy).simplices
    t=xy[tri];det=np.abs(np.linalg.det(t[:,1:]-t[:,:1]))
    # Qhull can emit nearly collinear triangles between boundary points. Only
    # discard roundoff-area triangles and require intact perimeter and volume.
    bad=det<=1e-12*h*h
    if np.any(bad):
        assert np.all(tri[bad]<len(boundary)), 'degenerate interior triangle'
        tri=tri[~bad];det=det[~bad]
    assert len(np.unique(tri))==len(xy)
    assert min(det)/h**2>=1e-4, 'poor planar element quality'
    edges=np.sort(np.vstack([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1)
    e,count=np.unique(edges,axis=0,return_counts=True)
    expected=np.sort(np.c_[np.arange(len(boundary)),np.roll(np.arange(len(boundary)),-1)],axis=1)
    assert np.all(count<=2) and set(map(tuple,e[count==1]))==set(map(tuple,expected)), 'boundary topology'
    assert abs(sum(det)/2-properties(poly)[0])<1e-10
    print('G3_CAVITY_MESH '+str(dict(n=n,nz=nz,discarded=int(sum(bad)),minimumPlanarAreaRatio=float(min(det)/h**2))),flush=True)
    N=len(xy);xyz=np.concatenate([np.c_[xy,np.full(N,z)] for z in np.linspace(0,height,nz+1)])
    tet=[]
    for k in range(nz):
        for t in tri:
            a,b,c=np.sort(t)+k*N
            tet.extend([[a,b,c,c+N],[a,b,b+N,c+N],[a,a+N,b+N,c+N]])
    return xy,tri,xyz,np.array(tet)

def assemble(poly,n,nz,height,field,c=343.,rho=1.204):
    xy,tri,xyz,tet=mesh(poly,n,nz,height);N=len(xyz);ii=[];jj=[];mm=[];kk=[];volume=0.
    for ids in tet:
        t=xyz[ids];J=(t[1:]-t[0]).T;V=abs(np.linalg.det(J))/6
        assert V>0
        grad=np.vstack([-np.ones(3),np.eye(3)])@np.linalg.inv(J)
        M=V/(20*c*c)*(np.ones((4,4))+np.eye(4));K=V*(grad@grad.T)
        ii.extend(np.repeat(ids,4));jj.extend(np.tile(ids,4));mm.extend(M.ravel());kk.extend(K.ravel());volume+=V
    M=coo_matrix((mm,(ii,jj)),shape=(N,N)).tocsc();K=coo_matrix((kk,(ii,jj)),shape=(N,N)).tocsc()
    # Exact degree-3 triangle quadrature via 4-point Gauss-Duffy (positive weights).
    z,w=np.polynomial.legendre.leggauss(4);z=(z+1)/2;w=w/2
    u,v=np.meshgrid(z,z,indexing='ij');u=u.ravel();v=v.ravel()
    lam=np.stack([1-u,u*(1-v),u*v],axis=1);weights=(w[:,None]*w[None,:]).ravel()*u
    B=np.zeros((N,field(xy[:1]).shape[1]));surface=0.
    for ids in tri:
        t=xy[ids];jac=abs(np.linalg.det((t[1:]-t[0]).T));surface+=jac/2
        B[ids]+=lam.T@((jac*weights)[:,None]*field(lam@t))
    A,_,_=properties(np.asarray(poly));assert abs(volume-A*height)<1e-10 and abs(surface-A)<1e-10
    assert abs(float(np.ones(N)@(M@np.ones(N)))*c*c-volume)<1e-10
    constant=float(np.linalg.norm(K@np.ones(N)))
    print('G3_CAVITY_CONSTANT '+str(dict(n=n,nz=nz,residual=constant)),flush=True)
    assert constant<1e-9
    return dict(M=M,K=K,B=B,xyz=xyz,tet=tet,xy=xy,tri=tri,volume=volume,area=A,rho=rho,c=c,constantResidual=constant)

def observer(model,points):
    xyz=model['xyz'];tet=model['tet'];t=xyz[tet]
    J=np.transpose(t[:,1:]-t[:,:1],(0,2,1));inv=np.linalg.inv(J)
    O=np.zeros((len(points),len(xyz)))
    for j,p in enumerate(points):
        v=np.einsum('tij,tj->ti',inv,p-t[:,0]);lam=np.c_[1-v.sum(1),v]
        candidates=np.flatnonzero(np.min(lam,axis=1)>=-1e-10)
        if not len(candidates):raise ValueError('observer outside closed cavity')
        i=candidates[0];O[j,tet[i]]=lam[i]
    return O

def response(model,s,points):
    if s.real<0 or abs(s)==0:raise ValueError('nonzero right half plane required')
    M,K,B=(model[x] for x in ('M','K','B'));rho=model['rho']
    A=K+s*s*M;X=splu(A.astype(complex)).solve(B.astype(complex))
    Z=rho*s*(B.T@X);P=rho*s*observer(model,points)@X
    H=(Z+Z.conj().T)/2
    expected=rho*s.real*(X.conj().T@(K@X)+abs(s)**2*X.conj().T@(M@X))
    den=max(np.linalg.norm(Z),1e-30)
    rec=float(np.linalg.norm(Z-Z.T)/den);power=float(np.linalg.norm(H-expected)/den)
    pas=float(min(np.linalg.eigvalsh(H))/den);res=float(np.linalg.norm(A@X-B)/max(np.linalg.norm(B),1e-30))
    return Z,P,dict(reciprocity=rec,powerRelative=power,passivityMinRelative=pas,residual=res,
        gate=rec<=1e-8 and power<=1e-8 and pas>=-1e-8 and res<=1e-8)
