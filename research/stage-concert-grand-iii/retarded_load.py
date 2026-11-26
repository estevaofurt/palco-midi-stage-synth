"""G3.14c: geometry-derived retarded Rayleigh load kernel.
No fitted poles. Linear causal delay bins with exact singularity quadrature.
A sampled passivity audit is necessary, NOT a certificate for feedback.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.fft import rfft2,irfft2
from scipy.sparse import coo_matrix
from numpy.polynomial.legendre import leggauss
from wire_physical_midpoint import load
from structural_region_decay import rebuild
from structural_passive_fit import read_reference,structural_impedance,contexts
from new_baffle_grid import DEVELOPMENT,RESERVED,EXTENSION,coordinate_audit
from wire_baffle_reference import FREQ
from response_weighted_fit import read_group,score
from polygon_radiation import SurfaceModes
from surface_reactive_fft import cell_integrals
from dual_cavity_spatial_diagnostic import save_matrices
from split_radiation import relative
from retarded_coordinates import align

RHO=1.204
C=343.

def delay_table(n,dx,dy,rate,order=8):
    """Each column: average 1/r with linear delay deposition for one offset."""
    if n<1 or min(dx,dy,rate,order)<=0:raise ValueError('geometry')
    z,w=leggauss(order);t=(z+1)/2;w=w/2
    u,v=np.meshgrid(t,t,indexing='ij');u=u.ravel();v=v.ravel()
    wt=(w[:,None]*w[None,:]).ravel()
    i,j=np.meshgrid(np.arange(n),np.arange(n),indexing='ij');i=i.ravel();j=j.ravel()
    taps=int(np.ceil(rate*np.hypot(n*dx,n*dy)/C))+1
    # Each block is small; convert local dense bins to sparse before assembly.
    rr=[];cc=[];vv=[]
    def deposit(ids,distance,weight):
        delay=rate*distance/C;k=np.floor(delay).astype(int);p=delay-k
        if np.any(k<0) or np.any(k+1>=taps):raise ValueError('delay support')
        local=np.zeros((len(ids),taps));ix=np.broadcast_to(np.arange(len(ids))[:,None],k.shape)
        np.add.at(local,(ix,k),weight*(1-p));np.add.at(local,(ix,k+1),weight*p)
        a,b=np.nonzero(local);rr.append(b);cc.append(ids[a]);vv.append(local[a,b])
    for sx in (-1,1):
        for sy in (-1,1):
            singular=(i<=1)&(j<=1)&((i==0)|(sx==-1))&((j==0)|(sy==-1))
            ids=np.flatnonzero(~singular)
            for start in range(0,len(ids),512):
                a=ids[start:start+512]
                distance=np.hypot(dx*(i[a,None]+sx*u),dy*(j[a,None]+sy*v))
                deposit(a,distance,wt*(1-u)*(1-v)/distance)
            for a in np.flatnonzero(singular):
                for x,y in ((u,u*v),(u*v,u)):
                    length=np.hypot(dx*(x/u),dy*(y/u))
                    tx=x if i[a]==0 else 1-x;ty=y if j[a]==0 else 1-y
                    deposit(np.array([a]),(u*length)[None,:],(wt*(1-tx)*(1-ty)/length)[None,:])
    out=coo_matrix((np.concatenate(vv),(np.concatenate(rr),np.concatenate(cc))),shape=(taps,n*n)).tocsr()
    if not np.isfinite(out.data).all() or min(out.data)<=0:raise ValueError('invalid delay weights')
    return out

def folded_correlation(F,G,n):
    corr=irfft2(F.conj()*G,s=(2*n,2*n))
    # Each nonzero offset has both signs; zero appears only once.
    ids=np.arange(n);neg=(-ids)% (2*n)
    a=corr[np.ix_(ids,ids)].copy()
    a[1:,:]+=corr[np.ix_(neg[1:],ids)]
    a[:,1:]+=corr[np.ix_(ids,neg[1:])]
    a[1:,1:]+=corr[np.ix_(neg[1:],neg[1:])]
    return a.ravel()

def build(B,dx,dy,rates):
    n,m=B.shape[0],B.shape[2]
    if B.shape!=(n,n,m) or not np.isfinite(B).all():raise ValueError('cells')
    tables=[delay_table(n,dx,dy,r) for r in rates]
    kernels=[np.zeros((t.shape[0],m,m)) for t in tables]
    F=rfft2(B,s=(2*n,2*n),axes=(0,1)).transpose(2,0,1).copy()
    for i in range(m):
        for j in range(i,m):
            a=folded_correlation(F[i],F[j],n)
            for table,K in zip(tables,kernels):
                x=RHO/(2*np.pi)*(table@a)
                K[:,i,j]=x;K[:,j,i]=x
    return kernels

def transfer(K,f,rate,discrete=False):
    f=np.atleast_1d(np.asarray(f,float));z=np.exp(-2j*np.pi*f/rate)
    H=np.einsum('ft,tij->fij',z[:,None]**np.arange(len(K)),K)
    s=(3-4*z+z*z)*rate/2 if discrete else 2j*np.pi*f
    return s[:,None,None]*H

def sampled_passivity(K,rate):
    # Include the full discrete band, not just the piano range.
    fs=np.unique(np.r_[np.geomspace(1.,rate/2,160),np.linspace(0.,rate/2,257)])
    worst=0.;at=0.
    for f in fs:
        Z=transfer(K,[f],rate,True)[0]
        R=(Z+Z.conj().T)/2
        e=float(np.linalg.eigvalsh(R).min()/max(np.linalg.norm(Z),1e-30))
        if e<worst:worst=e;at=float(f)
    return dict(minimumRelative=worst,frequencyHz=at,samples=len(fs),
        sampledGate=bool(worst>=-1e-10),certified=False)

def errors(actual,expected):
    return dict(impedance=relative(actual,expected),resistance=relative(actual.real,expected.real),
                reactance=relative(actual.imag,expected.imag))

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','reference','grid','surface','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();archive,wires,sha=load(a.source,a.scale);z,rh=read_reference(a.reference,sha)
    local={}
    def sink(plate,poly,lift):local.update(plate=plate,poly=poly,lift=lift)
    k,D,P,A,wires,G,lift,_=rebuild(a.scale,a.surface,archive,wires,surface_sink=sink)
    Q,ca=align(dict(stiffness=k,damping=D,ports=P,wirePorts=A,physicalLift=lift,regionalDamping=G),z)
    field=SurfaceModes(local['plate'],local['lift']@Q.T)
    groups=[('original',FREQ,z)];hashes={}
    for role,fs in [('development',DEVELOPMENT),('reserved',RESERVED),('extension',EXTENSION)]:
        d,h=read_group(a.grid,role,fs,sha,rh);groups.append((role,fs,d));hashes[role]=h
    ctx=contexts(z,wires,{v['key']:v for v in json.loads(a.scale.read_text())['rows']})
    rates=(48000,96000);cases=[];matrices={}
    for n in (60,120):
        B,dx,dy,area=cell_integrals(local['poly'],field,n)
        if abs(area-local['plate']['areaM2'])/local['plate']['areaM2']>1e-9:raise ValueError('cell area')
        for rate,K in zip(rates,build(B,dx,dy,rates)):
            pa=sampled_passivity(K,rate);rows=[]
            for role,fs,d in groups:
                expected=structural_impedance(d['impedance'],z['fieldMap'])
                Z=transfer(K,fs,rate);Zd=transfer(K,fs,rate,True)
                for f,x,y,ref in zip(fs,Z,Zd,expected):
                    rows.append(dict(role=role,frequencyHz=f,continuousDerivative=errors(x,ref),
                        discreteDerivative=errors(y,ref)))
            # Existing score() requires passive input. Report response only
            # if the actual sampled resistance passes its stricter test.
            responseRows=[]
            for role,fs,d in groups:
                Z=transfer(K,fs,rate,True)
                passive=all(np.linalg.eigvalsh(x.real).min()>=-1e-10*max(np.linalg.norm(x.real),1e-30) for x in Z)
                if passive:
                    responseRows.extend(dict(role=role,**v) for v in score(fs,d,z,Z,ctx))
            band=max(max(v['discreteDerivative'].values()) for v in rows if v['role']!='extension')
            responseMax=max((v['maximumResponse'] for v in responseRows if v['role']!='extension'),default=None)
            row=dict(grid=n,rate=rate,taps=len(K),passivity=pa,matrixMaximum=band,
                responseMaximum=responseMax,responseCoverage=len(responseRows),frequencies=rows,responses=responseRows,
                screeningGate=bool(pa['sampledGate'] and len(responseRows)==26 and band<=.05 and responseMax is not None and responseMax<=.05))
            cases.append(row);matrices[f'kernel_{n}_{rate}']=K
            print('G3_RETARDED_LOAD_CASE '+json.dumps({k:v for k,v in row.items() if k not in ('frequencies','responses')},allow_nan=False),flush=True)
    a.out.mkdir(parents=True,exist_ok=True)
    entry=save_matrices(a.out,'retarded_load_kernels',frequencies=sorted(FREQ+DEVELOPMENT+RESERVED+EXTENSION),**matrices)
    summary=dict(gate=True,diagnosticOnly=True,screeningPassed=sum(v['screeningGate'] for v in cases),
        configurations=len(cases),geometryDerived=True,causalDelayKernel=True,physicalAcousticFitAccepted=False,
        feedbackIntegrated=False,passivityCertified=False,continuousFrequencyValidated=False,timeDomainReady=False,
        sourceFrozenSha256=sha,referenceManifestSha256=rh,gridManifestSha256=hashes,coordinateReplay=ca)
    (a.out/'retarded_load.json').write_text(json.dumps(dict(summary=summary,cases=cases,archive=entry),indent=2,allow_nan=False))
    print('G3_RETARDED_LOAD_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
