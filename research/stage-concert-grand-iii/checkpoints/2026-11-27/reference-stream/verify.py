import ast,sys,time,json,platform
from pathlib import Path
import numpy as np,scipy
from scipy.fft import rfft,irfft,next_fast_len
from stream import Stream
ROOT=Path(sys.argv[1]);OUT=Path(__file__).parent
from helpers import basis,block_kernel,factors,rel
checks=[];rows=[]
def check(name,ok):checks.append(dict(name=name,ok=bool(ok)));assert ok,name
rng=np.random.default_rng(281127)
for n in (1,2,3,7,8,9,31,33,101):
 K=rng.normal(size=(n,4,3));u=rng.normal(size=(257,3));S=Stream(K);y=np.array([S.step(v) for v in u]);ref=np.zeros_like(y)
 for i,k in enumerate(K):ref[i:]+=u[:len(u)-i]@k.T
 check(f'generic-{n}',rel(y,ref)<1e-12);S.reset();check(f'reset-{n}',np.array_equal(y,np.array([S.step(v) for v in u])))
def batch(K,u):
 n=next_fast_len(len(u)+len(K)-1);U=rfft(u,n=n,axis=0);y=np.empty((len(u),K.shape[1]))
 for i in range(K.shape[1]):y[:,i]=irfft(np.einsum('fi,fi->f',rfft(K[:,i,:],n=n,axis=0),U),n=n)[:len(u)]
 return y
def run(S,u):
 t=time.perf_counter();y=np.array([S.step(v) for v in u]);return y,time.perf_counter()-t
for p in (6,12,24,48):
 z=np.load(ROOT/'G3_Multirate_Expansao'/('ports48.npz' if p==48 else 'ports24.npz'));n=len(z['idx']);sel=np.r_[np.arange(p//2),n//2+np.arange(p//2)];Q=basis(8,3)
 for name,k in [('exterior',z['K'][:,sel][:,:,sel]),('receiver',z['H'][:,:,sel])]:
  D=block_kernel(k,Q,Q);A,B,_,_=factors(k,Q);P=Stream(D);F=Stream(B,A);L=len(D);N=2*L+128
  row=dict(ports=p,operator=name,taps=L,raw_dense_bytes=D.nbytes,dense_stream_bytes=P.bytes,factored_stream_bytes=F.bytes,trials=[])
  for kind in ('noise','pulse','sine'):
   u=np.zeros((N,3*p));na=128
   if kind=='pulse':u[0]=rng.normal(size=3*p);na=1
   elif kind=='noise':u[:na]=rng.normal(size=(na,3*p))
   else:
    t=np.arange(na*8)/384000;v=np.sin(2*np.pi*5183.7*t[:,None]+np.arange(p)[None,:]*.3);u[:na]=(Q.T@v.reshape(na,8,p)).reshape(na,-1)
   ref=batch(D,u);P.reset();F.reset();y,td=run(P,u);f,tf=run(F,u);e1=rel(y,ref);e2=rel(f,ref);pre=f'{p}-{name}-{kind}'
   check(pre+'-dense',e1<1e-11);check(pre+'-factor',e2<1e-11);tail=float(np.linalg.norm(f[na+L-1:])/max(np.linalg.norm(ref),1e-300));check(pre+'-tail',tail<1e-11)
   F.reset();v=F.preview(u[0]);w=F.preview(u[0]);check(pre+'-preview',F.t==0 and np.array_equal(v,w) and np.array_equal(v,F.step(u[0])))
   tr=dict(kind=kind,steps=N,dense_error=e1,factor_error=e2,tail_error=tail,dense_s=td,factor_s=tf)
   if name=='exterior':
    wr=np.sum(ref*u,axis=1)/384000;wf=np.sum(f*u,axis=1)/384000;s=max(np.sum(abs(wr)),1e-300);err=float(np.max(abs(np.cumsum(wf-wr)))/s);mi=float(min(0,np.min(np.cumsum(wf)))/s);check(pre+'-work',err<1e-11);check(pre+'-passivity',mi>=-1e-10);tr.update(work_error=err,min_work=mi)
   row['trials'].append(tr)
  rows.append(row);print(p,name,L,[(x['kind'],x['factor_error'],round(x['dense_s'],4),round(x['factor_s'],4)) for x in row['trials']],flush=True);del D,A,B,P,F
  res=dict(environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),rows=rows,checks=checks,passed=sum(x['ok'] for x in checks),total=len(checks));(OUT/'results.json').write_text(json.dumps(res,indent=2))
print(res['passed'],res['total'],flush=True)
