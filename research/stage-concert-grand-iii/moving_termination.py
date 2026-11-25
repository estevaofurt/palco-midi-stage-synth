"""G3.03a: a vertical string with an explicit moving rear boundary.
Analytical Ritz mass integrals, fixed front, simply supported rotation at both ends.
Rear load is a diagnostic passive one-port, NOT a piano bridge.
"""
import math
import numpy as np
from scipy.linalg import eigh
from wound_modes import mass_matrix,stiffness

def matrices(r,N,mass,stiff,width=.005):
    L=r['lengthM'];T=r['tensionPerStringN'];EI=r['bendingNm2'];s=r['hammerPositionM']
    if not (N>=8 and mass>0 and stiff>=0 and 0<width<=2*min(s,L-s)):raise ValueError('boundary domain')
    mu=r['linearDensityKgM'];core=r['coreMassPerM'];n=np.arange(1,N+1,dtype=float)
    # y(x)=b*x/L+sum q_n sqrt(2/L)sin(n*pi*x/L). b has units m.
    # Mass includes moving shape and cross inertia (not independent extra string).
    if r['wrapLayers']:
        a,z=r['windingIntervalM'];extra=(mu-core)*L/(z-a)
        M0=mass_matrix(L,core,extra,a,z,N)
        pieces=[(0.,L,core),(a,z,extra)]
    else:
        M0=mu*np.eye(N);pieces=[(0.,L,mu)]
    k=n*np.pi/L
    def primitive(x):return (-x*np.cos(k*x)/k+np.sin(k*x)/k**2)*math.sqrt(2/L)/L
    cross=sum(d*(primitive(z)-primitive(a)) for a,z,d in pieces)
    mshape=sum(d*(z**3-a**3)/(3*L**2) for a,z,d in pieces)
    M=np.zeros((N+1,N+1));M[0,0]=mass+mshape;M[0,1:]=cross;M[1:,0]=cross;M[1:,1:]=M0
    K=np.diag(np.r_[stiff+T/L,stiffness(L,EI,T,N)])
    P=np.zeros((N+1,2));P[0,0]=s/L;P[1:,0]=math.sqrt(2/L)*np.sin(k*s)*np.sinc(n*width/(2*L));P[0,1]=1.
    # Column0 hammer average displacement, column1 rear translation.
    return M,K,P

def basis(r,N,cut,mass,stiff,width=.005):
    M,K,P=matrices(r,N,mass,stiff,width)
    w2,U=eigh(K,M)
    assert np.all(w2>0)
    mask=np.sqrt(w2)/(2*np.pi)<=cut
    if not np.any(mask):raise ValueError('empty basis')
    return w2[mask],U[:,mask].T@P

class Boundary:
    """Exact undamped modal update plus implicit passive rear-port damping."""
    def __init__(self,w2,P,sr,damp):
        if sr<=0 or damp<0:raise ValueError('integrator domain')
        self.w2=np.asarray(w2);self.P=np.asarray(P);self.h=1/sr;self.damp=damp
        w=np.sqrt(self.w2);h=self.h;self.w=w;self.c=np.cos(w*h);self.s=np.sin(w*h)
        self.G=2*np.sin(w*h/2)**2/self.w2;self.J=self.s/w
        self.q=np.zeros_like(w);self.v=np.zeros_like(w);self.loss=0.
        self.p=self.P[:,1];self.H=(self.P.T*self.G)@self.P
        self.den=1+damp*self.H[1,1]/h
        assert np.max(abs(self.H-self.H.T))<1e-12 and self.den>=1
    def energy(self):return .5*float(self.v@self.v+(self.w2*self.q)@self.q)
    def position(self):return self.P.T@self.q
    def velocity(self):return self.P.T@self.v
    def step(self,external):
        F=np.asarray(external,dtype=float);q=self.q.copy()
        free=(self.c-1)*q+self.J*self.v
        d0=free+self.G*(self.P@F)
        drag=self.damp/self.h*float(self.p@d0)/self.den
        applied=self.P@F-self.p*drag
        delta=free+self.G*applied
        self.q=q+delta;self.v=-self.w*self.s*q+self.c*self.v+self.J*applied
        dp=self.P.T@delta;loss=drag*float(dp[1]);self.loss+=loss
        assert loss>=-1e-15
        return dict(work=float(F@dp),loss=loss,dragN=drag,damperResidualN=abs(drag-self.damp*float(dp[1])/self.h))
