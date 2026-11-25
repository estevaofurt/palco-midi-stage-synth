"""G3.06e energy-scaled structural modes and radiation projection.
Frequency-domain proof on actual candidate polygon modes; no causal fit or strings.
"""
import numpy as np
from scipy.linalg import cholesky,eigh,solve_triangular
from scipy.interpolate import BSpline
from structural_response import congruence
from radiation_impedance import impedance,audit
from radiation_resistance import surface,pressure
from ribbed_plate import quadrature

def modes(M,K,D,P,count,shiftHz=100.):
    # Shift-invert symmetric pencil: largest eigenvalues correspond to lowest modes.
    # Avoid subtracting tiny eigenvalues from a huge stiffness spectrum.
    shift=(2*np.pi*shiftHz)**2
    scale=1/np.sqrt(np.diag(M));W=scale[:,None]*scale[None,:]
    m=M*W;k=(K*W);d=D*W
    L=cholesky((k+k.T)/2+shift*(m+m.T)/2,lower=True)
    E=congruence(L,m)
    n=len(m);assert 0<count<=n
    ev,V=eigh(E,subset_by_index=[n-count,n-1]);ev=ev[::-1];V=V[:,::-1]
    assert min(ev)>0
    w2=1/ev-shift;assert min(w2)>0
    U=solve_triangular(L.T,V,lower=False)/np.sqrt(ev)
    massError=float(np.linalg.norm(U.T@m@U-np.eye(count))/np.sqrt(count))
    # Audit residual in the energy-scaled coordinates, plus original norm for transparency.
    scaled=float(np.linalg.norm(E@V-V*ev)/max(np.linalg.norm(V*ev),1e-30))
    # Independent original-coordinate residual is reported, not hidden by projection.
    original=float(np.linalg.norm(k@U-(m@U)*w2)/max(np.linalg.norm((m@U)*w2),1e-30))
    Dm=U.T@d@U;Dm=(Dm+Dm.T)/2
    assert min(np.linalg.eigvalsh(Dm))>=-1e-9*max(np.linalg.norm(Dm),1.)
    return dict(U=scale[:,None]*U,M=np.eye(count),K=np.diag(w2),D=Dm,P=U.T@(scale[:,None]*P),
                Hz=np.sqrt(w2)/(2*np.pi),massError=massError,scaledEigenResidual=scaled,originalEigenResidual=original)

class SurfaceModes:
    """Evaluate the unrestricted tensor splines using only 16 locally active products."""
    def __init__(self,model,U):
        b=model['basis'];assert not b.essential
        self.b=b;self.coeff=(model['T']@U).reshape(b.naxis,b.naxis,U.shape[1])
    def __call__(self,xy,poly=None):
        b=self.b;p=np.clip(np.atleast_2d(xy),b.low,b.high)
        x=BSpline.design_matrix(p[:,0],b.spl[0][0].t,3,extrapolate=False)
        y=BSpline.design_matrix(p[:,1],b.spl[1][0].t,3,extrapolate=False)
        assert np.all(np.diff(x.indptr)==4) and np.all(np.diff(y.indptr)==4)
        ix=x.indices.reshape(-1,4);iy=y.indices.reshape(-1,4)
        vx=x.data.reshape(-1,4);vy=y.data.reshape(-1,4)
        return np.einsum('pi,pj,pijk->pk',vx,vy,self.coeff[ix[:,:,None],iy[:,None,:]])

def response(modal,Z,observer,f):
    w=2*np.pi*f;M=modal['M'];K=modal['K'];D=modal['D'];P=modal['P']
    # Reference integral may have a small discretization asymmetry. It is audited
    # before this function. No symmetrization of computed mobility.
    X=np.linalg.solve(K-w*w*M+1j*w*(D+Z),P);V=1j*w*X
    Y=P.T@V;H=(Y+Y.conj().T)/2
    hs=(Z+Z.conj().T)/2
    structural=V.conj().T@D@V;air=V.conj().T@hs@V
    err=float(np.linalg.norm(H-structural-air)/max(np.linalg.norm(H),1e-30))
    return Y,observer@V,dict(powerRelative=err,reciprocity=float(np.linalg.norm(Y-Y.T)/max(np.linalg.norm(Y),1e-30)),
       passivityMinRelative=float(min(np.linalg.eigvalsh(H))/max(np.linalg.norm(H),1e-30)),
       airPowerFraction=float(np.trace(air).real/max(np.trace(H).real,1e-30)))

def load(poly,field,f,mic,outer,inner,rho=1.204,c=343.):
    raw=impedance(poly,field,2j*np.pi*f,rho,c,outer,inner)
    report=audit(raw)
    xy,w=quadrature(poly,outer);S=field(xy)
    R=surface(xy,w,S,f,rho,c)
    report['resistanceRelative']=float(np.linalg.norm(raw.real-R)/max(np.linalg.norm(R),1e-30))
    obs=pressure(xy,w,S,mic,f,rho,c)
    # Use the independently PSD real resistance and symmetric reactive quadrature.
    # Differences from the raw integral are explicitly measured and gated.
    Z=(R+R.T)/2+1j*(raw.imag+raw.imag.T)/2
    report['projectionRelative']=float(np.linalg.norm(Z-raw)/max(np.linalg.norm(raw),1e-30))
    return Z,obs,report
