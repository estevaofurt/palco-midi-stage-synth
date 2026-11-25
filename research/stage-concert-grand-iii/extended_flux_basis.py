"""Experimental degree-six/seven aperture basis. Preserve old coordinates
through degree five. Whiten planar geometry and use weighted QR instead of
forming a monomial Gram matrix, which squares the condition number.
"""
import numpy as np
from scipy.linalg import solve_triangular
from numpy.polynomial.legendre import legvander
from board_contour import properties
from ribbed_plate import quadrature

class ExtendedFluxBasis:
    def __init__(self,poly,count):
        if count not in (28,36):raise ValueError('degree six or seven required')
        self.count=count;self.degree={28:6,36:7}[count]
        poly=np.asarray(poly,float)
        self.area,self.center,_=properties(poly)
        xy,w=quadrature(poly,12)
        X=xy-self.center
        C=X.T@(w[:,None]*X)/self.area
        lam,U=np.linalg.eigh(C)
        if not np.isfinite(lam).all() or min(lam)<=0:raise ValueError('degenerate panel covariance')
        whiten=U/np.sqrt(lam)[None,:]
        span=np.max(abs((poly-self.center)@whiten),axis=0)
        self.map=whiten/span[None,:]
        A=np.sqrt(w/self.area)[:,None]*self.raw(xy)
        _,R=np.linalg.qr(A,mode='reduced')
        # Fix sign of the constant and all diagonal factors.
        R=np.where(np.diag(R)<0,-1.,1.)[:,None]*R
        self.condition=float(np.linalg.cond(R))
        if not np.isfinite(self.condition) or self.condition>1e10:raise ValueError('ill-conditioned extended aperture basis')
        self.T=solve_triangular(R,np.eye(count),lower=False)
    def raw(self,xy):
        x,y=((np.atleast_2d(xy)-self.center)@self.map).T
        X=legvander(x,self.degree);Y=legvander(y,self.degree)
        return np.column_stack([X[:,d-j]*Y[:,j] for d in range(self.degree+1) for j in range(d+1)])
    def __call__(self,xy,poly=None):
        return self.raw(xy)@self.T/self.area
