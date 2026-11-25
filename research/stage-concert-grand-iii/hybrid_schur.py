"""Exact block elimination of wedge interior nodes with sparse LU.
Only the prism interface is dense. No modal truncation or added loss.
The sparse interior factorization is reused across all right hand sides.
"""
import numpy as np
from scipy.sparse import issparse
from scipy.sparse.linalg import splu
from scipy.linalg import solve
from split_radiation import relative

def solve_interface(W,D,B,block=32):
    if not issparse(W):raise ValueError('sparse wedge operator required')
    D=np.asarray(D);B=np.asarray(B);N=len(D);size=W.shape[0]
    if W.shape!=(size,size) or D.shape!=(N,N) or B.ndim!=2 or B.shape[0]!=size or not 0<N<size or not isinstance(block,int) or block<1:
        raise ValueError('invalid interface dimensions')
    if not all(np.isfinite(x).all() for x in (W.data,D,B)):
        raise ValueError('nonfinite operator')
    dtype=np.result_type(W.dtype,D.dtype,B.dtype)
    W=W.astype(dtype).tocsc();D=D.astype(dtype,copy=False);B=B.astype(dtype,copy=False)
    A=W[:N,:N].toarray()+D
    E=W[:N,N:].tocsc();F=W[N:,:N].tocsc()
    C=W[N:,N:].tocsc()
    lu=splu(C)
    # Stream the Schur correction. No dense interior-by-interface inverse.
    for start in range(0,N,block):
        stop=min(start+block,N)
        A[:,start:stop]-=E@lu.solve(F[:,start:stop].toarray())
    rhs=B[:N]-E@lu.solve(B[N:])
    Xr=solve(A,rhs,assume_a='gen')
    Xi=lu.solve(B[N:]-F@Xr)
    X=np.vstack([Xr,Xi])
    R=W@X;R[:N]+=D@Xr
    residual=relative(R,B)
    if not np.isfinite(X).all() or residual>1e-8:raise ValueError('Schur solution failed full residual audit')
    sparse_bytes=lambda x:int(x.data.nbytes+x.indices.nbytes+x.indptr.nbytes)
    return X,dict(solver='schur',residual=residual,interfaceNodes=N,interiorNodes=size-N,
        fullDenseMatrixBytes=int(size*size*np.dtype(dtype).itemsize),interfaceDenseMatrixBytes=A.nbytes,
        sparseFactorBytes=sparse_bytes(lu.L)+sparse_bytes(lu.U),columnBlock=block,
        interfaceReciprocity=relative(A,A.T))
