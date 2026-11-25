"""Outgoing 3-D Helmholtz scattering by a closed rigid obstacle.
MFS sources must lie strictly inside a closed solid. Not valid directly for
a zero-thickness screen or open cabinet. Benchmark: exact Neumann sphere.
Convention exp(i omega t).
"""
import numpy as np
from scipy.special import spherical_jn,spherical_yn,eval_legendre
from scipy.spatial.distance import cdist
from split_radiation import relative

def sphere_points(n,phase=0.):
    i=np.arange(n,dtype=float)+.5
    z=1-2*i/n;phi=i*np.pi*(3-np.sqrt(5))+phase
    return np.c_[np.sqrt(1-z*z)*np.cos(phi),np.sqrt(1-z*z)*np.sin(phi),z]

def green(x,y,k):
    r=cdist(np.atleast_2d(x),np.atleast_2d(y))
    if min(r.ravel())<=0:raise ValueError('coincident monopoles')
    return np.exp(-1j*k*r)/(4*np.pi*r)

def normal_derivative(x,n,y,k):
    x=np.asarray(x);n=np.asarray(n);y=np.asarray(y)
    d=x[:,None,:]-y[None,:,:];r=np.linalg.norm(d,axis=-1)
    if min(r.ravel())<=0:raise ValueError('coincident derivative')
    return np.exp(-1j*k*r)/(4*np.pi*r)*(-1j*k-1/r)*np.einsum('ijd,id->ij',d,n)/r

def solve_neumann(boundary,normals,internal,incident,k):
    """Multi-RHS least squares for outgoing equivalent monopole strengths.
    No passivity/reciprocity projection; audit at independent points.
    """
    A=normal_derivative(boundary,normals,internal,k)
    B=-normal_derivative(boundary,normals,incident,k)
    q,_,rank,sv=np.linalg.lstsq(A,B,rcond=1e-12)
    return q,dict(rank=int(rank),columns=len(internal),condition=float(sv[0]/sv[-1]),
        boundaryResidual=relative(A@q,B))

def exact_sphere_scattered(x,y,k,a,degree=24):
    """Scattered Green function outside a rigid sphere centered at origin."""
    x=np.atleast_2d(x);y=np.atleast_2d(y)
    r=np.linalg.norm(x,axis=1);s=np.linalg.norm(y,axis=1)
    if min(r)<a-1e-12 or min(s)<=a or min(k,a)<=0:raise ValueError('sphere exterior required')
    mu=np.clip((x/r[:,None])@(y/s[:,None]).T,-1,1)
    H=lambda l,z,der=False:spherical_jn(l,z,derivative=der)-1j*spherical_yn(l,z,derivative=der)
    result=np.zeros(mu.shape,complex)
    for l in range(degree+1):
        ratio=spherical_jn(l,k*a,derivative=True)/H(l,k*a,True)
        result+=(2*l+1)*ratio*H(l,k*r)[:,None]*H(l,k*s)[None,:]*eval_legendre(l,mu)
    return 1j*k/(4*np.pi)*result

def far_gram(sources,internal,q,k,order):
    mu,w=np.polynomial.legendre.leggauss(order)
    phi=2*np.pi*np.arange(4*order)/(4*order);s=np.sqrt(1-mu*mu)
    d=np.stack([s[:,None]*np.cos(phi),s[:,None]*np.sin(phi),np.broadcast_to(mu[:,None],(order,len(phi)))],axis=-1).reshape(-1,3)
    w=np.repeat(w*2*np.pi/len(phi),len(phi))
    F=np.exp(1j*k*(d@sources.T))+np.exp(1j*k*(d@internal.T))@q
    return F.conj().T@(w[:,None]*F)/(4*np.pi)

def source_impedance(sources,internal,q,k,rho,c):
    """Regularized radiating monopole impedance. Free-space imaginary
    self term is singular and omitted; finite radiation resistance is exact.
    """
    r=cdist(sources,sources);G=np.zeros(r.shape,complex)
    idx=r>0;G[idx]=np.exp(-1j*k*r[idx])/(4*np.pi*r[idx])
    G[np.diag_indices(len(r))]=-1j*k/(4*np.pi)
    return 1j*rho*c*k*(G+green(sources,internal,k)@q)

def benchmark(a,k,sources,observers,n,rho=1.204,c=343.):
    internal=.65*a*sphere_points(n)
    boundary=a*sphere_points(3*n,.27);normals=boundary/a
    q,rep=solve_neumann(boundary,normals,internal,sources,k)
    held=a*sphere_points(4*n+1,1.17)
    A=normal_derivative(held,held/a,internal,k)
    B=-normal_derivative(held,held/a,sources,k)
    near=green(observers,internal,k)@q
    exact=exact_sphere_scattered(observers,sources,k,a)
    Z=source_impedance(sources,internal,q,k,rho,c)
    R=(Z+Z.conj().T)/2
    expected=rho*c*k*k/(4*np.pi)*far_gram(sources,internal,q,k,28)
    rep.update(heldoutBoundaryResidual=relative(A@q,B),scatteredPressureRelative=relative(near,exact),
        reciprocity=relative(Z,Z.T),powerRelative=relative(R,expected),
        passivityMinRelative=float(min(np.linalg.eigvalsh(R))/max(np.linalg.norm(R),1e-30)))
    rep['gate']=rep['heldoutBoundaryResidual']<=.01 and rep['scatteredPressureRelative']<=.01 and rep['reciprocity']<=.01 and rep['powerRelative']<=.01 and rep['passivityMinRelative']>=-1e-8
    return near,Z,rep
