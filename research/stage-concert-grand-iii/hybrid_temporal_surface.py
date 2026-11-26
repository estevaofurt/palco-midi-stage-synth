"""G3.12a: replay accepted dry hybrid model and screen a surface basis.
Surface coordinates are new; old four-field acoustic operators are incompatible.
This is dry structural validation only."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import cholesky,solve_triangular,eigh,solve
from dry_hybrid_reduction import grids,response_columns,hybrid_basis
from dry_snapshot_reduction import normalized,read,errors
from dry_structural_modal import mobility
from dry_damping_midpoint import proof,timing
from acoustic_matrix_archive import read_npz
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from bridge_strings import centerline
from spline_plate import assemble
from structural_assembly import assemble as structure
from polygon_radiation import SurfaceModes
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

def require_source(root):
    frozenraw=(root/'frozen_hybrid.json').read_bytes();f=json.loads(frozenraw)
    d=json.loads((root/'dry_hybrid_reduction.json').read_text());s=d['summary']
    expected=dict(gate=True,reductionGate=True,diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,
        selectedRank=72,lowModes=64,extraModes=8,fullCoordinates=1386,selectionUsedOuter=False,
        fullDampingPreserved=True,acousticFitAccepted=False,timeDomainReady=False,radiationReady=False)
    if any(s.get(k)!=v for k,v in expected.items()) or hashlib.sha256(frozenraw).hexdigest()!=d['frozenSha256']:
        raise ValueError('unapproved hybrid provenance')
    if max(s[k] for k in ('trainingMaximum','innerMaximum','outerMaximum'))>.05:raise ValueError('invalid reduction gate')
    train=np.asarray(f['trainingHz']);inner=np.asarray(f['innerHz']);outer=np.asarray(f['plannedOuterHz'])
    for x,y in zip((train,inner,outer),grids()):
        if x.shape!=y.shape or not np.allclose(x,y,rtol=1e-14,atol=0):raise ValueError('grid mismatch')
    sel=f['selected']
    if (sel['rank'],sel['lowModes'],sel['extraModes'])!=(72,64,8):raise ValueError('selection mismatch')
    data=read_npz(root,f['archive'],dict(stiffness=(72,),damping=(72,72),ports=(72,4)),train)
    return f,data,hashlib.sha256(frozenraw).hexdigest()

def harmonic_discrete(k,D,P,freq,rate):
    # Implicit midpoint transfer for collocated midpoint velocity.
    # Bilinear substitution is exact for the discrete linear recurrence.
    warped=rate/np.pi*np.tan(np.pi*np.asarray(freq)/rate)
    Y=mobility(k,D,P,freq);Z=mobility(k,D,P,warped)
    return errors(Z,Y)

def surface_gram(basis,field,order,n):
    H=np.zeros((n,n));area=0.
    for xy,w,_ in basis.patches(order):
        S=field(xy);H+=S.T@(w[:,None]*S);area+=float(w.sum())
    return (H+H.T)/2,area

def surface_basis(H):
    H=np.asarray(H,float)
    if H.ndim!=2 or H.shape[0]!=H.shape[1] or not np.isfinite(H).all() or relative(H,H.T)>1e-12:raise ValueError('invalid surface Gram')
    ev,W=eigh((H+H.T)/2);ev=ev[::-1];W=W[:,::-1]
    if ev[0]<=0 or ev[-1]<-1e-10*ev[0]:raise ValueError('indefinite surface Gram')
    keep=ev>ev[0]*1e-12
    return ev[keep],W[:,keep]

def response_states(k,D,P,freq):
    rows=[]
    for f in freq:
        w=2*np.pi*f
        rows.append(1j*w*solve(np.diag(k-w*w)+1j*w*D,P))
    return np.stack(rows)

def residuals(H,ev,W,X,n):
    total=np.einsum('fip,ij,fjp->fp',X.conj(),H,X).real
    # Orthogonal spatial projection energy; residual from omitted coordinates,
    # plus any eigenvalues discarded by the numerical rank threshold.
    C=np.einsum('ij,fjp->fip',W.T,X)
    retained=np.sum(ev[:n][None,:,None]*abs(C[:,:n])**2,axis=1)
    err=np.sqrt(np.maximum(total-retained,0.)/np.maximum(total,1e-30))
    return dict(maximum=float(np.max(err)),aggregate=float(np.sqrt(np.maximum(total-retained,0.).sum()/max(total.sum(),1e-30))))

def reconstruct(scale,frozen):
    raw=scale.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=frozen['scaleSha256']:raise ValueError('scale mismatch')
    sc=json.loads(raw);l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json')
    c=contour_build(l,read('board_contour_hypothesis.json'),mat);rib=read('ribbed_plate_hypothesis.json')['rib']
    poly=np.asarray(c['contourXY_m']);centers={s:centerline(l['bridgeAttachmentNodes'][s]) for s in ('bass','treble')}
    plate=assemble(poly,c['ribs'],mat['plate'],rib,30,14,False)
    z=structure(plate,centers,read('bridge_hypothesis.json'),mat,read('rim_structure_hypothesis.json'),2,8,14,True)
    M=z['M'];K=z['K']+z['Jrim']+z['Jbridge'];D=z['D'];P=z['P'][:,[0,2,4,5]]
    m,k,d,p=normalized(M,K,D,P);train=np.asarray(frozen['trainingHz'])
    S=response_columns(m,k,d,p,train);T,_,_=hybrid_basis(m,k,S,64);T=T[:,:72]
    mr=T.T@m@T;kr=T.T@k@T
    w,U=eigh((kr+kr.T)/2,(mr+mr.T)/2)
    V=T@U;Dr=V.T@d@V;Dr=(Dr+Dr.T)/2;Pr=V.T@p
    s=1/np.sqrt(np.diag(M));L=cholesky((K+(2*np.pi*100)**2*M)*(s[:,None]*s[None,:]),lower=True)
    physical=s[:,None]*solve_triangular(L.T,V,lower=False)
    mass=relative(physical.T@M@physical,np.eye(72))
    if mass>1e-7:raise ValueError('physical lift mass mismatch')
    field=SurfaceModes(plate,physical[:z['plateDofs']])
    return w,Dr,Pr,plate,field,physical,mass

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();f,archive,sha=require_source(a.source);a.out.mkdir(parents=True,exist_ok=True)
    k,D,P=(archive[x] for x in ('stiffness','damping','ports'))
    train=np.asarray(f['trainingHz']);inner=np.asarray(f['innerHz'])
    # New interstitial grid, not the G3.11z outer grid.
    base=np.geomspace(30,500,32);valid=base[:-1]**.125*base[1:]**.875
    tests=[proof(k,D,P,r,72) for r in (48000,96000)]
    bench=[timing(k,D,P,r,72) for r in (48000,96000)]
    harmonic=[dict(sampleRate=r,**harmonic_discrete(k,D,P,valid,r)) for r in (48000,96000)]
    w,Dr,Pr,plate,field,physical,mass=reconstruct(a.scale,f)
    replay=errors(mobility(w,Dr,Pr,train),mobility(k,D,P,train))['maximum']
    if replay>1e-6:raise ValueError('hybrid lift replay mismatch')
    H0,area0=surface_gram(plate['basis'],field,8,72);H,area=surface_gram(plate['basis'],field,12,72)
    gram_error=relative(H0,H);area_error=max(abs(area0-plate['areaM2']),abs(area-plate['areaM2']))/plate['areaM2']
    if gram_error>1e-8 or area_error>1e-10:raise ValueError('surface quadrature failed')
    ev,W=surface_basis(H);X=response_states(w,Dr,Pr,np.sort(np.r_[train,inner]))
    rows=[]
    for n in sorted(set(min(v,len(ev)) for v in (4,8,16,24,32,48,64,72))):
        rows.append(dict(fields=n,training=residuals(H,ev,W,X,n)))
    eligible=[v for v in rows if v['training']['maximum']<=.05]
    selected=min(eligible,key=lambda x:x['fields']) if eligible else rows[-1]
    n=selected['fields'];A=np.sqrt(ev[:n])[:,None]*W[:,:n].T
    # Phi(x) = S(x) W / sqrt(ev), A maps physical modal velocity to
    # orthonormal field velocity. Export the consistent lifted coordinates.
    entry=save_matrices(a.out,'hybrid_surface',frequencies=train,stiffness=w,damping=Dr,ports=Pr,
        physicalLift=physical,gram=H,fieldVectors=W[:,:n],fieldEigenvalues=ev[:n],fieldMap=A)
    frozen=dict(selected=selected,archive=entry,sourceFrozenSha256=sha,scaleSha256=f['scaleSha256'],
        trainingHz=train.tolist(),innerHz=inner.tolist(),plannedValidationHz=valid.tolist())
    raw=json.dumps(frozen,indent=2,allow_nan=False).encode();(a.out/'frozen_surface.json').write_bytes(raw)
    validation=residuals(H,ev,W,response_states(w,Dr,Pr,valid),n)
    gate=all(v['gate'] for v in tests+bench)
    summary=dict(gate=gate,diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,rank=72,
        surfaceFields=n,surfaceNumericalRank=len(ev),surfaceTrainingMaximum=selected['training']['maximum'],surfaceValidationMaximum=validation['maximum'],
        surfaceGate=bool(max(selected['training']['maximum'],validation['maximum'])<=.05),
        sourceReplayRelative=replay,physicalMassRelative=mass,surfaceQuadratureRelative=gram_error,areaRelative=area_error,
        maximumEnergyError=max(v['energyRelative'] for v in tests+bench),maximumStateError=max(v['stateRelative'] for v in tests),
        maximumWarpError=max(v['maximum'] for v in harmonic),acousticCoordinatesChanged=True,oldAcousticOperatorsCompatible=False,
        acousticFitAccepted=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    (a.out/'hybrid_temporal_surface.json').write_text(json.dumps(dict(summary=summary,candidates=rows,validation=validation,proof=tests,
        benchmark=bench,harmonic=harmonic,frozenSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_HYBRID_SURFACE_GATE '+json.dumps(summary),flush=True)
    for v in rows:print('G3_HYBRID_SURFACE_CASE '+json.dumps(v),flush=True)
    for v in bench:print('G3_HYBRID_TEMPORAL_BENCH '+json.dumps(v),flush=True)
    if not gate:raise ValueError('hybrid temporal proof failed')
if __name__=='__main__':main()
