"""P0 weakly tested single-layer exterior BEM.
Both density and testing functions are constant per triangle. Integrate
the Neumann trace over target triangles, not just their centroids.
No algebraic symmetrization; no claim of a symmetric Calderon formulation.
"""
import numpy as np
from scipy.linalg import solve
from exterior_bem import elements,samples
from bem_static_split import operators
from split_radiation import relative

def assembly(t,k,outer,inner):
    x,w=samples(t,outer);_,n,a=elements(t)
    N=len(t);q=x.shape[1];S=np.zeros((N,N),complex);D=np.zeros_like(S)
    # Bounded memory: integrate one target quadrature slice at a time.
    ids=np.arange(N)
    for j in range(q):
        G,K=operators(t,x[:,j],n,ids,k,inner)
        S+=w[:,j,None]*G;D+=w[:,j,None]*K
    return S,D,dict(singleLayerReciprocity=relative(S,S.T),
        staticFluxBalance=relative(D.sum(0),-a) if k==0 else None,
        outerOrder=outer,innerOrder=inner)

def project(t,field,order):
    x,w=samples(t,order)
    V=np.asarray(field(x.reshape(-1,3)),float).reshape(len(t),x.shape[1],-1)
    return np.einsum('tq,tqm->tm',w,V)

def fit(S,D,B):
    if S.shape!=D.shape or D.shape[0]!=B.shape[0]:raise ValueError('incompatible weak operator')
    q=solve(D,-B,assume_a='gen')
    return q,dict(weakResidual=relative(D@q,-B),coefficientNorm=float(np.linalg.norm(q)))

def weak_impedance(S,B,q,areas,k,rho=1.204,c=343.):
    # P0 projection of the prescribed normal velocity in the work pairing.
    return 1j*rho*c*k*(B/areas[:,None]).T@S@q

def static_audit(t,outer,inner):
    S,D,r=assembly(t,0.,outer,inner)
    return dict(**r,minimumSingleLayerEigenvalue=float(np.linalg.eigvalsh((S.real+S.real.T)/2).min()))
