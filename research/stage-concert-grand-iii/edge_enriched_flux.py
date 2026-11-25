"""Experimental localized edge trial space, not an asserted singular exponent.
Preserve the degree-nine polynomial span and append independently
orthogonalized edge functions. Width is a dimensionless numerical
trial-space parameter, not a fitted acoustic or material parameter.
"""
import numpy as np
from ribbed_plate import quadrature
from split_radiation import relative

class EdgeEnrichedFlux:
    def __init__(self,poly,base,width,*,order=40):
        self.poly=np.asarray(poly,float);self.base=base;self.area=base.area
        if base.count!=55 or not np.isfinite(width) or not 0<width<.25 or order<24:
            raise ValueError('invalid edge enrichment')
        self.width=float(width);self.a=self.poly;d=np.roll(self.poly,-1,axis=0)-self.a
        length=np.linalg.norm(d,axis=1)
        if np.any(length<=0):raise ValueError('degenerate edges')
        self.t=d/length[:,None];self.n=np.c_[-self.t[:,1],self.t[:,0]];self.length=length
        self.height=np.max(np.einsum('ped,ed->pe',self.poly[:,None,:]-self.a[None,:,:],self.n),axis=0)
        if np.any(self.height<=0):raise ValueError('invalid edge orientation')
        x,w=quadrature(self.poly,order);W=w/self.area
        P=self.area*base(x);Q=self.raw(x)
        M=P.T@(W[:,None]*P)
        if relative(M,np.eye(55))>1e-8:raise ValueError('invalid polynomial mass')
        self.projection=np.linalg.solve(M,P.T@(W[:,None]*Q))
        E=Q-P@self.projection
        _,s,V=np.linalg.svd(np.sqrt(W)[:,None]*E,full_matrices=False)
        if s[-1]<=1e-8*s[0] or s[-1]<=1e-10:raise ValueError('dependent edge enrichment')
        self.transform=V.T/s[None,:];self.condition=float(s[0]/s[-1]);self.count=55+len(s)
        self.extraCount=len(s)
    def raw(self,xy):
        d=np.asarray(xy,float)[:,None,:]-self.a[None,:,:]
        z=np.einsum('ped,ed->pe',d,self.n)/self.height
        u=2*np.einsum('ped,ed->pe',d,self.t)/self.length-1
        e=np.exp(-z/self.width)
        return np.stack([e,u*e],axis=-1).reshape(len(d),-1)
    def __call__(self,xy,poly=None):
        P=self.area*self.base(xy)
        E=(self.raw(xy)-P@self.projection)@self.transform
        return np.column_stack([P,E])/self.area
    def audit(self,order=56):
        x,w=quadrature(self.poly,order);B=self(x)
        mass=self.area*B.T@(w[:,None]*B)
        integral=w@B
        expected=np.r_[1.,np.zeros(self.count-1)]
        return dict(massRelative=relative(mass,np.eye(self.count)),
            maximumIntegralError=float(np.max(abs(integral-expected))),
            baselineRelative=relative(B[:,:55],self.base(x)),
            condition=self.condition,extraCount=self.extraCount)
