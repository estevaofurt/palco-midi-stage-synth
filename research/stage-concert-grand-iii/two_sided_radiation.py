"""Two independent acoustic domains on a common structural velocity.
Upper: cavity with optional free-space aperture reference. Lower: infinite
baffle. This does NOT solve external mutual radiation around a finite rim.
All fields use peak phasors exp(i omega t).
"""
import numpy as np
from split_radiation import relative

def herm(A):return (A+A.conj().T)/2

def combine(Zup,Zdown,up_map,down_map):
    """Work-conjugate maps from one structural velocity to two fluid ports."""
    Zup,Zdown=np.asarray(Zup),np.asarray(Zdown)
    U,L=np.asarray(up_map,float),np.asarray(down_map,float)
    if U.ndim!=2 or L.ndim!=2 or U.shape[1]!=L.shape[1]:raise ValueError('common structural velocity required')
    parts=[]
    for Z,A in ((Zup,U),(Zdown,L)):
        if Z.shape!=(A.shape[0],A.shape[0]) or not np.isfinite(Z).all():raise ValueError('invalid acoustic operator')
        if relative(Z,Z.T)>1e-8:raise ValueError('nonreciprocal side')
        if min(np.linalg.eigvalsh(herm(Z))) < -1e-10*max(np.linalg.norm(Z),1e-30):raise ValueError('active side')
        parts.append(A.T@Z@A)
    zu,zl=parts;z=zu+zl
    err=relative(herm(z),herm(zu)+herm(zl))
    rec=relative(z,z.T)
    pas=float(min(np.linalg.eigvalsh(herm(z)))/max(np.linalg.norm(z),1e-30))
    return z,(zu,zl),dict(powerRelative=err,reciprocity=rec,passivityMinRelative=pas,
        gate=err<=1e-8 and rec<=1e-8 and pas>=-1e-10)

def fixture(M,K,D,z,parts,f):
    """Independent frequency-domain mechanical power audit; no piano fit."""
    M,K,D=map(np.asarray,(M,K,D));omega=2*np.pi*f
    V=1j*omega*np.linalg.solve(K-omega**2*M+1j*omega*(D+z),np.eye(len(M)))
    P=herm(V);wood=V.conj().T@D@V
    up,down=[V.conj().T@herm(q)@V for q in parts]
    den=max(np.linalg.norm(P),1e-30)
    e=float(np.linalg.norm(P-wood-up-down)/den)
    vals=[float(np.trace(q).real) for q in (wood,up,down)]
    rec=relative(V,V.T)
    pas=float(min(np.linalg.eigvalsh(P))/den)
    return V,dict(powerRelative=e,reciprocity=rec,passivityMinRelative=pas,
        powerFractions=dict(structure=vals[0]/sum(vals),upper=vals[1]/sum(vals),lower=vals[2]/sum(vals)),
        gate=e<=1e-8 and rec<=1e-8 and pas>=-1e-10 and min(vals)>=-1e-10)
