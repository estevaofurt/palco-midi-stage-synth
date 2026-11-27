"""Opt-in extended precision coefficients, physical inputs unchanged."""
import numpy as np
import replay as r
def coefficients(lam,res,fs):
    L=np.longdouble;gamma=L(r.GAMMA);dt=L(1)/fs;h=gamma/2;w=np.sqrt(lam.astype(L));g=np.sqrt(res.astype(L));nz=w>0;k=np.sqrt(np.maximum(w*w-h*h,0));e=np.exp(-h*dt);angle=k*dt;sn=np.divide(np.sin(angle),k,out=np.full_like(k,dt),where=k!=0);co=np.cos(angle)
    a=e*(co+h*sn);b=e*w*sn;d=e*(co-h*sn);a[~nz]=1;d[~nz]=np.exp(-gamma*dt)
    eq=np.divide(g,w,out=np.zeros_like(g),where=nz);one_minus_a=-np.expm1(-h*dt)+e*(2*np.sin(angle/2)**2-h*sn);one_minus_a[~nz]=0;g0=one_minus_a*eq;g1=b*eq;g1[~nz]=g[~nz]*(-np.expm1(-gamma*dt))/gamma
    fac=np.divide(g,w*dt,out=np.zeros_like(g),where=nz);cx=-fac*one_minus_a;cv=fac*b;feed=fac*g0;mu=-np.expm1(-gamma*dt)/(gamma*dt);cv[~nz]=g[~nz]*mu;feed[~nz]=res[~nz]*(1-mu)/gamma
    new=np.array([a,b,-b,d,g0,g1,cx,cv,feed],dtype=float)
    assert np.isfinite(new).all()
    return new
def factory(original):
    class Refined(original):
        def __init__(self,l,res,B,fs):
            super().__init__(l,res,B,fs)
            self.a,self.b,self.c,self.d,self.g0,self.g1,self.cx,self.cv,self.feed=coefficients(l,res,fs)
            self.D=B.T@(self.feed[:,None]*B)
    return Refined
