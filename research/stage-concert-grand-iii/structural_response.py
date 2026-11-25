"""Energy-equilibrated complex mechanical response, no modification of physical parameters.
A = K - omega^2 M + i omega D; precondition by K + omega^2 M + omega D.
All ports transformed by the same congruence; no symmetrization of computed mobility.
"""
import numpy as np
from scipy.linalg import cholesky,solve,solve_triangular

def symmetric(A):
    err=float(np.linalg.norm(A-A.T)/max(np.linalg.norm(A),1e-30))
    if err>1e-12:raise ValueError(f'nonsymmetric matrix: {err}')
    return (A+A.T)/2,err

def congruence(L,A):
    B=solve_triangular(L,A,lower=True,check_finite=False)
    B=solve_triangular(L,B.T,lower=True,check_finite=False).T
    return (B+B.T)/2

def metrics(Y,X,D,omega,units):
    # Average harmonic power identity: Hermitian(Y) = omega^2 X^H D X.
    Z=Y*units[:,None]*units[None,:]
    H=(Z+Z.conj().T)/2
    Q=X*units[None,:]
    expected=omega**2*(Q.conj().T@D@Q)
    return dict(reciprocity=float(np.linalg.norm(Y-Y.T)/max(np.linalg.norm(Y),1e-30)),
        passivityMinRelative=float(min(np.linalg.eigvalsh(H))/max(np.linalg.norm(H),1e-30)),
        powerRelative=float(np.linalg.norm(H-expected)/max(np.linalg.norm(H),np.linalg.norm(expected),1e-30)))

def response(M,K,D,P,freq,units,method='energy'):
    M,em=symmetric(M);K,ek=symmetric(K);D,ed=symmetric(D)
    units=np.asarray(units);assert len(units)==P.shape[1]
    # First diagonal mass equilibration, then energy congruence at each frequency.
    s=1/np.sqrt(np.diag(M));W=s[:,None]*s[None,:]
    M=M*W;K=K*W;D=D*W;P=P*s[:,None]
    Y=[];records=[]
    for f in freq:
        omega=2*np.pi*f;assert omega>0
        A=K-omega**2*M+1j*omega*D
        if method=='energy':
            L=cholesky(K+omega**2*M+omega*D,lower=True)
            # Transform the two terms independently to avoid subtractive cancellation
            # before scaling, especially with tiny cut-cell supports.
            E=congruence(L,K);B=congruence(L,omega**2*M);C=congruence(L,omega*D)
            G=E-B+1j*C
            R=solve_triangular(L,P,lower=True)
            V=solve(G,R,assume_a='gen')
            Z=1j*omega*(R.T@V)
            X=solve_triangular(L.T,V,lower=False)
            row=metrics(Z,V,C/omega,omega,units)
            row['scaledResidual']=float(np.linalg.norm(G@V-R)/max(np.linalg.norm(R),1e-30))
            row['normalizationResidual']=float(np.linalg.norm(E+B+C-np.eye(len(E)))/np.sqrt(len(E)))
        elif method=='direct':
            X=solve(A,P,assume_a='gen');Z=1j*omega*(P.T@X)
            row=metrics(Z,X,D,omega,units)
        else:raise ValueError('unknown solver')
        row['originalResidual']=float(np.linalg.norm(A@X-P)/max(np.linalg.norm(P),1e-30))
        row['frequencyHz']=float(f)
        Y.append(Z);records.append(row)
    summary=dict(method=method,matrixAsymmetry=[em,ek,ed],
       reciprocity=max(x['reciprocity'] for x in records),
       passivityMinRelative=min(x['passivityMinRelative'] for x in records),
       powerRelative=max(x['powerRelative'] for x in records),
       originalResidual=max(x['originalResidual'] for x in records),
       scaledResidual=max((x.get('scaledResidual',0.) for x in records)),
       normalizationResidual=max((x.get('normalizationResidual',0.) for x in records)))
    summary['gate']=summary['reciprocity']<=1e-8 and summary['passivityMinRelative']>=-1e-8 and summary['powerRelative']<=1e-6 and summary['originalResidual']<=1e-5
    if method=='energy':summary['gate']=summary['gate'] and summary['scaledResidual']<=1e-8 and summary['normalizationResidual']<=1e-5
    return np.array(Y),summary,records
