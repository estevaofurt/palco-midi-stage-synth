"""Mass-normalized modal target for G3.02d preparation.
Lossless fixed ends only; exact constant-force update and reciprocal port.
"""
import numpy as np
from scipy.linalg import eigh
from wound_modes import mass_matrix,stiffness
def basis(r,N,cut,width):
    L=r['lengthM'];s=r['hammerPositionM'];T=r['tensionPerStringN'];EI=r['bendingNm2']
    if not 0<width<=2*min(s,L-s) or N<8 or cut<=0:raise ValueError('port domain')
    mu=r['linearDensityKgM'];core=r['coreMassPerM']
    if r['wrapLayers']:
        start,end=r['windingIntervalM'];extra=(mu-core)*L/(end-start);M=mass_matrix(L,core,extra,start,end,N)
    else:M=mu*np.eye(N)
    w2,U=eigh(np.diag(stiffness(L,EI,T,N)),M)
    assert np.all(w2>0)
    keep=np.sqrt(w2)/(2*np.pi)<=cut
    if not np.any(keep):raise ValueError('empty basis')
    n=np.arange(1,N+1);P=np.sqrt(2/L)*np.sin(n*np.pi*s/L)*np.sinc(n*width/(2*L))
    return w2[keep],U[:,keep].T@P
class Target:
    def __init__(self,w2,P,sr):
        self.w2=np.asarray(w2);self.P=np.asarray(P);self.w=np.sqrt(self.w2);h=1/sr
        self.c=np.cos(self.w*h);self.s=np.sin(self.w*h)
        self.G=2*np.sin(self.w*h/2)**2/self.w2;self.J=self.s/self.w
        self.q=np.zeros_like(self.w);self.v=np.zeros_like(self.w);self.H=float(self.P@(self.G*self.P))
    def energy(self):return .5*float(self.v@self.v+(self.w2*self.q)@self.q)
    def position(self):return float(self.P@self.q)
    def free(self):return float(self.P@(self.c*self.q+self.J*self.v))
    def step(self,F):
        old=self.position();q=self.q.copy()
        self.q=self.c*q+self.J*self.v+self.G*self.P*F
        self.v=-self.w*self.s*q+self.c*self.v+self.J*self.P*F
        return F*(self.position()-old)
