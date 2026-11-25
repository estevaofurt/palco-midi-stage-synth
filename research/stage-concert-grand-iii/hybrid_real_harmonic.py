"""Real-valued lossless harmonic prism interface functions.
Analytic continuation: for lambda < k², sech(i x)=sec(x),
a tanh(a h)=-beta tan(beta h), tanh(a h)/a=tan(beta h)/beta.
No damping, imaginary-part clipping, or pole shift.
"""
import numpy as np

def real_vertical(lam,h,omega,c):
    lam=np.asarray(lam)
    if lam.ndim!=1 or not len(lam) or np.iscomplexobj(lam) or not np.isfinite(lam).all() or min(lam)<0 or not all(np.isfinite(v) and v>0 for v in (h,omega,c)):
        raise ValueError('invalid lossless harmonic parameters')
    delta=lam-(omega/c)**2;beta=np.sqrt(abs(delta));x=beta*h
    ev=delta>=0;prop=~ev
    sech=np.empty_like(x);d=np.empty_like(x);ratio=np.empty_like(x)
    e=np.exp(-x[ev]);den=1+e*e
    sech[ev]=2*e/den;tanh=-np.expm1(-2*x[ev])/den
    d[ev]=beta[ev]*tanh
    cos=np.cos(x[prop])
    if np.any(2*abs(cos)<1e-10):raise ValueError('prism Dirichlet-top pole')
    sech[prop]=1/cos;d[prop]=-beta[prop]*np.tan(x[prop])
    small=x<1e-7
    ratio[small]=h*(1-delta[small]*h*h/3)
    nz=ev&~small;ratio[nz]=d[nz]/delta[nz]
    nz=prop&~small;ratio[nz]=d[nz]/delta[nz]
    return sech,d,ratio
