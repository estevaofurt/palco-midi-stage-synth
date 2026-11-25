"""Common free-space source reference for upper ports and lower board.
A reference of prescribed monopole sheets, NOT a finite-rim Neumann solution.
No infinite-baffle load is added to this common-space model.
"""
import numpy as np
from lid_exterior import Panel
from split_radiation import relative

def herm(A):return (A+A.conj().T)/2

class BoardField:
    def __init__(self,panel,field):
        self.panel=panel;self.field=field
        self.count=field(panel.world(panel.poly[:1])[:,:2]).shape[1]
    def __call__(self,xy):
        return self.field(self.panel.world(xy)[:,:2])

def board_panel(poly,field):
    poly=np.asarray(poly,float)
    p=Panel(np.c_[poly,np.zeros(len(poly))],np.array([0.,0.,-1.]),1)
    p.basis=BoardField(p,field)
    return p

def validated(Z,name):
    if Z.ndim!=2 or Z.shape[0]!=Z.shape[1] or not np.isfinite(Z).all():
        raise ValueError('invalid '+name)
    if relative(Z,Z.T)>1e-8:raise ValueError('nonreciprocal '+name)
    if min(np.linalg.eigvalsh(herm(Z))) < -1e-10*max(np.linalg.norm(Z),1e-30):
        raise ValueError('active '+name)

def eliminate(Zc,Pc,Ze,nb):
    """Cavity ordering [board, aperture]; exterior ordering [aperture, board].
    Positive board velocity into upper cavity; exterior board velocity -v.
    Interior aperture velocity -u, exterior +u. Solve pressure continuity
    without imposing independence of the two radiating surfaces.
    """
    Zc,Pc,Ze=map(np.asarray,(Zc,Pc,Ze))
    validated(Zc,'cavity');validated(Ze,'exterior')
    if Zc.shape!=Ze.shape or Pc.ndim!=2 or Pc.shape[1]!=len(Zc) or not 0<nb<len(Zc):
        raise ValueError('incompatible port dimensions')
    na=len(Zc)-nb;I=np.eye(nb)
    A=Zc[nb:,nb:]+Ze[:na,:na]
    B=Zc[nb:,:nb]+Ze[:na,na:]
    U=np.linalg.solve(A,B)
    Qc=np.vstack([I,-U]);Qe=np.vstack([U,-I])
    C=Zc@Qc;E=Ze@Qe
    total=C[:nb]-E[na:]
    Rc=Qc.conj().T@herm(Zc)@Qc
    R=herm(Ze)
    Rup=U.conj().T@R[:na,:na]@U
    Rdown=R[na:,na:]
    Rcross=-U.conj().T@R[:na,na:]-R[na:,:na]@U
    Rext=Qe.conj().T@R@Qe
    den=max(np.linalg.norm(total),1e-30)
    p=float(np.linalg.norm(herm(total)-Rc-Rext)/den)
    part=float(np.linalg.norm(Rext-Rup-Rdown-Rcross)/den)
    rep=dict(powerRelative=p,partitionRelative=part,reciprocity=relative(total,total.T),
        pressureContinuity=relative(C[nb:],E[:na]),
        passivityMinRelative=float(min(np.linalg.eigvalsh(herm(total)))/den),
        crossPowerTrace=float(np.trace(Rcross).real/2),
        upperPowerTrace=float(np.trace(Rup).real/2),lowerPowerTrace=float(np.trace(Rdown).real/2),
        exteriorPowerTrace=float(np.trace(Rext).real/2))
    rep['gate']=max(p,part,rep['reciprocity'],rep['pressureContinuity'])<=1e-8 and rep['passivityMinRelative']>=-1e-8
    return total,Pc@Qc,U,Qe,rep
