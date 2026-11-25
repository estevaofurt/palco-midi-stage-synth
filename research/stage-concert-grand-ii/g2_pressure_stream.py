"""Offline streaming Rayleigh convolution, same kernels as g2_radiation.
Memory bounded by block size, modes and propagation tail, not duration.
"""
import numpy as np
from scipy.fft import rfft, irfft, next_fast_len

class PressureStream:
    def __init__(self,kernels,block_size=4096,mode_batch=32):
        ks=[np.asarray(k,dtype=np.float64) for k in kernels]
        if not ks or any(k.ndim!=2 or not k.size or not np.all(np.isfinite(k)) for k in ks):
            raise ValueError('finite nonempty mode-by-delay kernels')
        self.modes=ks[0].shape[0]
        if any(k.shape[0]!=self.modes for k in ks):
            raise ValueError('mode count')
        if not isinstance(block_size,int) or block_size<1 or not isinstance(mode_batch,int) or mode_batch<1:
            raise ValueError('block size or mode batch')
        self.block_size=block_size;self.mode_batch=mode_batch;self.channels=len(ks)
        self.tail=max(k.shape[1] for k in ks)-1
        self.fft_size=next_fast_len(block_size+self.tail)
        self.kernels=ks
        self.K=[rfft(k,n=self.fft_size,axis=1) for k in ks]
        self.first=[]
        for k in ks:
            nz=np.flatnonzero(np.any(k!=0,axis=0))
            self.first.append(int(nz[0]) if len(nz) else None)
        self.overlap=np.zeros((self.channels,self.tail))
        self.samples=0;self.finished=False
    def process(self,acc):
        if self.finished:raise ValueError('finished')
        a=np.asarray(acc,dtype=np.float64)
        if a.ndim!=2 or a.shape[0]!=self.modes or not 1<=a.shape[1]<=self.block_size or not np.all(np.isfinite(a)):
            raise ValueError('acceleration block')
        n=a.shape[1];size=n+self.tail
        spectra=np.zeros((self.channels,self.fft_size//2+1),dtype=np.complex128)
        for start in range(0,self.modes,self.mode_batch):
            sl=slice(start,min(start+self.mode_batch,self.modes))
            A=rfft(a[sl],n=self.fft_size,axis=1)
            for ch,K in enumerate(self.K):spectra[ch]+=np.sum(A*K[sl],axis=0)
        out=irfft(spectra,n=self.fft_size,axis=1)[:,:size].copy()
        # exact zeros for the portion before this block's first possible contribution
        for ch,first in enumerate(self.first):
            if first is None:out[ch].fill(0)
            else:out[ch,:first]=0
        out[:,:self.tail]+=self.overlap
        self.overlap=out[:,n:].copy()
        self.samples+=n
        return out[:,:n].copy()
    def finish(self):
        if self.finished or self.samples==0:raise ValueError('no active stream')
        self.finished=True
        return self.overlap.copy()

def render_blocks(acc,kernels,block_size=4096,mode_batch=32):
    """Convenience only; caller may instead write each process result to disk."""
    stream=PressureStream(kernels,block_size,mode_batch)
    a=np.asarray(acc)
    if a.ndim!=2 or a.shape[1]==0:raise ValueError('empty acceleration')
    blocks=[stream.process(a[:,i:i+block_size]) for i in range(0,a.shape[1],block_size)]
    return np.concatenate([*blocks,stream.finish()],axis=1)
