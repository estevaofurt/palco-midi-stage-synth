"""Coordinate bridge for the *reference* common exterior load.
Cavity uses [board, canonical apertures], exterior [apertures, board].
Transform physical velocities and dual pressures by congruence.
No certification or promotion of an experimental BEM operator.
"""
import numpy as np
from scipy.linalg import block_diag
from scipy.spatial.distance import cdist
from common_exterior import eliminate,validated
from port_coordinates import transform
from split_radiation import relative

def vertices(p):return p.world(p.poly)
def normal(p):return np.cross(p.axes[:,0],p.axes[:,1])
def compatible(a,b,tol=1e-9):
    x,y=vertices(a),vertices(b);d=cdist(x,y)
    return max(d.min(0).max(),d.min(1).max())<=tol and np.linalg.norm(normal(a)-normal(b))<=tol

def bridge(cavity_panels,exterior_panels,board,order=16):
    """Return E mapping canonical exterior coordinates into actual ones.
    Require a unique geometric match (including orientation) per aperture.
    Board basis is checked by actual samples rather than assumed orthogonal.
    """
    if len(exterior_panels)!=len(cavity_panels)+1:raise ValueError('wrong number of exterior ports')
    if not compatible(exterior_panels[-1],board):raise ValueError('board geometry or orientation mismatch')
    old=exterior_panels[:-1];indices=[];blocks=[];errors=[]
    for a in cavity_panels:
        matches=[j for j,o in enumerate(old) if compatible(o,a)]
        if len(matches)!=1 or matches[0] in indices:raise ValueError('ambiguous or missing aperture match')
        j=matches[0];indices.append(j);T,rep=transform([old[j]],[a],order)
        if max(rep.values())>1e-8:raise ValueError('incompatible aperture fields')
        blocks.append(T);errors.append(max(rep.values()))
    _,x,w,V=board.samples(order);U=exterior_panels[-1].basis(exterior_panels[-1].local(x))
    if U.shape!=V.shape or relative(U,V)>1e-8:raise ValueError('board field mismatch')
    nb=V.shape[1];blocks.append(np.eye(nb))
    offsets=np.r_[0,np.cumsum([a.basis.count for a in exterior_panels])]
    perm=np.concatenate([np.arange(offsets[j],offsets[j+1]) for j in indices+[len(old)]])
    E=np.zeros((offsets[-1],offsets[-1]));E[perm,:]=block_diag(*blocks)
    orth=relative(E.T@E,np.eye(len(E)))
    if orth>1e-8:raise ValueError('nonorthogonal coordinate map')
    return E,dict(aperturePermutation=indices,fieldRelative=max(errors,default=0.),boardFieldRelative=relative(U,V),orthogonalityRelative=orth,gate=True)

def reference_couple(Zc,Pc,Ze,Pe,E,nb,*,reference_kind):
    """Only the validated common monopole reference is supported here.
    Reject unapproved scattering/BEM loads rather than symmetrizing them.
    """
    if reference_kind!='common-free-space-monopole':raise ValueError('unsupported or uncertified exterior reference')
    Zc,Pc,Ze,Pe,E=map(np.asarray,(Zc,Pc,Ze,Pe,E))
    if E.shape!=Ze.shape or Pe.ndim!=2 or Pe.shape[1]!=len(E) or not all(np.isfinite(x).all() for x in (E,Pe)):
        raise ValueError('incompatible exterior coordinate dimensions')
    if np.iscomplexobj(E) or relative(E.T@E,np.eye(len(E)))>1e-8:raise ValueError('invalid coordinate map')
    validated(Ze,'original exterior')
    canonical=E.T@Ze@E
    total,pi,U,Q,rep=eliminate(Zc,Pc,canonical,nb)
    Qactual=E@Q;pe=Pe@Qactual
    work=relative(Q.conj().T@canonical@Q,Qactual.conj().T@Ze@Qactual)
    rep['coordinateWorkRelative']=work
    rep['gate']=bool(rep['gate'] and work<=1e-8)
    rep.update(referenceOnly=True,finiteRimNeumannReady=False,radiationReady=False)
    return total,pi,pe,U,Qactual,rep
