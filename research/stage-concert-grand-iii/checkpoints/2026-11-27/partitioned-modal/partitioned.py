"""Exact dyadic temporal partitioning of spatial spectra. Offline prototype."""
import numpy as np
from scipy.fft import fft,ifft,rfft2
from causal import SpatialStream
from spatial import embed
class PartitionedStream(SpatialStream):
    def __init__(self,K,A,B):
        self.A=A; self.B=B; self.n=n=K.shape[-1]; self.d=d=K.shape[2]; self.p=A.shape[1];self.q=B.shape[1];self.L=L=K.shape[1]
        F=rfft2(embed(K),axes=(-2,-1));self.imag_ratio=float(np.max(abs(F.imag))/max(np.max(abs(F.real)),1e-300));assert self.imag_ratio<1e-13
        self.F=F[:,:1].real.copy();self.parts=[];b=1
        while b<L:
            f=fft(F[:,b:min(2*b,L)].real,n=2*b,axis=1).transpose(1,0,2,3,4,5).copy()
            self.parts.append((b,f));b*=2
        del F
        self.inputs=np.zeros((b,2,d,2*n,n+1),complex)
        self.ring=np.zeros((2*b,2,d,2*n,n+1),complex); self.t=0
    def history_spec(self): return self.ring[self.t%len(self.ring)].copy()
    def commit(self,u,h=None):
        x=self.encode(u);y=self.decode(self.history_spec()+self.direct_spec(x)) if h is None else h+self.decode(self.direct_spec(x))
        self.ring[self.t%len(self.ring)]=0;self.inputs[self.t%len(self.inputs)]=x
        for b,F in self.parts:
            if (self.t+1)%b:continue
            v=self.inputs[(self.t+1-b)%len(self.inputs):self.t%len(self.inputs)+1]
            X=fft(v,n=2*b,axis=0);Y=np.empty_like(X)
            for k in range(2):
                Y[:,k]=np.einsum('fabij,fbij->faij',F[:,0],X[:,k])+np.einsum('fabij,fbij->faij',F[:,1],X[:,1-k])
            V=ifft(Y,axis=0,overwrite_x=True)[:-1]
            start=(self.t+1)%len(self.ring);first=min(len(V),len(self.ring)-start)
            self.ring[start:start+first]+=V[:first];self.ring[:len(V)-first]+=V[first:]
        self.t+=1;return y
    def step(self,u):return self.commit(u)
    def reset(self):self.inputs.fill(0);self.ring.fill(0);self.t=0
    @property
    def bytes(self):return self.F.nbytes+sum(f.nbytes for _,f in self.parts)+self.inputs.nbytes+self.ring.nbytes
