"""Exact dyadic tail, compressed real spatial/parity kernels, direct short head.
The block [b,2b) of lags cannot contribute before the b-input block is closed.
"""
import numpy as np
from scipy.fft import fft,ifft
from numba import njit,prange
from constant_stream import ConstantStream,accumulate

@njit(parallel=True)
def product(F,X,idx,sgn):
    d=idx.shape[0]; nx=X.shape[1];ny=X.shape[2];nt=X.shape[3]
    Y=np.zeros_like(X)
    for i in prange(nx):
        ii=min(np.int64(i),nx-np.int64(i))
        for j in range(ny):
            for a in range(d):
                for b in range(d):
                    r=idx[a,b];s=sgn[a,b]
                    for k in range(nt):
                        f0=s*F[0,r,ii,j,k];f1=s*F[1,r,ii,j,k];v=X[1+b,i,j,k]
                        Y[1+a,i,j,k]+=f0*v
                        if b==0:
                            w=X[0,i,j,k];Y[1+a,i,j,k]+=f1*w
                            if a==0:Y[0,i,j,k]+=f0*w
                        if a==0:Y[0,i,j,k]+=f1*v
    return Y

class HybridStream(ConstantStream):
    def __init__(self,K,A,B,Q,head=32,workers=4):
        super().__init__(K,A,B,Q)
        if head<1 or head&(head-1):raise ValueError('head must be power of two')
        self.head=head;self.workers=workers;self.parts=[];b=head
        while b<self.L:
            f=fft(np.ascontiguousarray(self.F[:,b:min(2*b,self.L)].transpose(0,2,3,4,1)),n=2*b,axis=-1,workers=workers)
            self.parts.append((b,f));b*=2
        self.F=self.F[:,:min(head,self.L)].copy()
        self.ring=np.zeros((max(1,b),self.d+1,2*self.n,self.n+1),complex)
    def reset(self):
        super().reset();self.ring.fill(0)
    def history(self):
        y0,y1=self.empty();accumulate(y0,y1,self.F,self.X0,self.X1,self.t,self.L,min(self.t,self.head-1,self.L-1),1,self.idx,self.sgn)
        tail=self.ring[self.t%len(self.ring)]
        return self.decode((y0+tail[:1],y1+tail[1:]))
    def commit(self,u,h):
        x0,x1=self.encode(u);y=self.empty();accumulate(*y,self.F,x0[None],x1[None],0,1,1,0,self.idx,self.sgn)
        self.ring[self.t%len(self.ring)]=0;self.X0[self.t%self.L]=x0;self.X1[self.t%self.L]=x1
        for b,F in self.parts:
            if (self.t+1)%b:continue
            ids=np.arange(self.t+1-b,self.t+1)%self.L
            x=np.concatenate((self.X0[ids],self.X1[ids]),axis=1)
            X=fft(np.ascontiguousarray(x.transpose(1,2,3,0)),n=2*b,axis=-1,workers=self.workers)
            V=ifft(product(F,X,self.idx,self.sgn),axis=-1,workers=self.workers,overwrite_x=True)[...,:2*b-1].transpose(3,0,1,2)
            start=(self.t+1)%len(self.ring);first=min(len(V),len(self.ring)-start)
            self.ring[start:start+first]+=V[:first];self.ring[:len(V)-first]+=V[first:]
        self.t+=1;return h+self.decode(y)
    @property
    def bytes(self):return self.F.nbytes+self.X0.nbytes+self.X1.nbytes+self.ring.nbytes+sum(f.nbytes for _,f in self.parts)
