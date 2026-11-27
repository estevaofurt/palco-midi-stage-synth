"""Exact parity and spatial symmetry compression; upper d3 fixed."""
import numpy as np
from scipy.fft import rfft2,irfft2
from numba import njit
from spatial import embed
@njit
def accumulate(y0,y1,F,X0,X1,t,L,count,offset,idx,sgn):
    d=y1.shape[0]; h=y1.shape[1]//2
    for l in range(count):
        k=(t-l-offset)%L
        for a in range(d):
            for b in range(d):
                r=idx[a,b];s=sgn[a,b]
                for i in range(2*h):
                    ii=min(i,2*h-i)
                    for j in range(h+1):
                        f0=s*F[0,l+offset,r,ii,j];f1=s*F[1,l+offset,r,ii,j];v1=X1[k,b,i,j]
                        if b<3:
                            v0=X0[k,b,i,j];y1[a,i,j]+=f0*v1+f1*v0
                            if a<3:y0[a,i,j]+=f0*v0+f1*v1
                        else:
                            y1[a,i,j]+=f0*v1
                            if a<3:y0[a,i,j]+=f1*v1
class ParityStream:
    def __init__(self,K,A,B,Q):
        self.A=A;self.B=B;self.n=n=K.shape[-1];self.d=d=K.shape[2];self.L=L=K.shape[1];self.p=A.shape[1];self.q=B.shape[1]
        assert d>=3 and np.max(abs(Q[::-1]-Q*(-1.)**np.arange(d)))<1e-13
        self.idx=np.empty((d,d),np.int64);self.sgn=np.ones((d,d));pairs=[]
        for a in range(d):
            for b in range(a,d):
                self.idx[a,b]=self.idx[b,a]=len(pairs);self.sgn[b,a]=(-1.)**(a+b);pairs.append((a,b))
        self.F=np.empty((2,L,len(pairs),n+1,n+1));err=0.
        for r,(a,b) in enumerate(pairs):
            v=K[:,:,a,b];w=K[:,:,b,a];den=max(np.max(abs(v)),1e-300)
            err=max(err,float(np.max(abs(w-self.sgn[b,a]*v))/den))
            f=rfft2(embed(v),axes=(-2,-1));den=max(np.max(abs(f.real)),1e-300)
            err=max(err,float(np.max(abs(f.imag))/den),float(np.max(abs(f.real[:,:,1:n]-f.real[:,:,-1:n:-1]))/den))
            self.F[:,:,r]=f.real[:,:,:n+1]
        self.symmetry_error=err;assert err<1e-12,err
        self.X0=np.zeros((L,3,2*n,n+1),complex);self.X1=np.zeros((L,d,2*n,n+1),complex);self.t=0
    def reset(self):self.X0.fill(0);self.X1.fill(0);self.t=0
    def encode(self,u):
        assert u.shape==(self.d,self.p+self.q) and np.isfinite(u).all() and not np.any(u[3:,:self.p])
        a=(u[:3,:self.p]@self.A.T).reshape(3,self.n,self.n);b=(u[:,self.p:]@self.B.T).reshape(self.d,self.n,self.n)
        return tuple(rfft2(v,s=(2*self.n,2*self.n),axes=(-2,-1)) for v in (a,b))
    def empty(self):return np.zeros_like(self.X0[0]),np.zeros_like(self.X1[0])
    def decode(self,y):
        out=np.zeros((self.d,self.p+self.q))
        for v,A,rows,cols in [(y[0],self.A,slice(0,3),slice(0,self.p)),(y[1],self.B,slice(None),slice(self.p,None))]:
            f=irfft2(v,s=(2*self.n,2*self.n),axes=(-2,-1))[...,:self.n,:self.n].reshape(len(v),-1);out[rows,cols]=f@A
        return out
    def history(self):
        y=self.empty();accumulate(*y,self.F,self.X0,self.X1,self.t,self.L,min(self.t,self.L-1),1,self.idx,self.sgn);return self.decode(y)
    def direct(self,u):
        x0,x1=self.encode(u);y=self.empty();accumulate(*y,self.F,x0[None],x1[None],0,1,1,0,self.idx,self.sgn);return self.decode(y)
    def preview(self,u):return self.history()+self.direct(u)
    def commit(self,u,h):
        x0,x1=self.encode(u);y=self.empty();accumulate(*y,self.F,x0[None],x1[None],0,1,1,0,self.idx,self.sgn)
        self.X0[self.t%self.L]=x0;self.X1[self.t%self.L]=x1;self.t+=1;return h+self.decode(y)
    def step(self,u):return self.commit(u,self.history())
