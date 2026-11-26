"""Physical surface CQ screening in four bridge-excitation directions.
Not an 80-mode engine; no hammer, WAV or feedback integration."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.fft import rfft2
from wire_physical_midpoint import load
from structural_region_decay import rebuild
from polygon_radiation import SurfaceModes
from surface_reactive_fft import cell_integrals
from retarded_surface import delay_kernel,impedance,RHO
from retarded_load import folded_correlation
from acoustic_cq_pilot import symbol,harmonic_symbol,transfer,convolve
from enriched_baffle import samples,resistance
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

def directions(A,wires):
    P=np.column_stack([np.mean([a for a,w in zip(A,wires) if w.port==j],axis=0) for j in range(4)])
    U,s,V=np.linalg.svd(P,full_matrices=False)
    if s[-1]<=1e-8*s[0]:raise ValueError('bridge direction rank')
    return U

class ProjectedLoad:
    def __init__(self,B,dx,dy):
        self.n=B.shape[0];self.m=B.shape[2];self.dx=dx;self.dy=dy
        n=self.n;m=self.m
        F=rfft2(B,s=(2*n,2*n),axes=(0,1)).transpose(2,0,1)
        self.corr=np.empty((n*n,m,m))
        for i in range(m):
            for j in range(i,m):
                a=folded_correlation(F[i],F[j],n)
                self.corr[:,i,j]=a;self.corr[:,j,i]=a
        self.corr=self.corr.reshape(n*n,m*m)
    def __call__(self,s):
        K=delay_kernel(self.n,self.dx,self.dy,s,8)
        return RHO*s/(2*np.pi)*(K.ravel()@self.corr).reshape(self.m,self.m)

def cq(load,rate,n):
    radius=np.exp(-8/n)
    z=radius*np.exp(-2j*np.pi*np.arange(n//2+1)/n)
    half=np.stack([load(s) for s in symbol(z,rate)])
    vals=np.concatenate([half,half[1:-1][::-1].conj()])
    w=np.fft.ifft(vals,axis=0)/radius**np.arange(n)[:,None,None]
    err=float(np.linalg.norm(w.imag)/max(np.linalg.norm(w.real),1e-30))
    if err>1e-8 or not np.isfinite(w).all():raise ValueError('CQ reconstruction')
    return w.real,err

def passivity(Z):
    # Two scales: local impedance and absolute band maximum. The DC
    # sample is reported separately, never divide by numerical DC residue.
    norms=np.linalg.norm(Z,axis=(1,2));scale=max(norms.max(),1e-30)
    ev=np.array([np.linalg.eigvalsh((v+v.conj().T)/2).min() for v in Z])
    return dict(minimumGlobal=float(ev.min()/scale),
        minimumLocalNonDC=float(np.min(ev[1:]/np.maximum(norms[1:],scale*1e-12))),
        dcRelative=float(norms[0]/scale))

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','surface','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--rate',type=int,choices=(48000,96000),required=True);a=p.parse_args()
    archive,wires,sha=load(a.source,a.scale);local={}
    def sink(plate,poly,lift):local.update(plate=plate,poly=poly,lift=lift)
    k,D,P,A,wires,G,lift,replay=rebuild(a.scale,a.surface,archive,wires,surface_sink=sink)
    U=directions(A,wires);plate=local['plate'];poly=local['poly']
    field=SurfaceModes(plate,local['lift']@U)
    xy,w,S=samples(plate,field,8)
    grids={}
    for n in (60,120):
        B,dx,dy,area=cell_integrals(poly,field,n)
        if abs(area-plate['areaM2'])/plate['areaM2']>1e-9:raise ValueError('area')
        grids[n]=(B,dx,dy)
    L=ProjectedLoad(*grids[60]);fine=ProjectedLoad(*grids[120])
    f=np.array([30.,110.,130.81,150.,261.63,329.63,400.,500.])
    ref=np.stack([fine(2j*np.pi*x) for x in f]);coarse=np.stack([L(2j*np.pi*x) for x in f])
    # Independent angular resistance and original FFT impedance at same coordinates.
    angular=[relative(z.real,resistance(xy,w,S,float(ff),16)[0]) for z,ff in zip(ref,f)]
    algebra=relative(L(2j*np.pi*150),impedance(*grids[60],2j*np.pi*150))
    if algebra>1e-10:raise ValueError('correlation algebra')
    grid=max(relative(x,y) for x,y in zip(coarse,ref))
    # Long enough to include nominal geometric travel time, then double.
    n=1024 if a.rate==48000 else 2048
    W,e=cq(L,a.rate,n);W2,e2=cq(L,a.rate,2*n)
    fs=np.unique(np.r_[0.,f,np.geomspace(1.,a.rate/2,200),np.linspace(0,a.rate/2,257)])
    direct=np.stack([L(s) for s in harmonic_symbol(fs,a.rate)])
    recon=transfer(W,fs,a.rate)
    dp=passivity(direct);rp=passivity(recon)
    alias=relative(W,W2[:n]);tail=float(np.linalg.norm(W2[n:])/max(np.linalg.norm(W2),1e-30))
    reconstruction=max(relative(x,y) for x,y in zip(recon[1:],direct[1:]))
    low=transfer(W,f,a.rate)
    band=max(relative(x,y) for x,y in zip(low,ref))
    rng=np.random.default_rng(112);v=rng.normal(size=(2*n,4));v[n:]=0
    work=np.cumsum(np.sum(v*convolve(W,v),axis=1)/a.rate)
    minWork=float(min(0.,work.min())/max(np.max(abs(work)),1e-30))
    gate=bool(max(grid,max(angular),band)<=.05 and max(alias,tail,reconstruction,e,e2)<=1e-5
        and max(dp['dcRelative'],rp['dcRelative'])<=1e-8
        and min(dp['minimumLocalNonDC'],rp['minimumLocalNonDC'],minWork)>=-1e-8)
    summary=dict(gate=True,screeningGate=gate,diagnosticOnly=True,rate=a.rate,contourSamples=n,
        physicalSurfaceHypothesis=True,projectedDirections=4,fullStructureValidated=False,
        passivityCertified=False,feedbackIntegrated=False,audibleSustainMeasured=False,
        sourceFrozenSha256=sha,gridMaximum=grid,angularMaximum=max(angular),correlationAlgebra=algebra,
        aliasRelative=alias,tailRelative=tail,reconstructionRelative=reconstruction,bandMaximum=band,
        directPassivity=dp,kernelPassivity=rp,minimumWorkRelative=minWork)
    # Keep physical coordinates from this exact reconstruction.
    from projected_board_cq import screen
    coupled=screen(k,D,A,wires,U,W,a.rate,local) if gate else None
    if coupled is not None:
        print('G3_CQ_BOARD_GATE '+json.dumps({key:value for key,value in coupled.items() if key not in ('harmonic','cases')},allow_nan=False),flush=True)
    a.out.mkdir(parents=True,exist_ok=True)
    entry=save_matrices(a.out,'cq_projected_surface',frequencies=f,projection=U,weights=W,reference=ref)
    (a.out/'cq_projected_surface.json').write_text(json.dumps(dict(summary=summary,archive=entry,boardScreen=coupled),indent=2,allow_nan=False))
    print('G3_CQ_PROJECTED_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
