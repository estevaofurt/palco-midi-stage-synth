"""Positive semidefinite hypothesis for extra internal modal loss.
Fixed-rear interior coordinates, not output EQ. No material calibration."""
import numpy as np
from distributed_felt import wire_loss

def extra_rates(w2,strength):
    w2=np.asarray(w2,float)
    if w2.ndim!=1 or len(w2)==0 or not np.isfinite(w2).all() or np.min(w2)<=0 or not np.isfinite(strength) or strength<0:
        raise ValueError('modal loss')
    # Smooth onset above 1.5 times the fixed-rear fundamental, plateau
    # at the fourth partial, preserving the lowest mode exactly.
    x=np.clip((np.sqrt(w2/w2[0])-1.5)/2.5,0.,1.)
    return strength*x*x*(3.-2.*x)

def mode_loss(wires,scale,strength):
    result=wire_loss(wires,scale)
    for w in result:
        delta=extra_rates(w.w2,strength)
        # Interior generalized eigenvectors are mass-orthonormal.
        # Dextra = Mii U diag(delta) U^T Mii. The rear coordinate
        # is unchanged; no extra cross terms with the rear.
        B=w.M[1:,1:]@w.U
        E=(B*delta)@B.T
        w.D[1:,1:]+=E
        w.gamma+=delta
        Dmodal=w.U.T@w.D[1:,1:]@w.U
        err=np.linalg.norm(Dmodal-np.diag(w.gamma))/max(np.linalg.norm(Dmodal),1e-30)
        if err>1e-8 or np.linalg.eigvalsh(E).min()<-1e-10*max(np.linalg.norm(E),1e-30):
            raise ValueError('modal damping consistency')
    return result
