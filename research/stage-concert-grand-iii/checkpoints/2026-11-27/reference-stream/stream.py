"""Dyadic causal convolution, current-interval direct term, no extra sample delay."""
import numpy as np
from scipy.fft import rfft,irfft
class Stream:
 def __init__(self,K,A=None):
  self.A=A;self.parts=[];b=1
  if A is None:self.head=K[0].copy();n=len(K)
  else:
   r,n,p,q=K.shape;_,d,e=A.shape;self.e=e;self.q=q
   self.head=np.einsum('rab,rij->aibj',A,K[:,0]).reshape(d*p,e*q)
  self.no,self.ni=self.head.shape
  while b<n:
   F=rfft(K[b:2*b],n=2*b,axis=0) if A is None else rfft(K[:,b:2*b],n=2*b,axis=1).transpose(1,0,2,3).copy()
   self.parts.append((b,F));b*=2
  self.ring=np.zeros((2*b,self.no));self.inputs=np.zeros((b,self.ni));self.t=0
 @property
 def bytes(self):return self.head.nbytes+self.ring.nbytes+self.inputs.nbytes+sum(F.nbytes for _,F in self.parts)+(0 if self.A is None else self.A.nbytes)
 def reset(self):self.t=0;self.ring.fill(0);self.inputs.fill(0)
 def history(self):return self.ring[self.t%len(self.ring)].copy()
 def preview(self,u):return self.history()+self.head@u
 def step(self,u):
  u=np.asarray(u,dtype=float)
  if u.shape!=(self.ni,) or not np.isfinite(u).all():raise ValueError('invalid input')
  y=self.preview(u);self.ring[self.t%len(self.ring)]=0;self.inputs[self.t%len(self.inputs)]=u
  for b,F in self.parts:
   if (self.t+1)%b:continue
   v=self.inputs[(self.t+1-b)%len(self.inputs):self.t%len(self.inputs)+1]
   if self.A is None:
    U=rfft(v,n=2*b,axis=0);Y=np.einsum('fij,fj->fi',F,U)
   else:
    U=rfft(v.reshape(b,self.e,self.q),n=2*b,axis=0);V=F@U.transpose(0,2,1)[:,None,:,:];Y=np.einsum('rae,frpe->fap',self.A,V,optimize=True)
   Y=irfft(Y,n=2*b,axis=0)[:-1].reshape(2*b-1,self.no)
   self.ring[(self.t+1+np.arange(len(Y)))%len(self.ring)]+=Y
  self.t+=1;return y

class Direct:
 """Reference causal FIR; duplicated ring avoids reordering history each step."""
 def __init__(self,K):
  self.K=K;self.head=K[0];self.n=len(K);self.no,self.ni=self.head.shape;self.buf=np.zeros((2*self.n,self.ni));self.t=0
 @property
 def bytes(self):return self.K.nbytes+self.buf.nbytes
 def reset(self):self.t=0;self.buf.fill(0)
 def history(self):
  i=(-self.t)%self.n;return np.einsum('kij,kj->i',self.K[1:],self.buf[i+1:i+self.n])
 def preview(self,u):return self.history()+self.head@u
 def step(self,u):
  y=self.preview(u);i=(-self.t)%self.n;self.buf[i]=self.buf[i+self.n]=u;self.t+=1;return y
