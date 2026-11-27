"""Exact delayed dyadic convolution. Real kernel spectra and deadline-spread tiles.
For input block [e-b,e), lags [2b,4b), first output at e+b.
At commits e..e+b-1, compute disjoint spatial tiles, before any output is due.
"""
import numpy as np
from scipy.fft import fft,ifft,rfft,next_fast_len
from numba import njit
from constant_stream import ConstantStream,accumulate

@njit
def tile_product(F,X,idx,sgn,spatial):
    d=idx.shape[0]; nt=X.shape[-1]; half=F.shape[-1];Y=np.zeros_like(X)
    for j in range(X.shape[1]):
        p=spatial[j]
        for a in range(d):
            for b in range(d):
                r=idx[a,b];s=sgn[a,b]
                for k in range(nt):
                    kk=k if k<half else nt-k
                    f0=F[0,r,p,kk];f1=F[1,r,p,kk]
                    if k>=half:f0=f0.conjugate();f1=f1.conjugate()
                    f0*=s;f1*=s;v=X[1+b,j,k]
                    Y[1+a,j,k]+=f0*v
                    if b==0:
                        w=X[0,j,k];Y[1+a,j,k]+=f1*w
                        if a==0:Y[0,j,k]+=f0*w
                    if a==0:Y[0,j,k]+=f1*v
    return Y

class ScheduledStream(ConstantStream):
    def __init__(self,K,A,B,Q,head=32,workers=1):
        super().__init__(K,A,B,Q)
        if head<2 or head&(head-1):raise ValueError('head must be power of two >=2')
        self.head=head;self.workers=workers;self.parts=[];b=head//2
        while 2*b<self.L:
            length=min(2*b,self.L-2*b);nt=next_fast_len(b+length-1)
            v=self.F[:,2*b:2*b+length].transpose(0,2,3,4,1).reshape(2,-1,(self.n+1)**2,length)
            F=rfft(np.ascontiguousarray(v),n=nt,axis=-1,workers=workers)
            self.parts.append((b,length,nt,F));b*=2
        self.F=self.F[:,:min(head,self.L)].copy()
        self.H=min(self.L,max(head,b));self.X0=self.X0[:self.H].copy();self.X1=self.X1[:self.H].copy()
        self.ring=np.zeros((self.L,self.d+1,2*self.n,self.n+1),complex)
        i,j=np.indices((2*self.n,self.n+1));self.spatial=(np.minimum(i,2*self.n-i)*(self.n+1)+j).ravel().astype(np.int64)
    def reset(self):super().reset();self.ring.fill(0)
    def history(self):
        y0,y1=self.empty();accumulate(y0,y1,self.F,self.X0,self.X1,self.t,self.H,min(self.t,self.head-1,self.L-1),1,self.idx,self.sgn)
        tail=self.ring[self.t%self.L]
        return self.decode((y0+tail[:1],y1+tail[1:]))
    def commit(self,u,h):
        x0,x1=self.encode(u);y=self.empty();accumulate(*y,self.F,x0[None],x1[None],0,1,1,0,self.idx,self.sgn)
        self.ring[self.t%self.L]=0;self.X0[self.t%self.H]=x0;self.X1[self.t%self.H]=x1
        pixels=len(self.spatial)
        for b,length,nt,F in self.parts:
            if self.t<b:continue
            phase=self.t%b;e=self.t-phase;lo=pixels*phase//b;hi=pixels*(phase+1)//b
            if hi==lo:continue
            ids=np.arange(e-b,e)%self.H
            a=self.X0.reshape(self.H,1,pixels)[ids,:,lo:hi];c=self.X1.reshape(self.H,self.d,pixels)[ids,:,lo:hi]
            X=fft(np.ascontiguousarray(np.concatenate((a,c),axis=1).transpose(1,2,0)),n=nt,axis=-1,workers=self.workers)
            V=ifft(tile_product(F,X,self.idx,self.sgn,self.spatial[lo:hi]),axis=-1,workers=self.workers,overwrite_x=True)[...,:b+length-1].transpose(2,0,1)
            start=(e+b)%self.L;first=min(len(V),self.L-start);ring=self.ring.reshape(self.L,self.d+1,pixels)
            ring[start:start+first,:,lo:hi]+=V[:first];ring[:len(V)-first,:,lo:hi]+=V[first:]
        self.t+=1;return h+self.decode(y)
    @property
    def bytes(self):return self.F.nbytes+self.X0.nbytes+self.X1.nbytes+self.ring.nbytes+self.spatial.nbytes+sum(f.nbytes for _,_,_,f in self.parts)
