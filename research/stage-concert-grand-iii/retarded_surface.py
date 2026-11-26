"""G3.14c: retarded Rayleigh surface impedance from physical travel times.
Continuous Laplace-domain cell quadrature, not a discrete feedback engine.
One-sided ideal baffle; no fitted poles or sound output."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.fft import fft2,ifft2
from surface_reactive_fft import cell_integrals,average_kernel
from structural_region_decay import rebuild
from structural_passive_fit import read_reference
from new_baffle_grid import coordinate_audit
from wire_baffle_reference import FREQ
from polygon_radiation import SurfaceModes
from enriched_baffle import samples,resistance
from wire_physical_midpoint import load
from radiation_resistance import pressure
from modal_string_radiation import response
from unison_profiles import KEYS,profiles_for_key,detune_profile
from mode_selective_loss import mode_loss
from split_radiation import relative
from retarded_local_reference import geometry
from structural_passive_fit import contexts as original_contexts
from surface_reactive_fft import reactive
from dual_cavity_spatial_diagnostic import save_matrices

RHO=1.204
C=343.
FREQUENCIES=[110.,130.81,150.,261.63,329.63,400.]

def delay_kernel(n,dx,dy,s,order=8):
    """Average exp(-s*r/c)/r over cell pairs. Duffy integration handles
    touching/self cells without a fabricated minimum distance."""
    if n<1 or min(dx,dy)<=0 or s.real<0 or not np.isfinite(s):raise ValueError('domain')
    z,w=leggauss(order);t=(z+1)/2;w=w/2
    u,v=np.meshgrid(t,t,indexing='ij');u=u.ravel();v=v.ravel()
    wt=(w[:,None]*w[None,:]).ravel()
    i,j=np.meshgrid(np.arange(n),np.arange(n),indexing='ij');i=i.ravel();j=j.ravel()
    K=np.zeros(n*n,complex)
    for sx in (-1,1):
        for sy in (-1,1):
            singular=(i<=1)&(j<=1)&((i==0)|(sx==-1))&((j==0)|(sy==-1))
            ids=np.flatnonzero(~singular)
            for start in range(0,len(ids),2048):
                a=ids[start:start+2048]
                R=np.hypot(dx*(i[a,None]+sx*u),dy*(j[a,None]+sy*v))
                K[a]+=np.sum(np.exp(-s*R/C)/R*(wt*(1-u)*(1-v))[None,:],axis=1)
            for a in np.flatnonzero(singular):
                value=0j
                for x,y in ((u,u*v),(u*v,u)):
                    L=np.hypot(dx*x/u,dy*y/u)
                    tx=x if i[a]==0 else 1-x;ty=y if j[a]==0 else 1-y
                    value+=np.sum(wt*(1-tx)*(1-ty)*np.exp(-s*u*L/C)/L)
                K[a]+=value
    return K.reshape(n,n)

def impedance(B,dx,dy,s,order=8):
    n,m=B.shape[0],B.shape[2]
    if B.shape!=(n,n,m) or not np.isfinite(B).all():raise ValueError('cells')
    K=delay_kernel(n,dx,dy,s,order)
    idx=np.minimum(np.arange(2*n),2*n-np.arange(2*n));valid=idx<n;J=np.minimum(idx,n-1)
    pad=K[np.ix_(J,J)]*(valid[:,None]&valid[None,:])
    H=fft2(pad);flat=B.reshape(-1,m);Z=np.empty((m,m),complex)
    for i in range(0,m,8):
        V=fft2(B[:,:,i:i+8],s=(2*n,2*n),axes=(0,1))
        conv=ifft2(V*H[:,:,None],axes=(0,1))[:n,:n]
        Z[:,i:i+8]=flat.T@conv.reshape(n*n,-1)
    return RHO*s/(2*np.pi)*Z

def audit(Z):
    asym=relative(Z,Z.T);R=(Z+Z.conj().T)/2
    mineig=float(np.linalg.eigvalsh(R).min()/max(np.linalg.norm(R),1e-30))
    return dict(reciprocity=asym,positiveRealMin=mineig,gate=bool(asym<=1e-9 and mineig>=-1e-8))

def errors(a,b):
    return dict(complex=relative(a,b),resistance=relative(a.real,b.real),reactance=relative(a.imag,b.imag))

def main():
    p=argparse.ArgumentParser()
    for name in ('scale','source','surface','reference','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();archive,wires,sha=load(a.source,a.scale);z,rh=read_reference(a.reference,sha)
    local={}
    def sink(plate,poly,lift):local.update(plate=plate,poly=poly,lift=lift)
    k,D,P,A,wires,G,lift,replay=rebuild(a.scale,a.surface,archive,wires,surface_sink=sink)
    plate,poly=local['plate'],local['poly']
    B,field,quad,grids,mic,ca=geometry(plate,poly,local['lift'])
    xy,w,S=quad[3:]
    rows={v['key']:v for v in json.loads(a.scale.read_text())['rows']}
    contexts=[]
    for key in KEYS:
        ww,_=detune_profile(wires,rows,profiles_for_key(key)[0][1]);ww=mode_loss(ww,4.,2. if key==64 else 4.)
        contexts.append(ww)
    md=dict(M=np.eye(80),K=np.diag(k),D=D,P=P)
    oldctx=original_contexts(dict(stiffness=k,damping=D,ports=P),wires,rows)
    records=[];matrices=[];reference=[]
    for f in FREQUENCIES:
        s=2j*np.pi*f;Z0=impedance(*grids[120],s);Z=impedance(*grids[240],s)
        Z12=impedance(*grids[240],s,12)
        R,_=resistance(xy,w,S,f,16);H=pressure(xy,w,S,mic,f,RHO,C)
        # Independent angular resistance; established cell reactance at archived points.
        row=dict(frequencyHz=f,grid=errors(Z0,Z),quadrature=errors(Z12,Z),
            angularResistanceRelative=relative(Z.real,R),passivity=audit(Z))
        X=reactive(*grids[240],f,8)
        row['independentReactanceRelative']=relative(Z.imag,X)
        if f in FREQ:
            i=FREQ.index(f);row['externalReplay']=[]
            for j,(m,ww) in enumerate(oldctx):
                yy,pp,aa=response(m,A,ww,B.T@(R+1j*X)@B,H@B,f)
                row['externalReplay'].append(dict(mobility=relative(yy,z['mobility'][j,i]),pressure=relative(pp,z['observation'][j,i]),gate=aa['gate']))
        # Compare both formulations with identical mechanics, observer and reactance.
        target=R+1j*X;cases=[]
        for j,ww in enumerate(contexts):
            yy,pp,aa=response(md,A,ww,B.T@Z@B,H@B,f)
            yr,pr,ar=response(md,A,ww,B.T@target@B,H@B,f)
            cases.append(dict(key=KEYS[j],mobility=relative(yy[:,j],yr[:,j]),pressure=relative(pp[:,j],pr[:,j]),
                              powerGate=bool(aa['gate'] and ar['gate'])))
        row['cases']=cases
        row['gate']=bool(max(row['grid'].values())<=.01 and max(row['quadrature'].values())<=1e-5
            and row['angularResistanceRelative']<=.01 and row['passivity']['gate']
            and all(v['powerGate'] and max(v['mobility'],v['pressure'])<=.05 for v in cases)
            and row['independentReactanceRelative']<=1e-8
            and all(v['gate'] and max(v['mobility'],v['pressure'])<=.05 for v in row.get('externalReplay',[])))
        records.append(row);matrices.append(Z);reference.append(target)
        print('G3_RETARDED_SURFACE_CASE '+json.dumps(row,allow_nan=False),flush=True)
    positive=[]
    for f in (0.,150.,329.63):
        for sigma in (20.,200.):
            s=2*np.pi*(sigma+1j*f);row=dict(frequencyHz=f,realHz=sigma,**audit(impedance(*grids[240],s)))
            positive.append(row);print('G3_RETARDED_SURFACE_POSITIVE '+json.dumps(row,allow_nan=False),flush=True)
    summary=dict(gate=all(v['gate'] for v in records+positive),diagnosticOnly=True,
        idealBaffleOnly=True,physicalTravelTime=True,rationalFitUsed=False,frequencyPoints=len(records),
        positiveRealSamples=len(positive),continuousPassivityProven=False,discreteFeedbackAccepted=False,
        timeDomainReady=False,polyphonyValidated=False,sourceFrozenSha256=sha,referenceManifestSha256=rh,
        localGeometryAudit=ca,independentCoordinatesMixed=False,maximumGridError=max(max(v['grid'].values()) for v in records),
        maximumAngularResistanceError=max(v['angularResistanceRelative'] for v in records))
    a.out.mkdir(parents=True,exist_ok=True)
    entry=save_matrices(a.out,'retarded_surface_impedance',frequencies=FREQUENCIES,impedance=np.stack(matrices),reference=np.stack(reference))
    (a.out/'retarded_surface.json').write_text(json.dumps(dict(summary=summary,frequenciesHz=FREQUENCIES,cases=records,positiveReal=positive,archive=entry),indent=2,allow_nan=False))
    print('G3_RETARDED_SURFACE_GATE '+json.dumps(summary,allow_nan=False),flush=True)
    if not summary['gate']:raise ValueError('retarded cell convergence or passivity gate failed')
if __name__=='__main__':main()
