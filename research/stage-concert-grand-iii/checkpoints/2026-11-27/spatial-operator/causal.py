"""Causal spatial history and non-mutating preview; offline reference."""
import json,time
from pathlib import Path
import numpy as np
from scipy.fft import rfft2,irfft2
from spatial import embed,temporal_grid,apply,rel
class SpatialStream:
 def __init__(self,K,A,B):
  self.A=A;self.B=B;self.n=K.shape[-1];self.d=K.shape[2];self.p=A.shape[1];self.q=B.shape[1];self.L=K.shape[1];n=self.n
  self.F=rfft2(embed(K),axes=(-2,-1));self.X=np.zeros((self.L,2,self.d,2*n,n+1),complex);self.t=0
 def encode(self,u):
  u=np.asarray(u,dtype=float)
  if u.shape!=(self.d,self.p+self.q) or not np.isfinite(u).all():raise ValueError('invalid input')
  a=(u[:,:self.p]@self.A.T).reshape(self.d,self.n,self.n);b=(u[:,self.p:]@self.B.T).reshape(self.d,self.n,self.n)
  return rfft2(np.stack([a,b]),s=(2*self.n,2*self.n),axes=(-2,-1))
 def decode(self,y):
  v=irfft2(y,s=(2*self.n,2*self.n),axes=(-2,-1))[...,:self.n,:self.n].reshape(2,self.d,-1)
  return np.concatenate([v[0]@self.A,v[1]@self.B],axis=-1)
 def history_spec(self):
  n=min(self.t,self.L-1);y=np.zeros_like(self.X[0]);
  if n:
   x=self.X[(self.t-np.arange(1,n+1))%self.L];f=self.F[:,1:n+1]
   for k in range(2):y[k]=np.einsum('labij,lbij->aij',f[0],x[:,k])+np.einsum('labij,lbij->aij',f[1],x[:,1-k])
  return y
 def direct_spec(self,x):
  f=self.F[:,0];return np.array([np.einsum('abij,bij->aij',f[0],x[k])+np.einsum('abij,bij->aij',f[1],x[1-k]) for k in range(2)])
 def history(self):return self.decode(self.history_spec())
 def direct(self,u):return self.decode(self.direct_spec(self.encode(u)))
 def preview(self,u):return self.decode(self.history_spec()+self.direct_spec(self.encode(u)))
 def step(self,u):
  x=self.encode(u);y=self.decode(self.history_spec()+self.direct_spec(x));self.X[self.t%self.L]=x;self.t+=1;return y
 def reset(self):self.X.fill(0);self.t=0

def main():
 p=Path(__file__).parent;z=np.load(p/'grid-b64.npz');K=temporal_grid(z['G'],z['Q']);A=z['A'];B=z['B'];S=SpatialStream(K,A,B);rng=np.random.default_rng(271128);u=rng.normal(size=(40,3,369));ref=apply(K,A,B,u);checks={};rows=[];t=time.perf_counter()
 for j,x in enumerate(u):
  a=S.preview(x);b=S.preview(x);assert S.t==j;assert np.array_equal(a,b);h=S.history();d=S.direct(x);y=S.step(x);assert S.t==j+1;rows.append([rel(y,ref[j]),rel(a,y),rel(h+d,y)])
 elapsed=time.perf_counter()-t;checks['max_batch_error'],checks['max_preview_error'],checks['max_split_error']=np.max(rows,axis=0).tolist();assert max(checks.values())<1e-10
 S.reset();checks['reset_error']=rel(S.step(u[0]),ref[0]);assert checks['reset_error']<1e-10
 t=time.perf_counter();S.reset();Y=np.array([S.step(x) for x in u]);elapsed_step=time.perf_counter()-t;assert rel(Y,ref[:len(u)])<1e-10
 # Prefix invariance: batch convolution with no future inputs produces same prefix.
 checks['prefix_error']=rel(apply(K,A,B,u[:17])[:17],ref[:17]);assert checks['prefix_error']<1e-10
 data=dict(checks=checks,steps=len(u),elapsed_all=elapsed,elapsed_step=elapsed_step,mean_step_us=elapsed_step/len(u)*1e6,fft_kernel_bytes=S.F.nbytes,history_bytes=S.X.nbytes)
 (p/'causal-results.json').write_text(json.dumps(data,indent=2));print(data,flush=True)
if __name__=='__main__':main()
