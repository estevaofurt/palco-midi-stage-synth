"""Exterior spatial/temporal FFT reference using archived physical operators."""
import ast,json,time,argparse
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from scipy.fft import fft2,ifft2,idctn,rfftn,irfftn,next_fast_len
FINE=384000; C=343.; RHO=1.204; M=8

def load_defs(root,file,names):
    p=root/file; t=ast.parse(p.read_text()); nodes=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in names]
    assert {x.name for x in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),globals())
def rel(a,b):return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-300))
def geometry(root):
    z=np.load(root/'G3_Cavidade_Compactacao_Local/adaptive_candidate.npz');n=30
    low=lambda c:np.min(z['lam'][z['ch']==c]);dx=C*np.pi/np.sqrt(low(60))/n;dy=C*np.pi/np.sqrt(low(2))/n;h=C*np.pi/np.sqrt(low(1))
    sc=np.linalg.norm(z['T'],axis=0)*np.sqrt(dx*dy); A=idctn((z['T']*np.sqrt(dx*dy)/sc).reshape(n,n,80),axes=(0,1),norm='ortho').reshape(n*n,80)
    E=np.zeros((n*n,len(z['ix'])));E[z['ix'],np.arange(len(z['ix']))]=1;B=idctn(E.reshape(n,n,-1),axes=(0,1),norm='ortho').reshape(n*n,-1)
    return SimpleNamespace(n=n,dx=dx,dy=dy,h=h),A,B,sc,z['ix']
def embed(k):
    n=k.shape[-1];i=np.minimum(np.arange(2*n),2*n-np.arange(2*n));v=i<n;i=np.minimum(i,n-1)
    return k[...,i[:,None],i[None,:]]*(v[:,None]&v[None,:])
def project_symbol(k,A,B):
    n=k.shape[-1];X=fft2(A.reshape(n,n,-1),s=(2*n,2*n),axes=(0,1));Y=fft2(B.reshape(n,n,-1),s=(2*n,2*n),axes=(0,1));H=fft2(embed(k),axes=(-2,-1))
    conv=lambda x,y:ifft2(x*y[:,:,None],axes=(0,1))[:n,:n].reshape(n*n,-1)
    J=A.T@conv(Y,H[1]);return np.block([[A.T@conv(X,H[0]),J],[J.T,B.T@conv(Y,H[0])]])
def temporal_grid(G,Q):
    n=G.shape[-1];d=Q.shape[1];L=(G.shape[1]+M-2)//M+1;K=np.zeros((2,L,d,d,n,n))
    for a in range(M):
      for b in range(M):
        l=np.arange(L)*M+a-b;ok=(l>=0)&(l<G.shape[1]);K[:,ok]+=G[:,l[ok],None,None]*np.outer(Q[a],Q[b])[None,None,:,:,None,None]
    return K
def apply(K,A,B,u):
    n=K.shape[-1];d=K.shape[2];p=A.shape[1];N=len(u)+K.shape[1]-1;shape=(next_fast_len(N),2*n,2*n)
    U=np.stack([np.einsum('tdp,ip->tdi',u[:,:,:p],A).reshape(len(u),d,n,n),np.einsum('tdp,ip->tdi',u[:,:,p:],B).reshape(len(u),d,n,n)])
    X=rfftn(U,s=shape,axes=(1,3,4));Y=np.zeros_like(X)
    for a in range(d):
      for b in range(d):
        for k in range(2):
          H=rfftn(embed(K[k,:,a,b]),s=shape,axes=(0,1,2));Y[0,:,a]+=H*X[k,:,b];Y[1,:,a]+=H*X[1-k,:,b]
    V=irfftn(Y,s=shape,axes=(1,3,4))[:,:N,:,:n,:n].reshape(2,N,d,n*n)
    return np.concatenate([V[0]@A,V[1]@B],axis=-1)
