"""Basis-specific Rayleigh observer, independent preparation for R3.
No material selection, mechanical feedback, or change to existing observer.
"""
import hashlib,json
import numpy as np
from g2_radiation import grid,geometry,kernels,pressure,LISTENERS,RHO,C
class BoardObserver:
    def __init__(self,modes,L=1.4,W=1.1,sr=96000,cut=6000):
        if not all(np.isfinite(z) and z>0 for z in (L,W,sr,cut)):raise ValueError('geometry/rate')
        self.L,self.W,self.sr=L,W,sr
        selected=[m for m in modes if m['f']<cut]
        if not selected:raise ValueError('empty basis')
        self.freqs=np.array([m['f'] for m in selected])
        assert np.all(np.isfinite(self.freqs)) and np.all(self.freqs>0)
        self.terms=sorted({(c['m'],c['n']) for m in selected for c in m['components']})
        ix={t:i for i,t in enumerate(self.terms)}
        self.U=np.zeros((len(selected),len(self.terms)))
        for i,m in enumerate(selected):
            seen=set()
            for c in m['components']:
                t=(c['m'],c['n']);assert t not in seen and min(t)>0;seen.add(t)
                assert np.isclose(c['kx'],t[0]*np.pi/L,rtol=1e-12,atol=1e-12)
                assert np.isclose(c['ky'],t[1]*np.pi/W,rtol=1e-12,atol=1e-12)
                self.U[i,ix[t]]=c['coefficient']
        assert np.isfinite(self.U).all()
        self.basis_sha=hashlib.sha256(json.dumps(dict(L=L,W=W,sr=sr,cut=cut,modes=[dict(f=m['f'],components=m['components']) for m in selected]),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    def validate(self,acc,basis_sha):
        if basis_sha!=self.basis_sha:raise ValueError('acoustic basis mismatch')
        a=np.asarray(acc)
        if a.ndim!=2 or a.shape[0]!=len(self.freqs) or a.shape[1]<2 or not np.isfinite(a).all():raise ValueError('acceleration')
        return a
    def make_kernels(self,nx,ny):
        x,y,area=grid(self.L,self.W,nx,ny)
        S=np.array([np.sin(m*np.pi*x/self.L)*np.sin(n*np.pi*y/self.W) for m,n in self.terms])
        out=[]
        for loc in LISTENERS:
            d,w=geometry(x,y,area,loc)
            out.append(self.U@kernels(S,d,w,self.sr,'linear'))
        return out
    def render(self,acc,basis_sha,nx=128,ny=96):
        a=self.validate(acc,basis_sha)
        channels=[pressure(a,k) for k in self.make_kernels(nx,ny)]
        n=max(map(len,channels))
        return np.stack([np.pad(p,(0,n-len(p))) for p in channels])
    def energy(self,acc,basis_sha,nt,np_,limit=8000):
        a=self.validate(acc,basis_sha);n=a.shape[1];N=1<<(2*n-1).bit_length()
        u=np.arange(n)/(n-1);taper=np.where(u<=.75,1,.5*(1+np.cos(np.pi*(u-.75)/.25)))
        A=self.U.T@np.fft.rfft(a*taper,n=N,axis=1)
        mu=(np.arange(nt)+.5)/nt;az=2*np.pi*(np.arange(np_)+.5)/np_
        radial=np.sqrt(1-mu**2)[:,None];dx=(radial*np.cos(az)[None,:]).ravel();dy=(radial*np.sin(az)[None,:]).ravel()
        mm,mi=np.unique([t[0] for t in self.terms],return_inverse=True);nn,ni=np.unique([t[1] for t in self.terms],return_inverse=True)
        def J(z,l):return l*np.exp(.5j*z*l)*np.sinc(z*l/(2*np.pi))
        def sine(m,l,z):
            b=m*np.pi/l;return (J(z+b,l)-J(z-b,l))/(2j)
        total=0.
        for i in range(min(int(limit*N/self.sr),N//2-1)+1):
            k=2*np.pi*i*self.sr/(N*C)
            X=sine(mm[:,None],self.L,k*dx[None,:]);Y=sine(nn[:,None],self.W,k*dy[None,:])
            z=A[:,i]@(X[mi]*Y[ni]);total+=float(np.sum(abs(z)**2))*(.5 if i==0 else 1.)
        return total*(2/(N*self.sr))*RHO/(4*np.pi**2*C)*(2*np.pi/(nt*np_))
