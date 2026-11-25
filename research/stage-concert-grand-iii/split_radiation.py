"""G3.06f: independently integrated resistive and reactive Rayleigh operators.
One-sided infinite baffle, harmonic frequency-domain only. No PSD clipping.
"""
import numpy as np
from numpy.polynomial.legendre import leggauss
from ribbed_plate import quadrature
from radiation_resistance import angular,surface,pressure
from radiation_impedance import audit

def relative(a,b):
    a=np.asarray(a);b=np.asarray(b)
    if a.shape!=b.shape:raise ValueError('comparison shape mismatch')
    return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-30))

def fan_batch(poly,field,freq,rho,c,outer,inner):
    """Integrate the weak-singular kernel at multiple frequencies in one geometry pass.
    Return unsymmetrized real and imaginary parts as independent numerical controls.
    """
    xy,w=quadrature(poly,outer);S=field(xy,poly)
    omega=2*np.pi*np.asarray(freq,dtype=float)
    if min(omega)<=0 or min(rho,c)<=0:raise ValueError('positive frequencies and medium')
    z,wt=leggauss(inner);t=(z+1)/2;wt=wt/2
    u,v=np.meshgrid(t,t,indexing='ij');W=(wt[:,None]*wt[None,:]).ravel()
    u=u.ravel();v=v.ravel();n=S.shape[1]
    raw=np.zeros((len(omega),n,n),complex)
    for x,weight,shape in zip(xy,w,S):
        q=np.zeros((len(omega),n),complex)
        for a,b in zip(poly,np.roll(poly,-1,axis=0)):
            A=a-x;B=b-x;det=A[0]*B[1]-A[1]*B[0]
            if det<=0:raise ValueError('strictly interior quadrature required')
            d=(1-v[:,None])*A+v[:,None]*B;L=np.linalg.norm(d,axis=1)
            y=x+u[:,None]*d
            kernel=np.exp(-1j*omega[:,None]*u*L/c)*(W*det/L)[None,:]
            q+=kernel@field(y,poly)
        raw+=weight*shape[None,:,None]*q[:,None,:]
    return xy,w,S,raw*(1j*rho*omega[:,None,None]/(2*np.pi))

def split_load(poly,field,freq,mic,outer,inner,angle,rho=1.204,c=343.):
    xy,w,S,raw=fan_batch(poly,field,freq,rho,c,outer,inner)
    out=[]
    for f,Q in zip(freq,raw):
        # Gram evaluation is the definition of the discrete resistive operator,
        # not projection of negative eigenvalues of the singular quadrature.
        R=angular(xy,w,S,f,rho,c,angle)
        R2=surface(xy,w,S,f,rho,c)
        X=(Q.imag+Q.imag.T)/2
        Z=R+1j*X
        obs=pressure(xy,w,S,mic,f,rho,c)
        a=audit(Q);b=audit(Z)
        report=dict(rawReciprocity=a['reciprocity'],rawMinPassivity=a['passivityMinRelative'],
          gramVsSurface=relative(R,R2),rawResistanceRelative=relative(Q.real,R),
          reactiveAsymmetry=relative(Q.imag,Q.imag.T),splitVsRaw=relative(Z,Q),
          reciprocity=b['reciprocity'],passivityMinRelative=b['passivityMinRelative'])
        # The original raw operator is still audited, including failed passivity.
        report['rawGate']=a['reciprocity']<=1e-3 and a['passivityMinRelative']>=-1e-8
        # The separate bilinear operators have their own explicit accuracy gates.
        report['gate']=report['gramVsSurface']<=1e-8 and report['rawResistanceRelative']<=.01 and report['reactiveAsymmetry']<=1e-3 and report['splitVsRaw']<=.01 and b['reciprocity']<=1e-8 and b['passivityMinRelative']>=-1e-8
        out.append((Z,obs,report))
    return out
