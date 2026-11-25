"""G3.04a distributed vertical Euler-Bernoulli beam in arclength coordinates.
Rotational DOF is slope dw/ds; force/moment ports are conjugate.
No actual curved-frame kinematics, torsion, board or string mass.
"""
import numpy as np
from scipy.linalg import solve,eigh
def segment(L,rhoA,EI,kf):
    if min(L,rhoA,EI)<=0 or kf<0:raise ValueError('beam domain')
    l=L
    G=l/420*np.array([[156,22*l,54,-13*l],[22*l,4*l*l,13*l,-3*l*l],[54,13*l,156,-22*l],[-13*l,-3*l*l,-22*l,4*l*l]])
    K=EI/l**3*np.array([[12,6*l,-12,6*l],[6*l,4*l*l,-6*l,2*l*l],[-12,-6*l,12,-6*l],[6*l,2*l*l,-6*l,4*l*l]])
    return rhoA*G,K,kf*G
def build(nodes,subdiv,rho,E,width,height,kf):
    xyz=np.asarray(nodes,dtype=float)
    if xyz.ndim!=2 or xyz.shape[1]!=3 or len(xyz)<2 or subdiv<1:raise ValueError('nodes')
    lengths=np.linalg.norm(np.diff(xyz,axis=0),axis=1)
    if np.any(lengths<=0):raise ValueError('coincident attachment')
    s=np.r_[0.,np.cumsum(lengths)];mesh=np.concatenate([np.linspace(a,b,subdiv,endpoint=False) for a,b in zip(s,s[1:])]+[s[-1:]])
    nd=2*len(mesh);M=np.zeros((nd,nd));K=np.zeros_like(M);F=np.zeros_like(M)
    A=width*height;I=width*height**3/12
    for j,l in enumerate(np.diff(mesh)):
        m,k,f=segment(l,rho*A,E*I,kf);ids=np.arange(2*j,2*j+4)
        M[np.ix_(ids,ids)]+=m;K[np.ix_(ids,ids)]+=k;F[np.ix_(ids,ids)]+=f
    ids=np.arange(len(s))*2*subdiv
    return dict(M=M,K=K,foundation=F,mesh=mesh,attachmentDofs=ids,arclength=s,massKg=float(rho*A*s[-1]))
def response(model,indices,frequencies,alpha,beta):
    M=model['M'];K=model['K']+model['foundation'];D=alpha*M+beta*K
    n=len(M);P=np.zeros((n,2*len(indices)))
    for j,i in enumerate(indices):
        dof=model['attachmentDofs'][i];P[dof,2*j]=1.;P[dof+1,2*j+1]=1.
    # Work-conjugate force/moment, displacement/slope in arclength.
    static=P.T@solve(K,P,assume_a='pos')
    # Full mass-normalized eigensolve, no modal cutoff: exact Rayleigh FRF.
    w2,U=eigh(K,M);assert min(w2)>0
    Q=U.T@P;ys=[];recip=0.;minpass=0.
    for f in frequencies:
        w=2*np.pi*f;Y=(Q.T*(1j*w/(w2-w*w+1j*w*(alpha+beta*w2))))@Q
        recip=max(recip,float(np.linalg.norm(Y-Y.T)/max(np.linalg.norm(Y),1e-30)))
        # Scale torque ports by a common length for numerical power metric.
        scale=np.tile([1.,.02],len(indices))
        Z=Y*scale[:,None]*scale[None,:]
        H=(Z+Z.conj().T)/2
        minpass=min(minpass,float(np.linalg.eigvalsh(H)[0]/max(np.linalg.norm(H),1e-30)))
        ys.append(Y)
    assert recip<=1e-10 and minpass>=-1e-10
    return dict(static=static,Y=np.array(ys),reciprocity=recip,passivityMinRelative=minpass,lowestHz=float(np.sqrt(w2[0])/(2*np.pi)))
