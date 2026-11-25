"""G3.06b complete one-sided Rayleigh impedance in Laplace domain.
Weak 1/r singularity integrated by a fan centered at each target point.
Re[s] >= 0, causal continuum kernel rho*s*exp(-s*r/c)/(2*pi*r).
No time-domain passive approximation or actual piano enclosure.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss
from ribbed_plate import quadrature

def impedance(poly,fields,s,rho,c,outer,inner):
    poly=np.asarray(poly,dtype=float);s=complex(s)
    if s.real<0 or min(rho,c)<=0:raise ValueError('right half plane and positive medium required')
    xy,w=quadrature(poly,outer);S=fields(xy,poly)
    z,wt=leggauss(inner);t=(z+1)/2;wt=wt/2
    # y=x+u*((1-v)*(a-x)+v*(b-x)); Jacobian u*cross, r=u*length.
    # Cancel u analytically, never invent a self-distance.
    u,v=np.meshgrid(t,t,indexing='ij');W=(wt[:,None]*wt[None,:]).ravel()
    u=u.ravel();v=v.ravel();Z=np.zeros((S.shape[1],S.shape[1]),complex)
    for x,weight,shape in zip(xy,w,S):
        q=np.zeros(S.shape[1],complex)
        for a,b in zip(poly,np.roll(poly,-1,axis=0)):
            A=a-x;B=b-x;det=A[0]*B[1]-A[1]*B[0]
            if det<=0:raise ValueError('strictly interior quadrature required')
            d=(1-v[:,None])*A+v[:,None]*B;L=np.linalg.norm(d,axis=1)
            y=x+u[:,None]*d
            q+=(W*det/L*np.exp(-s*u*L/c))@fields(y,poly)
        Z+=weight*np.outer(shape,q)
    return rho*s/(2*np.pi)*Z

def audit(Z):
    H=(Z+Z.conj().T)/2
    return dict(reciprocity=float(np.linalg.norm(Z-Z.T)/max(np.linalg.norm(Z),1e-30)),
      passivityMinRelative=float(min(np.linalg.eigvalsh(H))/max(np.linalg.norm(H),1e-30)))

def retarded_pressure(xy,w,S,points,t,derivative,rho,c):
    """Prescribed generalized velocity derivative; zero prehistory supplied by caller."""
    xy=np.asarray(xy);points=np.atleast_2d(points)
    if min(points[:,2])<=0 or min(rho,c)<=0:raise ValueError('upper half space required')
    d=np.linalg.norm(points[:,None,:]-np.c_[xy,np.zeros(len(xy))][None,:,:],axis=-1)
    vdot=derivative(t-d/c)
    if vdot.shape!=(*d.shape,S.shape[1]):raise ValueError('derivative shape')
    return rho/(2*np.pi)*np.sum(w[None,:]*np.sum(vdot*S[None,:,:],axis=-1)/d,axis=1)
