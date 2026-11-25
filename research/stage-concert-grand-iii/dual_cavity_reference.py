"""Reference-only algebra for upper and lower acoustic domains.
Convention: positive board velocity into upper air, negative into lower.
All port velocities point into their respective domain. Exterior velocity
is positive out of each cavity. No experimental BEM promotion.
"""
import numpy as np
from scipy.linalg import block_diag
from common_exterior import validated,herm
from split_radiation import relative

def couple(Zu,Pu,Zl,Pl,Ze,Pe,nb,*,reference_kind):
    if reference_kind!='common-free-space-monopole':
        raise ValueError('unsupported or uncertified exterior reference')
    Zu,Pu,Zl,Pl,Ze,Pe=map(np.asarray,(Zu,Pu,Zl,Pl,Ze,Pe))
    for Z,name in ((Zu,'upper'),(Zl,'lower'),(Ze,'exterior')):validated(Z,name)
    na=len(Zu)-nb;nl=len(Zl)-nb
    if not 0<nb<min(len(Zu),len(Zl)) or Ze.shape!=(na+nl,na+nl):
        raise ValueError('incompatible port counts')
    for P,Z in ((Pu,Zu),(Pl,Zl),(Pe,Ze)):
        if P.ndim!=2 or P.shape[1]!=len(Z) or not np.isfinite(P).all():raise ValueError('invalid observer map')
    A=block_diag(Zu[nb:,nb:],Zl[nb:,nb:])+Ze
    B=np.vstack([Zu[nb:,:nb],-Zl[nb:,:nb]])
    F=np.linalg.solve(A,B);U,W=F[:na],F[na:]
    Qu=np.vstack([np.eye(nb),-U]);Ql=np.vstack([-np.eye(nb),-W])
    Cu=Zu@Qu;Cl=Zl@Ql;Ce=Ze@F
    total=Cu[:nb]-Cl[:nb]
    internal=Qu.conj().T@herm(Zu)@Qu+Ql.conj().T@herm(Zl)@Ql
    R=herm(Ze);upper=U.conj().T@R[:na,:na]@U;lower=W.conj().T@R[na:,na:]@W
    cross=U.conj().T@R[:na,na:]@W+W.conj().T@R[na:,:na]@U
    external=F.conj().T@R@F
    den=max(np.linalg.norm(total),1e-30)
    rep=dict(reciprocity=relative(total,total.T),
        upperPressureContinuity=relative(Cu[nb:],Ce[:na]),
        lowerPressureContinuity=relative(Cl[nb:],Ce[na:]),
        solveResidual=relative(A@F,B),
        powerRelative=float(np.linalg.norm(herm(total)-internal-external)/den),
        partitionRelative=float(np.linalg.norm(external-upper-lower-cross)/den),
        passivityMinRelative=float(np.linalg.eigvalsh(herm(total)).min()/den),
        upperPowerTrace=float(np.trace(upper).real/2),lowerPowerTrace=float(np.trace(lower).real/2),
        crossPowerTrace=float(np.trace(cross).real/2),exteriorPowerTrace=float(np.trace(external).real/2))
    rep['gate']=max(rep[k] for k in ('reciprocity','upperPressureContinuity','lowerPressureContinuity','solveResidual','powerRelative','partitionRelative'))<=1e-8 and rep['passivityMinRelative']>=-1e-8
    rep.update(referenceOnly=True,physicalCavityCertified=False,finiteRimNeumannReady=False,radiationReady=False)
    return total,Pu@Qu,Pl@Ql,Pe@F,F,rep
