"""G3.06d: reciprocal midpoint coupling of structural modes to passive acoustic states.
The high-frequency inertance is assembled exactly once in the structural inertia.
No pressure feedback from receiver observations.
"""
import numpy as np
from scipy.linalg import cho_factor,cho_solve

class Coupled:
    def __init__(self,M,K,D,map_,load,sr):
        self.M=np.asarray(M);self.K=np.asarray(K);self.D=np.asarray(D);self.A=np.asarray(map_)
        self.load=load;self.h=1/sr;h=self.h
        n=len(M);assert self.A.shape==(load.n,n)
        self.tail=self.A.T@load.tail@self.A
        self.Meff=self.M+self.tail
        self.B=np.einsum('pi,jpk->jik',self.A,load.B)
        self.om2=load.omega[:,None]**2
        self.den=1+h*load.gamma+h*h*self.om2/4
        self.S=self.B*(h/(2*self.den[:,None,:]))
        H=2*self.Meff/h+self.D+h*self.K/2+np.einsum('jik,jlk->il',self.S,self.B)
        self.factor=cho_factor(H)
        self.q=np.zeros(n);self.v=np.zeros(n)
        self.x=np.zeros_like(load.x);self.a=np.zeros_like(load.v)
        self.lossStructure=0.;self.lossAir=0.
    def partition(self):
        return dict(structure=.5*float(self.v@self.M@self.v+self.q@self.K@self.q),
                    airInertance=.5*float(self.v@self.tail@self.v),
                    airOscillators=.5*float(np.sum(self.a**2+self.om2*self.x**2)))
    def energy(self):return sum(self.partition().values())
    def step(self,F):
        F=np.asarray(F,dtype=float);h=self.h
        free=(self.a-h*self.om2*self.x/2)/self.den
        rhs=2*self.Meff@self.v/h-self.K@self.q-np.einsum('jik,jk->i',self.B,free)+F
        vm=cho_solve(self.factor,rhs)
        am=free+np.einsum('jik,i->jk',self.S,vm)
        self.q+=h*vm;self.v=2*vm-self.v
        self.x+=h*am;self.a=2*am-self.a
        ds=h*float(vm@self.D@vm);da=2*self.load.gamma*h*float(np.sum(am**2))
        self.lossStructure+=ds;self.lossAir+=da
        assert min(ds,da)>=-1e-14
        return h*float(vm@F)

def mobility(M,K,D,A,Z,f):
    w=2*np.pi*f
    H=K-w*w*M+1j*w*(D+A.T@Z@A)
    X=np.linalg.solve(H,np.eye(len(M)));Y=1j*w*X
    # Separate structural and acoustic dissipative powers.
    hs=(Y+Y.conj().T)/2
    predicted=Y.conj().T@(D+A.T@((Z+Z.conj().T)/2)@A)@Y
    err=float(np.linalg.norm(hs-predicted)/max(np.linalg.norm(hs),1e-30))
    rec=float(np.linalg.norm(Y-Y.T)/max(np.linalg.norm(Y),1e-30))
    pas=float(min(np.linalg.eigvalsh(hs))/max(np.linalg.norm(hs),1e-30))
    return Y,dict(powerRelative=err,reciprocity=rec,passivityMinRelative=pas)
