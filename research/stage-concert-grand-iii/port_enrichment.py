"""Port-enriched Galerkin subspace. Real congruence preserves mechanical passivity.
No change of physical matrices or empirical compensation of acoustic response.
"""
import numpy as np
from scipy.linalg import cholesky,cho_solve,solve_triangular,eigh

def enrich(M,K,D,P,U,load,baseCount=96,levels=(128,192),shiftHz=30.):
    # Work in mass-diagonally equilibrated coordinates as in polygon_radiation.
    scale=1/np.sqrt(np.diag(M));W=scale[:,None]*scale[None,:]
    m=M*W;k=K*W;d=D*W;F=load*scale[:,None]
    B=U/scale[:,None]
    assert baseCount<=min(levels) and max(levels)<=B.shape[1]
    L=cholesky((k+k.T)/2+(2*np.pi*shiftHz)**2*(m+m.T)/2,lower=True)
    def append(Q,V):
        # Twice remove the M-orthogonal projection to avoid spurious rank.
        for _ in range(2):V=V-Q@(Q.T@(m@V))
        gram=V.T@m@V;norm=np.sqrt(np.maximum(np.diag(gram),0))
        keep=norm>max(np.max(norm)*1e-12,1e-30)
        if not np.any(keep):return Q,0
        V=V[:,keep]/norm[keep]
        g=V.T@m@V;ev,T=eigh((g+g.T)/2)
        keep=ev>ev[-1]*1e-10
        E=V@(T[:,keep]/np.sqrt(ev[keep]))
        return np.column_stack([Q,E]),int(sum(keep))
    Q=B[:,:baseCount].copy()
    # Shifted static compliance at all work-conjugate forcing locations.
    S=cho_solve((L,True),F)
    Q,rank=append(Q,S)
    sizes=[baseCount,Q.shape[1]];prior=baseCount
    for n in levels:
        Q,_=append(Q,B[:,prior:n]);prior=n;sizes.append(Q.shape[1])
    def project(A):
        a=Q.T@A@Q;return (a+a.T)/2
    mass=project(m);stiff=project(k);drag=project(d)
    ortho=float(np.linalg.norm(mass-np.eye(len(mass)),2))
    assert ortho<=1e-5
    return dict(U=scale[:,None]*Q,M=mass,K=stiff,D=drag,P=Q.T@(P*scale[:,None]),sizes=sizes,
      residualVectorRank=rank,massError=ortho,shiftHz=shiftHz)
