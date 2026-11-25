"""G2.09g-A/B: original one-way Rayleigh observation, no mechanical feedback."""
import numpy as np
from scipy.special import roots_legendre
from scipy.signal import fftconvolve
RHO=1.204; C=343.
LISTENERS=np.array([[.70,.55,1.],[.45,.55,1.],[.95,.55,1.]])
def grid(L,W,nx,ny,gauss=False):
    if gauss:
        x,wx=roots_legendre(nx);y,wy=roots_legendre(ny)
        x=(x+1)*L/2;y=(y+1)*W/2
        area=(wx[:,None]*wy[None,:]*L*W/4).ravel()
    else:
        x=(np.arange(nx)+.5)*L/nx;y=(np.arange(ny)+.5)*W/ny
        area=np.full(nx*ny,L*W/(nx*ny))
    X,Y=np.meshgrid(x,y,indexing='ij')
    return X.ravel(),Y.ravel(),area
def shape_matrix(shapes,x,y,L,W):
    rows=[]
    for m in shapes:
        if m['id']=='uniform':s=np.ones_like(x)
        elif m['id']=='antisymmetric':s=np.sin(2*np.pi*x/L)*np.sin(np.pi*y/W)
        else:
            s=np.zeros_like(x)
            for a in m['components']:
                s+=a['coefficient']*np.sin(a['kx']*x)*np.sin(a['ky']*y)
        rows.append(s)
    return np.array(rows)
def geometry(x,y,area,listener):
    r=np.sqrt((x-listener[0])**2+(y-listener[1])**2+listener[2]**2)
    return r/C,RHO*area/(2*np.pi*r)
def response(shapes,delay,weight,f):
    return (shapes*weight)@np.exp(-2j*np.pi*delay[:,None]*np.asarray(f)[None,:])
def kernels(shapes,delay,weight,sr,method='cubic',mean_step=True):
    # mean step acceleration input indexed at its interval START: actual center +h/2.
    # Delay includes half-step, so output is at the physical output sample clock.
    d=delay*sr+(.5 if mean_step else 0.)
    i=np.floor(d).astype(int);u=d-i
    order=2 if method=='linear' else 4
    if method not in ('linear','cubic'):raise ValueError('method')
    taps=np.zeros((shapes.shape[0],int(i.max())+order))
    for j in range(order):
        a=np.ones_like(u)
        for k in range(order):
            if j!=k:a*=(u-k)/(j-k)
        for m,s in enumerate(shapes):
            taps[m]+=np.bincount(i+j,weights=s*weight*a,minlength=taps.shape[1])
    return taps
def kernel_response(taps,sr,f):
    return taps@np.exp(-2j*np.pi*np.arange(taps.shape[1])[:,None]*np.asarray(f)[None,:]/sr)
def pressure(acc,taps):
    # Acceleration [mode, interval], taps [mode, delay], output full tail in Pa.
    if acc.shape[0]!=taps.shape[0] or not np.all(np.isfinite(acc)):raise ValueError('acceleration')
    out=np.zeros(acc.shape[1]+taps.shape[1]-1)
    for a,k in zip(acc,taps):out+=fftconvolve(a,k,mode='full')
    # FFT roundoff can leak epsilon into mathematical zero region; exact causal mask.
    nz=np.flatnonzero(np.any(taps!=0,axis=0))
    if len(nz):out[:nz[0]]=0
    else:out.fill(0)
    return out
