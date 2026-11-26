"""G3.13d: direct retarded Rayleigh impedance without rational fitting.
Cell-averaged spatial lag correlations -> finite delay kernel.
A discretized delay kernel is NOT automatically passive; screen explicitly."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.fft import rfft2,irfft2
from scipy.sparse import coo_matrix
from numpy.polynomial.legendre import leggauss
from wire_physical_midpoint import load
from structural_region_decay import rebuild
from structural_passive_fit import read_reference
from response_weighted_fit import read_group,score
from new_baffle_grid import DEVELOPMENT,RESERVED,EXTENSION,coordinate_audit
from wire_baffle_reference import FREQ
from polygon_radiation import SurfaceModes
from surface_reactive_fft import cell_integrals,average_kernel
from structural_passive_fit import contexts,structural_impedance,matrix_errors,worst
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

RHO=1.204;C=343.
def delay_matrix(n,dx,dy,rate,order):
    """For each nonnegative cell lag integrate triangular difference density.
    Duffy transform handles all zero-corner singular quadrants. Linear
    fractional-delay interpolation, nonnegative time bins, no fitted poles."""
    t,w=leggauss(order);t=(t+1)/2;w=w/2
    u,v=np.meshgrid(t,t,indexing='ij');u=u.ravel();v=v.ravel()
    wt=(w[:,None]*w[None,:]).ravel()
    i,j=np.indices((n,n));i=i.ravel();j=j.ravel()
    taps=int(np.ceil(rate/C*np.hypot(n*dx,n*dy)))+2
    rows=[];cols=[];vals=[]
    def deposit(ids,delay,weight):
        lo=np.floor(delay).astype(int);a=delay-lo
        if min(lo.ravel())<0 or max(lo.ravel())+1>=taps:raise ValueError('delay support')
        c=np.broadcast_to(ids[:,None],lo.shape)
        rows.extend([lo.ravel(),(lo+1).ravel()]);cols.extend([c.ravel(),c.ravel()])
        vals.extend([(weight*(1-a)).ravel(),(weight*a).ravel()])
    for sx in (-1,1):
        for sy in (-1,1):
            singular=(i<=1)&(j<=1)&((i==0)|(sx==-1))&((j==0)|(sy==-1))
            ids=np.flatnonzero(~singular)
            for start in range(0,len(ids),1024):
                a=ids[start:start+1024];radius=np.hypot(dx*(i[a,None]+sx*u),dy*(j[a,None]+sy*v))
                deposit(a,rate*radius/C,wt[None,:]*(1-u)*(1-v)/radius)
            for a in np.flatnonzero(singular):
                for x,y in ((u,u*v),(u*v,u)):
                    L=np.hypot(dx*x/u,dy*y/u)
                    tx=x if i[a]==0 else 1-x;ty=y if j[a]==0 else 1-y
                    deposit(np.array([a]),(rate*u*L/C)[None,:],(wt*(1-tx)*(1-ty)/L)[None,:])
    H=coo_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),shape=(taps,n*n)).tocsr()
    static=np.asarray(H.sum(axis=0)).reshape(n,n)
    err=relative(static,average_kernel(n,dx,dy,0.,order))
    if err>1e-12 or min(H.data)<0:raise ValueError('lag quadrature')
    return H,err

def fold(c,n):
    """Sum signed offsets into absolute lag cells without duplicating axes."""
    out=c[...,:n,:n].copy()
    out[...,1:,:]+=c[...,-1:-n:-1,:n]
    out[...,:,1:]+=c[...,:n,-1:-n:-1]
    out[...,1:,1:]+=c[...,-1:-n:-1,-1:-n:-1]
    return out

def kernel(B,dx,dy,rate,order=8):
    n,ny,p=B.shape
    if n!=ny or n<2:raise ValueError('cell grid')
    H,static=delay_matrix(n,dx,dy,rate,order)
    F=rfft2(B.transpose(2,0,1),s=(2*n,2*n),axes=(-2,-1))
    a,b=np.triu_indices(p);K=np.zeros((H.shape[0],p,p))
    for start in range(0,len(a),16):
        i,j=a[start:start+16],b[start:start+16]
        c=irfft2(F[i].conj()*F[j],s=(2*n,2*n),axes=(-2,-1))
        x=fold(c,n).reshape(len(i),-1)
        z=RHO/(2*np.pi)*(H@x.T)
        K[:,i,j]=z;K[:,j,i]=z
    return K,static

def impedance(K,f,rate,sigma=0.):
    s=sigma+2j*np.pi*np.atleast_1d(f)
    return np.einsum('ft,tij->fij',np.exp(-s[:,None]*np.arange(len(K))/rate),K)*s[:,None,None]

def passivity(K,rate):
    rows=[]
    for sigma in (0.,2*np.pi*10):
        for f in np.geomspace(10.,rate*.49,161):
            Z=impedance(K,[f],rate,sigma)[0];R=(Z+Z.conj().T)/2
            eig=np.linalg.eigvalsh(R);den=max(np.linalg.norm(R),1e-30)
            rows.append(dict(frequencyHz=float(f),sigma=float(sigma),minimumRelative=float(eig.min()/den)))
    band=[v for v in rows if 30<=v['frequencyHz']<=500]
    return dict(bandMinimum=min(v['minimumRelative'] for v in band),wideMinimum=min(v['minimumRelative'] for v in rows),
        bandSampleGate=all(v['minimumRelative']>=-1e-8 for v in band),
        wideSampleGate=all(v['minimumRelative']>=-1e-8 for v in rows),samples=rows)

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','surface','reference','grid','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();archive,wires,sha=load(a.source,a.scale);z,rh=read_reference(a.reference,sha)
    local={}
    def sink(plate,poly,lift):local.update(plate=plate,poly=poly,lift=lift)
    k,D,P,A,wires,G,lift,replay=rebuild(a.scale,a.surface,archive,wires,surface_sink=sink)
    ca=coordinate_audit(dict(stiffness=k,damping=D,ports=P,wirePorts=A,physicalLift=lift,regionalDamping=G),z)
    plate,poly=local['plate'],local['poly']
    field=SurfaceModes(plate,local['lift']@z['fieldVectors']/np.sqrt(z['fieldEigenvalues'])[None,:])
    ctx=contexts(z,wires,{x['key']:x for x in json.loads(a.scale.read_text())['rows']})
    datasets=[('previous',FREQ,z)]
    for role,f in [('development',DEVELOPMENT),('reserved',RESERVED),('extension',EXTENSION)]:
        data,dh=read_group(a.grid,role,f,sha,rh);datasets.append((role,f,data))
    cases=[];arrays={}
    for n in (60,120,240):
        B,dx,dy,area=cell_integrals(poly,field,n)
        if abs(area-plate['areaM2'])/plate['areaM2']>1e-9:raise ValueError('cell area')
        rate=48000;K,static=kernel(B,dx,dy,rate)
        arrays[f'kernel_{n}']=K
        # Map the field kernel into the actual mechanical coordinates.
        J=np.einsum('ai,tab,bj->tij',z['fieldMap'],K,z['fieldMap'])
        audit=passivity(J,rate);groups=[]
        for role,f,data in datasets:
            Z=impedance(K,f,rate);S=structural_impedance(Z,z['fieldMap'])
            er=matrix_errors(Z,data['impedance'])
            es=matrix_errors(S,structural_impedance(data['impedance'],z['fieldMap']))
            # response() requires PSD resistance; do not repair an indefinite kernel.
            # Numerical screening remains informative even when a response is skipped.
            minimum=min(float(np.linalg.eigvalsh((x+x.conj().T)/2).min()/max(np.linalg.norm(x.real),1e-30)) for x in S)
            responseRows=score(f,data,z,S,ctx) if minimum>=-1e-10 else []
            g=dict(role=role,fieldMaximum=worst(er),structuralMaximum=worst(es),minimumResistance=minimum,
                responseMaximum=max(v['maximumResponse'] for v in responseRows) if responseRows else None,
                responsePowerGate=bool(responseRows and all(v['powerGate'] for v in responseRows)))
            groups.append(g)
        row=dict(grid=n,rate=rate,taps=len(K),staticQuadratureRelative=static,groups=groups,passivity=audit)
        cases.append(row)
        print('G3_RETARDED_IMPEDANCE_CASE '+json.dumps({**row,'passivity':{k:v for k,v in audit.items() if k!='samples'}},allow_nan=False),flush=True)
    finest=cases[-1]
    primary=[v for v in finest['groups'] if v['role']!='extension']
    screen=all(v['fieldMaximum']<=.05 and v['structuralMaximum']<=.05 and v['responsePowerGate'] and v['responseMaximum']<=.05 for v in primary)
    summary=dict(gate=True,screeningFitGate=bool(screen),bandPassivitySampleGate=finest['passivity']['bandSampleGate'],
        widePassivitySampleGate=finest['passivity']['wideSampleGate'],diagnosticOnly=True,calibratedParameters=False,
        directGeometryDelay=True,rationalFitUsed=False,grids=[60,120,240],structureRank=80,fields=80,
        continuousPassivityProven=False,feedbackIntegrationApproved=False,physicalAcousticFitAccepted=False,
        timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    a.out.mkdir(parents=True,exist_ok=True)
    desc=save_matrices(a.out,'retarded_impedance',frequencies=FREQ,fieldMap=z['fieldMap'],**arrays)
    (a.out/'retarded_impedance.json').write_text(json.dumps(dict(summary=summary,cases=cases,archive=desc,
        coordinateReplay=ca,sourceFrozenSha256=sha,referenceManifestSha256=rh),indent=2,allow_nan=False))
    print('G3_RETARDED_IMPEDANCE_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