def main(root,out):
    load_defs(root,'G3_Exterior_Cascas/shells.py',['stepavg','weights']);load_defs(root,'G3_Multirate_Expansao/expand.py',['grid_delays']);load_defs(root,'G3_Acoplamento_Multirate/multirate.py',['basis','block_kernel']);m,A,B,sc,ix=geometry(root);Q=basis(M,3);rng=np.random.default_rng(271127);rows=[];checks=[]
    def ck(k,v,tol=1e-10):checks.append(dict(name=k,value=float(v),limit=tol,ok=bool(v<tol)));assert v<tol,(k,v)
    print('geometry',m,flush=True)
    def signal(typ,p):
      u=rng.normal(size=(24,3,p))
      if typ=='impulse':u[1:]=0
      if typ=='sine':u=Q.T@np.sin(2*np.pi*5183.7*np.arange(24*M).reshape(24,M,1)/FINE+np.arange(p)[None,None,:]*.3)
      return u
    for b,refpath,radpath in [(16,'G3_Acoplamento_Multirate/expanded-kernels.npz','G3_Exterior_Cascas/n30-b16.json'),(64,'G3_Multirate_Expansao/ports48.npz','G3_Exterior_Cascas/n30-b64-critical.json')]:
      global subradius
      a=json.loads((root/radpath).read_text())[0]['a'];subradius=lambda m,b:a
      t=time.perf_counter();G,_=grid_delays(m,b);print('grid',b,G.shape,time.perf_counter()-t,flush=True);z=np.load(root/refpath);idx=z['idx'];p=len(idx)//2;ia=idx[:p];ib=idx[p:]-80;aa=A[:,ia];bb=B[:,ib];expected=np.r_[sc[ia],np.sqrt(m.dx*m.dy)*np.sinc((ix[ib]//m.n)/(2*m.n))*np.sinc((ix[ib]%m.n)/(2*m.n))];ck(f'scales-{b}',rel(expected,z['scale']));ref=z['K']
      for f in (130.8128,2000,5183.7,8000,48000,97123.4):
        k=np.einsum('t,stij->sij',np.exp(-2j*np.pi*f/FINE*np.arange(G.shape[1])),G);v=project_symbol(k,aa,bb);r=np.einsum('t,tij->ij',np.exp(-2j*np.pi*f/FINE*np.arange(len(ref))),ref);ck(f'symbol-{b}-{f}',rel(v,r))
      K=temporal_grid(G,Q);D=block_kernel(ref,Q,Q);print('block',b,K.shape,D.shape,flush=True)
      for typ in ('impulse','noise','sine'):
        u=signal(typ,2*p);t=time.perf_counter();v=apply(K,aa,bb,u);sec=time.perf_counter()-t;r=np.zeros((len(u)+len(D)-1,3*2*p));uf=u.reshape(len(u),-1)
        for j in range(len(D)):r[j:j+len(u)]+=uf@D[j].T
        r=r.reshape(-1,3,2*p);N=max(len(v),len(r));pad=lambda x:np.pad(x,((0,N-len(x)),(0,0),(0,0)));err=rel(pad(v),pad(r));ck(f'temporal-{b}-{typ}',err);rows.append(dict(b=b,ports=2*p,kind=typ,error=err,seconds=sec));print(rows[-1],flush=True)
      if b==64:
        f=5183.7;freq=f+np.arange(M)*FINE/M;E=np.exp(2j*np.pi*np.outer(np.arange(M),freq)/FINE)/np.sqrt(M);T=Q.T@E;ZZ=[]
        for fj in freq:
          k=np.einsum('t,stij->sij',np.exp(-2j*np.pi*fj/FINE*np.arange(G.shape[1])),G);ZZ.append(project_symbol(k,A,B))
        for typ in ('impulse','noise','sine'):
          u=signal(typ,369);t=time.perf_counter();v=apply(K,A,B,u);sec=time.perf_counter()-t;w0=np.sum(u*v[:len(u)],axis=(1,2))/FINE;minimum=float(min(0,np.cumsum(w0).min())/max(np.sum(abs(w0)),1e-300));ck(f'full-passivity-{typ}',-minimum);assert np.isfinite(v).all()
          U=np.einsum('t,tdp->dp',np.exp(-2j*np.pi*f/(FINE/M)*np.arange(len(u))),u);V=np.einsum('t,tdp->dp',np.exp(-2j*np.pi*f/(FINE/M)*np.arange(len(v))),v);Y=np.zeros_like(V)
          for j,Z in enumerate(ZZ):Y+=T[:,j,None]*(Z@(T[:,j].conj()@U))[None,:]
          e=rel(V,Y);ck(f'full-frequency-replay-{typ}',e);rows.append(dict(b=b,ports=369,kind=typ,seconds=sec,minimum_work=minimum,symbol_replay=e));print(rows[-1],flush=True)
        densebytes=K.shape[1]*(3*369)**2*8;gridbytes=K.nbytes;np.savez_compressed(out/'grid-b64.npz',G=G,A=A,B=B,Q=Q,dx=m.dx,dy=m.dy,h=m.h,rate=FINE);print('storage',gridbytes,densebytes,flush=True)
      del K,D,G
    (out/'results.json').write_text(json.dumps(dict(geometry=vars(m),rows=rows,checks=checks,grid_block_bytes=gridbytes,dense_full_bytes=densebytes),indent=2));print('PASS',len(checks),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--out',type=Path,default=Path(__file__).parent);a=p.parse_args();main(a.root,a.out)
