"""Closed prism exact vertical propagation coupled to P1 inclined wedge.
Harmonic reference only. Horizontal FE eigenbasis is complete, not truncated.
At a pole of the prism with homogeneous Dirichlet top, reject rather than damp.
"""
import numpy as np
from scipy.linalg import eigh,solve
from scipy.sparse import coo_matrix
from prism_cavity import build as prism_build,observer
from inclined_lid import build as inclined_build
from lid_exterior import ports
from split_radiation import relative

def build(poly,n,nz,height,angle,field,count,c=343.,rho=1.204,*,wedge_layers=1):
    if not 0<angle<90:raise ValueError('inclined lid required')
    m=prism_build(poly,n,height,field,c,rho)
    full,C0,report=inclined_build(poly,n,nz,height,angle,field,c,rho,wedge_layers=wedge_layers)
    N=len(m['xy']);old=N*(nz+1);rim=old-N
    np.testing.assert_allclose(full['xy'],m['xy'],atol=1e-13,rtol=0)
    tet=full['tet'][len(m['tri'])*3*nz:]-rim
    xyz=full['xyz'][rim:];size=len(xyz)
    assert tet.min()>=0 and tet.max()<size
    tt=xyz[tet];J=np.transpose(tt[:,1:]-tt[:,:1],(0,2,1))
    V=abs(np.linalg.det(J))/6
    grad=np.einsum('ij,tjk->tik',np.vstack([-np.ones(3),np.eye(3)]),np.linalg.inv(J))
    K=V[:,None,None]*(grad@np.transpose(grad,(0,2,1)))
    M=V[:,None,None]*(np.ones((4,4))+np.eye(4))/(20*c*c)
    i=np.repeat(tet,4,axis=1).ravel();j=np.tile(tet,(1,4)).ravel()
    K=coo_matrix((K.ravel(),(i,j)),shape=(size,size)).tocsc()
    M=coo_matrix((M.ravel(),(i,j)),shape=(size,size)).tocsc()
    assert abs(V.sum()-report['wedgeVolumeM3'])<1e-10
    panels,C=ports(full,C0,report,count,canonical=True)
    assert np.linalg.norm(C[:rim])<1e-12
    mass=m['M'].toarray();lam,U=eigh(m['K'].toarray(),mass,check_finite=True)
    if lam.min()<-1e-8:raise ValueError('negative horizontal eigenvalue')
    lam[np.abs(lam)<1e-8]=0
    return dict(prism=m,full=full,Cfull=C,panels=panels,C=C[rim:],K=K,M=M,
        N=N,lam=lam,U=U,MU=mass@U,report=report)

def vertical(lam,h,s,c):
    a=np.sqrt((lam+(s/c)**2).astype(complex));x=a*h
    # Exponential form prevents overflow in evanescent horizontal modes.
    e=np.exp(-x);den=1+e*e
    if min(abs(den))<1e-10:raise ValueError('prism Dirichlet-top pole')
    sech=2*e/den;tanh=(1-e*e)/den
    small=abs(x)<1e-7
    ratio=np.empty_like(a);ratio[small]=h*(1-x[small]**2/3)
    ratio[~small]=tanh[~small]/a[~small]
    return a,den,sech,a*tanh,ratio

def response(m,f,points,*,solver='dense'):
    if solver not in ('dense','schur'):raise ValueError('unknown hybrid solver')
    if f<=0:raise ValueError('positive harmonic frequency')
    s=2j*np.pi*f;p=m['prism'];h=p['height'];N=m['N'];U=m['U'];MU=m['MU'];B=p['B'];C=m['C']
    a,den,sech,d,ratio=vertical(m['lam'],h,s,p['c'])
    b=U.T@B;F=MU@(sech[:,None]*b)
    W=m['K']+s*s*m['M'];D=(MU*d[None,:])@MU.T
    rhs=np.column_stack([np.pad(F,((0,W.shape[0]-N),(0,0))),C])
    if solver=='dense':
        W=W.toarray();W[:N,:N]+=D
        X=solve(W,rhs,assume_a='gen')
        solve_report=dict(solver='dense',fullDenseMatrixBytes=W.nbytes,interfaceDenseMatrixBytes=D.nbytes)
        residual=relative(W@X,rhs)
    else:
        from hybrid_schur import solve_interface
        X,solve_report=solve_interface(W,D,rhs)
        residual=solve_report['residual']
    T=MU.T@X[:N]
    Z=rhs.T@X;nb=B.shape[1]
    Z[:nb,:nb]+=b.T@(ratio[:,None]*b)
    z=np.asarray(points,float)[:,2];O=observer(p,points)@U
    P=np.zeros((len(z),rhs.shape[1]),complex)
    for i,zi in enumerate(z):
        ctop=(np.exp(-a*(h-zi))+np.exp(-a*(h+zi)))/den
        # sinh(a*(h-z))/(a*cosh(a*h))
        r=np.empty_like(a);small=abs(a*h)<1e-7
        r[small]=h-zi
        r[~small]=(np.exp(-a[~small]*zi)-np.exp(-a[~small]*(2*h-zi)))/(a[~small]*den[~small])
        P[i]=(O[i]*ctop)@T
        P[i,:nb]+=(O[i]*r)@b
    Z*=p['rho']*s;P*=p['rho']*s
    H=(Z+Z.conj().T)/2;scale=max(np.linalg.norm(Z),1e-30)
    rep=dict(reciprocity=relative(Z,Z.T),losslessRelative=float(np.linalg.norm(H)/scale),
        residual=residual,interfaceCondition=float(min(abs(den))),linearSolve=solve_report)
    rep['gate']=rep['reciprocity']<=1e-8 and rep['losslessRelative']<=1e-8 and rep['residual']<=1e-8
    return Z,P,rep

def terminate(Z,P,Ze,nb):
    if Ze.shape!=(len(Z)-nb,len(Z)-nb):raise ValueError('exterior shape')
    R=(Ze+Ze.conj().T)/2
    if relative(Ze,Ze.T)>1e-8 or min(np.linalg.eigvalsh(R))<-1e-10*max(np.linalg.norm(Ze),1e-30):
        raise ValueError('invalid exterior')
    U=np.linalg.solve(Z[nb:,nb:]+Ze,Z[nb:,:nb]);Q=np.vstack([np.eye(nb),-U])
    Y=Z[:nb]@Q;H=(Y+Y.conj().T)/2
    expected=U.conj().T@R@U+Q.conj().T@((Z+Z.conj().T)/2)@Q
    den=max(np.linalg.norm(Y),1e-30)
    rep=dict(reciprocity=relative(Y,Y.T),powerRelative=float(np.linalg.norm(H-expected)/den),
        pressureContinuity=relative(Z[nb:]@Q,Ze@U),passivityMinRelative=float(min(np.linalg.eigvalsh(H))/den))
    rep['gate']=rep['reciprocity']<=1e-8 and rep['powerRelative']<=1e-8 and rep['pressureContinuity']<=1e-8 and rep['passivityMinRelative']>=-1e-8
    return Y,P@Q,U,rep
