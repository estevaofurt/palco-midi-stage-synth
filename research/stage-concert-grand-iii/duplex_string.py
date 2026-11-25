"""Rear duplex and independently budgeted intrinsic loss proof.
Solid string only, front and hitch fixed, shared translating rear bridge port.
No front duplex, actual bridge, radiation or selected material loss coefficients.
"""
import numpy as np
from scipy.linalg import eigh
from moving_termination import matrices,Boundary
def assemble(r,N,load,ratio):
    if r['wrapLayers'] or N<8 or not 0<=ratio<=1:raise ValueError('solid duplex domain')
    size=1+N*(1+int(ratio>0));M=np.zeros((size,size));K=np.zeros_like(M);P=np.zeros((size,2))
    M[0,0]=load['massKg'];K[0,0]=load['stiffnessNm'];P[0,1]=1.
    parts=[]
    for j,rr in enumerate([r]+([dict(r,lengthM=r['lengthM']*ratio,hammerPositionM=r['lengthM']*ratio/2)] if ratio else [])):
        # Auxiliary coordinate is measured from the fixed hitch toward the common bridge.
        A,B,C=matrices(rr,N,load['massKg'],0.,width=.005 if j==0 else min(.005,rr['lengthM']/2))
        A[0,0]-=load['massKg']
        ids=np.r_[0,np.arange(1+j*N,1+(j+1)*N)]
        M[np.ix_(ids,ids)]+=A;K[np.ix_(ids,ids)]+=B
        if j==0:P[ids,0]=C[:,0]
        parts.append((ids,A,B))
    return M,K,P,parts
class Decay:
    """Exact velocity-only subflow in mass-normalized coordinates for PSD damping."""
    def __init__(self,D,h):
        D=(D+D.T)/2;d,V=eigh(D)
        if min(d)<-1e-9*max(1.,max(abs(d))):raise ValueError('nonpassive D')
        self.V=V;self.factor=np.exp(-np.maximum(d,0)*h);self.zero=not np.any(d>0)
    def step(self,v):
        if self.zero:return v,0.
        z=self.V.T@v;new=self.V@(self.factor*z)
        loss=.5*float(np.sum((1-self.factor**2)*z*z))
        assert loss>=0
        return new,loss
class Duplex:
    def __init__(self,r,N,cut,sr,load,ratio,loss):
        M,K,P,self.parts=assemble(r,N,load,ratio);w2,U=eigh(K,M)
        assert np.all(w2>0)
        keep=np.sqrt(w2)/(2*np.pi)<=cut;self.U=U[:,keep]
        self.b=Boundary(w2[keep],self.U.T@P,sr,load['dampingNsm']);self.load=load
        self.lossMain=0.;self.lossDuplex=0.;self.decays=[]
        for j,(ids,A,B) in enumerate(self.parts):
            # Main: D=2 sigma0 M_s + 2 sigma2 K_s, not a global acoustic decay fit.
            # Duplex: independent distributed viscous loss, no rear drag duplication.
            W=self.U[ids,:]
            D=2*(loss['mainSigma0PerS']*A+loss['mainSigma2S']*B) if j==0 else 2*loss['duplexSigmaPerS']*A
            self.decays.append(Decay(W.T@D@W,.5/sr))
    def position(self):return self.b.position()
    def energy(self):return self.b.energy()
    @property
    def loss(self):return self.b.loss+self.lossMain+self.lossDuplex
    def decay(self,j):
        self.b.v,L=self.decays[j].step(self.b.v)
        if j==0:self.lossMain+=L
        else:self.lossDuplex+=L
    def step(self,F):
        for j in range(len(self.decays)):self.decay(j)
        out=self.b.step(F)
        for j in reversed(range(len(self.decays))):self.decay(j)
        return out['work']
    def partition(self):
        x=self.U@self.b.q;v=self.U@self.b.v
        E=[.5*float(v[i]@A@v[i]+x[i]@B@x[i]) for i,A,B in self.parts]
        load=.5*(self.load['massKg']*v[0]**2+self.load['stiffnessNm']*x[0]**2)
        assert min(E)>=-1e-15 and abs(sum(E)+load-self.energy())<max(1e-12,self.energy()*1e-7)
        return dict(mainJ=E[0],duplexJ=E[1] if len(E)>1 else 0.,loadJ=float(load))
