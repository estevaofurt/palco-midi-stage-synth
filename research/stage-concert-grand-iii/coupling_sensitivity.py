"""Sensitivity of the coupled reference in physical L2 velocity coordinates.
x = W F, W = diag(1/sqrt(panel area)), pressure dual b = W^-1 B.
A_phys = W^-1 A W^-1. No regularization or modification of the solve.
"""
import numpy as np
from scipy.linalg import block_diag,svdvals,solve

def prepare(Zu,Zl,Ze,nb,counts,areas):
    Zu,Zl,Ze=map(np.asarray,(Zu,Zl,Ze));areas=np.asarray(areas,float)
    if not isinstance(nb,int) or not 0<nb<min(len(Zu),len(Zl)) or any(z.ndim!=2 or z.shape[0]!=z.shape[1] or not np.isfinite(z).all() for z in (Zu,Zl,Ze)):
        raise ValueError('invalid coupled matrices')
    if areas.shape!=(len(counts),) or not np.isfinite(areas).all() or np.any(areas<=0) or any(not isinstance(n,(int,np.integer)) or n<1 for n in counts):
        raise ValueError('invalid port geometry')
    na=len(Zu)-nb;nl=len(Zl)-nb
    if Ze.shape!=(na+nl,na+nl) or sum(counts)!=na+nl:
        raise ValueError('invalid port dimensions')
    A=block_diag(Zu[nb:,nb:],Zl[nb:,nb:])+Ze
    B=np.vstack([Zu[nb:,:nb],-Zl[nb:,:nb]])
    scale=np.repeat(np.sqrt(areas),counts)
    M=scale[:,None]*A*scale[None,:];rhs=scale[:,None]*B
    sigma=svdvals(M)
    if sigma[-1]<=0 or not np.isfinite(sigma).all():
        raise ValueError('singular physical coupling')
    return dict(A=M,B=rhs,scale=scale,sigmaMin=float(sigma[-1]),
        report=dict(physicalCondition=float(sigma[0]/sigma[-1]),sigmaMin=float(sigma[-1]),sigmaMax=float(sigma[0])))

def compare_sensitivity(old,new,F0,F1):
    F0,F1=map(np.asarray,(F0,F1))
    s=old['scale']
    if not np.array_equal(s,new['scale']) or F0.shape!=F1.shape or F0.shape!=old['B'].shape or F1.shape!=new['B'].shape or not all(np.isfinite(x).all() for x in (F0,F1)):
        raise ValueError('incompatible physical flows')
    X0=F0/s[:,None];X1=F1/s[:,None];A0,A1=old['A'],new['A'];B0,B1=old['B'],new['B']
    norm=lambda x:float(np.linalg.norm(x))
    den=max(norm(X1),1e-30)
    r0=A0@X0-B0;r1=A1@X1-B1
    # Exact signed identity: A1 (X0-X1)=(B0-B1)+(A1-A0)X0+r0-r1.
    force=B0-B1;operator=(A1-A0)@X0
    terms=solve(A1,np.column_stack([force,operator,r0-r1]),assume_a='gen')
    n=F0.shape[1];u,v,e=np.split(terms,[n,2*n],axis=1)
    delta=X0-X1;closure=norm(delta-u-v-e)/den
    if not np.isfinite(terms).all() or closure>1e-8:
        raise ValueError('sensitivity decomposition failed closure')
    bound=(norm(force)+norm(operator)+norm(r0-r1))/new['sigmaMin']/den
    actual=norm(delta)/den
    if actual>bound+1e-8:raise ValueError('invalid singular value bound')
    return dict(physicalFlowChange=actual,excitationContribution=norm(u)/den,
        impedanceContribution=norm(v)/den,numericalResidualContribution=norm(e)/den,
        decompositionClosure=closure,upperBound=float(bound),
        excitationImpedanceAlignment=float(np.vdot(u,v).real/max(norm(u)*norm(v),1e-30)),
        relativeExcitationChange=norm(force)/max(norm(B1),1e-30),
        relativeOperatorChange=norm(A1-A0)/max(norm(A1),1e-30),
        oldPhysicalCondition=old['report']['physicalCondition'],newPhysicalCondition=new['report']['physicalCondition'])
