"""G3.06c: passive finite spectral realization of acoustic impedance.
Z(s) = s*Mtail + sum B_j B_j^T s/(s^2+2 gamma s+Omega_j^2).
A diagnostic approximation of the radiation continuum, not a selected load.
"""
import numpy as np
from scipy.linalg import eigh
def factor_psd(A):
    A=np.asarray(A,dtype=float)
    if np.linalg.norm(A-A.T)>1e-10*max(np.linalg.norm(A),1e-30):raise ValueError('nonsymmetric weight')
    d,U=eigh((A+A.T)/2)
    if min(d)<-1e-10*max(max(abs(d)),1e-30):raise ValueError('nonpassive spectral weight')
    return U*np.sqrt(np.maximum(d,0.))
class Load:
    def __init__(self,omega,weights,gamma,tail):
        self.omega=np.asarray(omega,dtype=float);self.gamma=float(gamma)
        self.tail=np.asarray(tail,dtype=float)
        if min(self.omega)<=0 or gamma<=0:raise ValueError('positive poles and damping required')
        factor_psd(self.tail)
        self.B=np.array([factor_psd(a) for a in weights]);self.n=self.tail.shape[0]
        if self.B.shape!=(len(self.omega),self.n,self.n):raise ValueError('weight dimensions')
        self.x=np.zeros((len(self.omega),self.n));self.v=self.x.copy()
        self.u=np.zeros(self.n)
    def impedance(self,s):
        s=complex(s);d=s/(s*s+2*self.gamma*s+self.omega**2)
        return s*self.tail+np.einsum('j,jik,jlk->il',d,self.B,self.B)
    def storage(self):
        return .5*float(np.sum(self.v**2+(self.omega[:,None]*self.x)**2)+self.u@self.tail@self.u)
    def step(self,u,h):
        """Implicit midpoint of each oscillator, input velocity endpoints.
        Return mean opposing force (positive input work), work, nonnegative loss.
        Tail inertance is counted here; in a coupled model put it in mass ONCE.
        """
        u=np.asarray(u,dtype=float)
        if h<=0 or u.shape!=(self.n,):raise ValueError('step domain')
        mid=(u+self.u)/2
        drive=np.einsum('jik,i->jk',self.B,mid)
        om2=self.omega[:,None]**2
        vm=(self.v+.5*h*(drive-om2*self.x))/(1+h*self.gamma+.25*h*h*om2)
        f=np.einsum('jik,jk->i',self.B,vm)+self.tail@(u-self.u)/h
        loss=2*self.gamma*h*float(np.sum(vm**2));work=h*float(mid@f)
        self.x+=h*vm;self.v=2*vm-self.v;self.u=u.copy()
        return f,work,loss

def spectral(resistance,high_limit,fmax,df,gamma_hz):
    """Midpoint quadrature of (2/pi) integral R(Omega) s/(s^2+Omega^2)dOmega.
    Positive damping broadens each spectral atom; tail approximated by inertance.
    Must validate both bandwidth and damping/spacing, not a fitted free gain.
    """
    count=round(fmax/df)
    if count<1 or abs(count*df-fmax)>1e-9:raise ValueError('integer number of bins')
    freq=(np.arange(count)+.5)*df;omega=2*np.pi*freq
    W=np.array([resistance(f) for f in freq])*(4*df)
    tail=2/(np.pi*2*np.pi*fmax)*np.asarray(high_limit)
    return Load(omega,W,2*np.pi*gamma_hz,tail)
