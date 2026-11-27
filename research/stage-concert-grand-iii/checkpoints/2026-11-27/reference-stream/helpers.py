import numpy as np

def basis(M,d):
 t=(np.arange(M)+.5)/M*2-1
 Q,R=np.linalg.qr(np.polynomial.legendre.legvander(t,d-1));return Q*np.sign(np.diag(R))

def block_kernel(K,Qin,Qout):
 M,d=Qin.shape;do=Qout.shape[1];_,p,q=K.shape;N=(len(K)+M-2)//M+1
 R=np.zeros((N,do,p,d,q))
 for a in range(M):
  for b in range(M):
   lag=np.arange(N)*M+a-b;ok=(lag>=0)&(lag<len(K));R[ok]+=np.einsum('i,kpq,j->kipjq',Qout[a],K[lag[ok]],Qin[b])
 return R.reshape(N,do*p,d*q)

def rel(a,b):return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-300))

def factors(K,Q):
 M,d=Q.shape;N=(len(K)+M-2)//M+1; offsets=np.arange(1-M,M); C=np.array([sum((np.outer(Q[a],Q[b]) for a in range(M) for b in range(M) if a-b==r),np.zeros((d,d))) for r in offsets]);U,s,V=np.linalg.svd(C.reshape(len(offsets),d*d),full_matrices=False);k=int(np.sum(s>s[0]*1e-13));W=U[:,:k]*s[:k];A=V[:k].reshape(k,d,d);B=np.zeros((k,N,*K.shape[1:]));
 for j,r in enumerate(offsets):
  l=np.arange(N)*M+r;ok=(l>=0)&(l<len(K));B[:,ok]+=W[j,:,None,None,None]*K[l[ok]][None]
 return A,B,s,rel(W@V[:k],C.reshape(len(offsets),d*d))
