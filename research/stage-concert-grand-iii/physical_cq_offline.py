"""G3.14d.13: gated offline physical CQ generation, 48 kHz only.
No real-time or engine acceptance. Never reuse a failed rank projection."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.fft import rfft2
from wire_physical_midpoint import load
from structural_region_decay import rebuild
from fixed_acoustic_projection import RANK,TRAIN,CHECK,NOVEL,freeze_projection,eligible
from acoustic_matrix_archive import read_npz
from retarded_local_reference import geometry
from acoustic_port_rank import reference,assess,summarize
from projected_board_cq import bridge_ports
from unison_profiles import KEYS,profiles_for_key,detune_profile
from mode_selective_loss import mode_loss
from modal_string_radiation import response
from polygon_radiation import SurfaceModes
from surface_reactive_fft import cell_integrals
from retarded_load import folded_correlation
from retarded_surface import delay_kernel,RHO
from acoustic_cq_pilot import symbol,harmonic_symbol
from acoustic_cq_surface import passivity
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

class PackedLoad:
    def __init__(self,B,dx,dy):
        self.n=B.shape[0];self.m=B.shape[2];self.dx=dx;self.dy=dy
        self.i,self.j=np.triu_indices(self.m)
        F=rfft2(B,s=(2*self.n,2*self.n),axes=(0,1)).transpose(2,0,1).copy()
        self.corr=np.empty((self.n**2,len(self.i)))
        for k,(i,j) in enumerate(zip(self.i,self.j)):self.corr[:,k]=folded_correlation(F[i],F[j],self.n)
    def evaluate(self,ss,order=8):
        ss=np.asarray(ss,complex);rows=[]
        for start in range(0,len(ss),16):
            S=ss[start:start+16]
            K=np.stack([delay_kernel(self.n,self.dx,self.dy,s,order).ravel() for s in S])
            Z=(K.real@self.corr+1j*(K.imag@self.corr))*((RHO/(2*np.pi))*S[:,None])
            rows.append(Z)
        return np.concatenate(rows)
    def expand(self,W):
        out=np.empty((*W.shape[:-1],self.m,self.m),dtype=W.dtype)
        out[...,self.i,self.j]=W;out[...,self.j,self.i]=W
        return out

def packed_weights(L,rate,n):
    radius=np.exp(-8/n);z=radius*np.exp(-2j*np.pi*np.arange(n//2+1)/n)
    half=L.evaluate(symbol(z,rate));full=np.concatenate([half,half[1:-1][::-1].conj()])
    W=np.fft.ifft(full,axis=0)/radius**np.arange(n)[:,None]
    imag=float(np.linalg.norm(W.imag)/max(np.linalg.norm(W.real),1e-30))
    if imag>1e-8:raise ValueError('complex weights')
    return W.real,imag

def transfer(W,f,rate):
    z=np.exp(-2j*np.pi*np.asarray(f)/rate)
    H=z[:,None]**np.arange(len(W))
    return H.real@W+1j*(H.imag@W)

def approved(root,sha):
    raw=(root/'frozen_acoustic_projection.json').read_bytes();d=json.loads(raw)
    s=json.loads((root/'fixed_acoustic_projection.json').read_text())['summary']
    if s['sourceFrozenSha256']!=sha or d['sourceFrozenSha256']!=sha or s['frozenSha256']!=hashlib.sha256(raw).hexdigest():raise ValueError('projection provenance')
    if d['rank']!=RANK or d['method']!='impedance' or s['rank']!=RANK:raise ValueError('projection scope')
    return d,s

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','source','surface','projection','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--audition',action='store_true')
    p.add_argument('--long-prior',type=Path)
    p.add_argument('--long-speed',type=float,choices=(.3,3.))
    a=p.parse_args();archive,wires,sha=load(a.source,a.scale);d,s=approved(a.projection,sha)
    a.out.mkdir(parents=True,exist_ok=True)
    if s['screeningGate'] is not True:
        report=dict(gate=True,screeningGate=False,blockedBy='rank64 harmonic screening',weightsGenerated=False,physicalFeedbackAccepted=False)
        (a.out/'physical_cq.json').write_text(json.dumps(report));print('G3_PHYSICAL_CQ_GATE '+json.dumps(report),flush=True);return
    z=read_npz(a.projection,d['archive'],dict(projection=(80,64),stiffness=(80,),damping=(80,80),ports=(80,7),
        wirePorts=(10,80),physicalLift=(1386,80),regionalDamping=(3,80,80),fieldMap=(80,80),
        trainingImpedance=(5,80,80),trainingPressure=(5,2,80)),list(TRAIN))
    local={}
    def sink(plate,poly,lift):local.update(plate=plate,poly=poly,lift=lift)
    k,D,P,A,wires,G,lift,replay=rebuild(a.scale,a.surface,archive,wires,surface_sink=sink)
    if [w.id for w in wires]!=d['wireIds']:raise ValueError('wire identity')
    # Archived matrices were integrity-checked, not imported into this basis.
    # Recreate the exact frozen selection rule and revalidate all three groups.
    # In particular, do not compare or copy individual eigenvector columns.
    del z
    geom=geometry(local['plate'],local['poly'],local['lift'])
    B=bridge_ports(A,wires);rows={v['key']:v for v in json.loads(a.scale.read_text())['rows']}
    ctx=[]
    for key in KEYS:
        ww,_=detune_profile(wires,rows,profiles_for_key(key)[0][1]);ctx.append(mode_loss(ww,4.,2. if key==64 else 4.))
    train=[reference(f,k,D,P,A,B,ctx,geom) for f in TRAIN]
    U=freeze_projection(np.stack([v['Z'] for v in train]))
    # Save the local basis before checking any other frequencies.
    entry=save_matrices(a.out,'local_cq_projection',frequencies=list(TRAIN),projection=U,
        stiffness=k,damping=D,ports=P,wirePorts=A,physicalLift=lift,regionalDamping=G,fieldMap=geom[0])
    localFrozen=dict(rank=RANK,method='impedance',archive=entry,trainingHz=TRAIN,sourceFrozenSha256=sha,
        priorProjectionFrozenSha256=s['frozenSha256'],wireIds=[w.id for w in wires])
    raw=json.dumps(localFrozen,indent=2,allow_nan=False).encode()
    (a.out/'local_cq_projection.json').write_bytes(raw)
    localHash=hashlib.sha256(raw).hexdigest()
    refs={f:v for f,v in zip(TRAIN,train)};checks={}
    for name,group in [('training',TRAIN),('priorCheck',CHECK),('additionalCheck',NOVEL)]:
        for f in group:
            if f not in refs:refs[f]=reference(f,k,D,P,A,B,ctx,geom)
        checks[name]=summarize([assess(refs[f],U,k,D,P,A,B,ctx) for f in group])
        print('G3_PHYSICAL_CQ_LOCAL_PROJECTION '+json.dumps(dict(group=name,**checks[name]),allow_nan=False),flush=True)
    # Both the independently archived and local projections must pass the
    # unchanged screening limits; matching their coordinates is not required.
    if not all(eligible(v) for v in checks.values()):
        report=dict(gate=True,screeningGate=False,blockedBy='local rank64 harmonic screening',weightsGenerated=False,
            localProjection=checks,localProjectionFrozenSha256=localHash,physicalFeedbackAccepted=False)
        (a.out/'physical_cq.json').write_text(json.dumps(dict(summary=report),indent=2));print('G3_PHYSICAL_CQ_GATE '+json.dumps(report),flush=True);return
    field=SurfaceModes(local['plate'],local['lift']@U)
    cells,dx,dy,area=cell_integrals(local['poly'],field,120)
    if abs(area-local['plate']['areaM2'])/local['plate']['areaM2']>1e-9:raise ValueError('area')
    L=PackedLoad(cells,dx,dy)
    rate=48000;n=1024
    W,e=packed_weights(L,rate,n);W2,e2=packed_weights(L,rate,2*n)
    alias=relative(W,W2[:n]);tail=float(np.linalg.norm(W2[n:])/max(np.linalg.norm(W2),1e-30))
    fs=np.unique(np.r_[0.,TRAIN,CHECK,NOVEL,np.geomspace(1.,rate/2,160),np.linspace(0.,rate/2,257)])
    direct=L.expand(L.evaluate(harmonic_symbol(fs,rate)));rec=L.expand(transfer(W,fs,rate))
    dp=passivity(direct);rp=passivity(rec)
    err=max(relative(x,y) for x,y in zip(rec[1:],direct[1:]))
    # Reuse the locally validated references, never archived coordinate columns.
    freqs=np.array([*TRAIN,*CHECK,*NOVEL]);wet=L.expand(transfer(W,freqs,rate));reports=[]
    md=dict(M=np.eye(80),K=np.diag(k),D=D,P=P)
    sampled=bool(min(dp['minimumLocalNonDC'],rp['minimumLocalNonDC'])>=-1e-8)
    if sampled:
        for f,Z in zip(freqs,wet):
            ref=refs[float(f)]
            target=U.T@ref['Z']@U;actual=U@Z@U.T
            cases=[]
            for j,ww in enumerate(ctx):
                yy,oo,audit=response(md,A,ww,actual,ref['H'],f)
                yr,orr,_=ref['notes'][j]
                cases.append(dict(key=KEYS[j],mobility=relative(yy[:,j],yr),pressure=relative(oo[:,j],orr),powerGate=bool(audit['gate'])))
            reports.append(dict(frequencyHz=float(f),projectedMatrixRelative=relative(Z,target),
                maximumResponse=max(max(v['mobility'],v['pressure']) for v in cases),cases=cases))
    passed=bool(sampled and max(alias,tail,err,e,e2)<=1e-5 and max(dp['dcRelative'],rp['dcRelative'])<=1e-8
        and len(reports)==len(freqs) and all(v['projectedMatrixRelative']<=.05 and v['maximumResponse']<=.05 and all(c['powerGate'] for c in v['cases']) for v in reports))
    entry=save_matrices(a.out,'physical_cq_weights',frequencies=freqs,weights=L.expand(W),projection=U,
        stiffness=k,damping=D,ports=P,wirePorts=A,physicalLift=lift)
    summary=dict(gate=True,screeningGate=passed,diagnosticOnly=True,rate=rate,rank=RANK,weightsGenerated=True,
        sourceFrozenSha256=sha,projectionFrozenSha256=s['frozenSha256'],archive=entry,localProjection=checks,localProjectionFrozenSha256=localHash,independentCoordinatesMixed=False,
        aliasRelative=alias,tailRelative=tail,reconstructionRelative=err,directPassivity=dp,kernelPassivity=rp,
        responseCases=len(reports),maximumResponse=max((v['maximumResponse'] for v in reports),default=None),
        passivityCertified=False,physicalFeedbackAccepted=False,audibleSustainMeasured=False,wholeEngineRealtimeValidated=False)
    (a.out/'physical_cq.json').write_text(json.dumps(dict(summary=summary,reports=reports),indent=2,allow_nan=False))
    print('G3_PHYSICAL_CQ_GATE '+json.dumps(summary,allow_nan=False),flush=True)
    if a.audition and passed:
        from physical_acoustic_audition import audition
        audition(a.out/'audition',k,D,A,wires,rows,U,L.expand(W),geom,rate,refs,sha,localHash)
    if a.long_prior is not None and passed:
        if a.long_speed is None:raise ValueError('missing long speed')
        from physical_acoustic_long import same_basis_long
        same_basis_long(a.out/'long',a.long_prior,k,D,A,wires,rows,U,L.expand(W),geom,rate,refs,sha,localHash,a.out,a.long_speed)
if __name__=='__main__':main()
