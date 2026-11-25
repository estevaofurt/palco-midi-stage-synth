"""Lower recess: exact vertical propagation, planar P1 FEM.
Local depth z=-world_z, board at z=0, artificial mouth at z=h.
Both prescribed normal velocities point into the cavity. The mouth is
not a rigid floor; its flux will be coupled to the exterior separately.
"""
import numpy as np
from scipy.linalg import eigh
from prism_cavity import build as prism_build,observer
from lid_exterior import Panel
from split_radiation import relative

def mouth_panel(poly,h,count):
    return Panel(np.c_[poly,np.full(len(poly),-h)],np.array([0.,0.,-1.]),count)

def build(poly,n,h,field,count,c=343.,rho=1.204):
    if h<=0:raise ValueError('positive recess depth required')
    mouth=mouth_panel(poly,h,count)
    def combined(x):
        return np.column_stack([field(x),mouth.basis(mouth.local(np.c_[x,np.full(len(x),-h)]))])
    m=prism_build(poly,n,h,combined,c,rho,field_order=6 if count in (45,55) else (5 if count in (28,36) else 4));nb=field(np.asarray(poly)[:1]).shape[1]
    lam,U=eigh(m['K'].toarray(),m['M'].toarray(),check_finite=True)
    if lam.min()<-1e-8:raise ValueError('negative planar eigenvalue')
    lam[np.abs(lam)<1e-8]=0.
    m.update(lam=lam,U=U,nb=nb,mouth=mouth,combined=combined)
    return m

def response(m,s,points):
    if s.real<0 or abs(s)==0:raise ValueError('nonzero right half plane required')
    h,c,rho,nb=m['height'],m['c'],m['rho'],m['nb']
    a=np.sqrt((m['lam']+(s/c)**2).astype(complex))
    e=np.exp(-a*h);den=-np.expm1(-2*a*h)
    if min(abs(a*den))<1e-10:raise ValueError('closed prism pole')
    selfTerm=(1+e*e)/(a*den);crossTerm=2*e/(a*den)
    B=m['U'].T@m['B'];B0=B[:,:nb];B1=B[:,nb:]
    Z=np.block([[B0.T@(selfTerm[:,None]*B0),B0.T@(crossTerm[:,None]*B1)],
                [B1.T@(crossTerm[:,None]*B0),B1.T@(selfTerm[:,None]*B1)]])
    pts=np.asarray(points,float).copy();pts[:,2]*=-1
    O=observer(m,pts)@m['U'];P=[]
    for o,z in zip(O,pts[:,2]):
        g0=(np.exp(-a*z)+np.exp(-a*(2*h-z)))/(a*den)
        g1=(np.exp(-a*(h-z))+np.exp(-a*(h+z)))/(a*den)
        P.append(np.r_[(o*g0)@B0,(o*g1)@B1])
    Z*=rho*s;P=rho*s*np.asarray(P)
    H=(Z+Z.conj().T)/2;scale=max(np.linalg.norm(Z),1e-30)
    rep=dict(reciprocity=relative(Z,Z.T),passivityMinRelative=float(np.linalg.eigvalsh(H).min()/scale),
        losslessRelative=float(np.linalg.norm(H)/scale),minimumPoleDistance=float(min(abs(a*den))))
    rep['gate']=rep['reciprocity']<=1e-8 and rep['passivityMinRelative']>=-1e-8 and (s.real>0 or rep['losslessRelative']<=1e-8)
    return Z,P,rep
