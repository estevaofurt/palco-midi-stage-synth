"""G3.12f: exact fixed-front wire condensation on frozen and enriched
structural bases. Dry frequency-domain pilot, no approved acoustic load.
Selection uses only development frequencies; reserve interstitial validation."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.linalg import cholesky,solve_triangular,eigh,svd
from enriched_baffle import load_source
from dry_snapshot_reduction import normalized,read
from dry_hybrid_reduction import response_columns,hybrid_basis
from dry_structural_modal import mobility
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from bridge_strings import centerline
from spline_plate import assemble
from structural_assembly import assemble as structure
from string_structure import setup,response as reference
from modal_string_radiation import response as condensed
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

def enrich_basis(T,S,count):
    # Preserve the entire frozen subspace, even when adding new port responses.
    R=S-T@(T.T@S);R-=T@(T.T@R)
    W,s,_=svd(R,full_matrices=False)
    rank=int(np.count_nonzero(s>max(s[0]*1e-12,np.linalg.norm(S)*1e-13)))
    W=W[:,:min(count,rank)]
    if W.shape[1]:
        W-=T@(T.T@W);W,_=np.linalg.qr(W,mode='reduced')
    V=np.column_stack((T,W))
    if relative(V.T@V,np.eye(V.shape[1]))>1e-9:raise ValueError('enrichment orthogonality')
    return V

def model(M,K,D,P,lift):
    mass=lift.T@M@lift;stiff=lift.T@K@lift;drag=lift.T@D@lift
    w,U=eigh((stiff+stiff.T)/2,(mass+mass.T)/2)
    V=lift@U;Dr=U.T@drag@U;Dr=(Dr+Dr.T)/2
    if min(w)<=0 or np.linalg.eigvalsh(Dr).min()<-1e-10*max(np.linalg.norm(Dr),1e-30):raise ValueError('nonpassive reduction')
    audit=relative(U.T@mass@U,np.eye(len(w)))
    if audit>1e-8:raise ValueError('mass normalization')
    return dict(M=np.eye(len(w)),K=np.diag(w),D=Dr,P=V.T@P),V,audit

def evaluate(modal,lift,wires,freq):
    n=len(modal['M']);ports=[lift[w.rear,:] for w in wires];rows=[];Y=[]
    for f in freq:
        y,_,a=condensed(modal,ports,wires,np.zeros((n,n)),np.zeros((1,n)),f)
        rows.append(a);Y.append(y)
    if not all(a['gate'] for a in rows):raise ValueError('reduced wire algebra failed')
    return np.stack(Y),rows

def comparison(Y,ref):
    e=[relative(x,y) for x,y in zip(Y,ref)]
    return dict(maximum=max(e),aggregate=relative(Y,ref),perFrequency=e)

def rebuild_base(M,K,D,P,archive,train):
    # Physical coordinates include the spline mass-orthogonalization.
    # Recreate the frozen hybrid subspace in this assembly, not the
    # coefficient columns of a separately generated spline basis.
    m,k,d,p=normalized(M,K,D,P)
    S=response_columns(m,k,d,p,train)
    V,_,keep=hybrid_basis(m,k,S,64)
    if keep<8:raise ValueError('insufficient frozen residual rank')
    s=1/np.sqrt(np.diag(M));L=cholesky((K+(2*np.pi*100)**2*M)*(s[:,None]*s[None,:]),lower=True)
    lift=s[:,None]*solve_triangular(L.T,V[:,:72],lower=False)
    md,A,mass=model(M,K,D,P,lift)
    Y=mobility(np.diag(md['K']),md['D'],md['P'],train)
    ref=mobility(archive['stiffness'],archive['damping'],archive['ports'],train)
    replay=comparison(Y,ref)['maximum']
    return A,dict(massRelative=mass,mobilityReplayMaximum=replay,gate=bool(mass<=1e-8 and replay<=1e-6))

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();z,sha=load_source(a.source,a.scale)
    raw=a.scale.read_bytes();sc=json.loads(raw);rows={v['key']:v for v in sc['rows']}
    l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json')
    c=contour_build(l,read('board_contour_hypothesis.json'),mat);rib=read('ribbed_plate_hypothesis.json')['rib']
    poly=np.asarray(c['contourXY_m']);centers={s:centerline(l['bridgeAttachmentNodes'][s]) for s in ('bass','treble')}
    plate=assemble(poly,c['ribs'],mat['plate'],rib,30,14,False)
    q=structure(plate,centers,read('bridge_hypothesis.json'),mat,read('rim_structure_hypothesis.json'),2,8,14,True)
    M=q['M'];K=q['K']+q['Jrim']+q['Jbridge'];D=q['D']
    old=z['physicalLift'];P0=q['P'][:,[0,2,4,5]]
    if old.shape!=(len(M),72):raise ValueError('physical lift shape mismatch')
    oldaudit=dict(massRelative=relative(old.T@M@old,np.eye(72)),portsRelative=relative(old.T@P0,z['ports']),
        stiffnessRelative=relative(old.T@K@old,np.diag(z['stiffness'])),dampingRelative=relative(old.T@D@old,z['damping']))
    f=json.loads((a.source/'frozen_surface.json').read_text());grid=np.asarray(f['trainingHz'])
    lift,replay=rebuild_base(M,K,D,P0,z,grid)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'wire_coordinate_replay.json').write_text(json.dumps(dict(archivedDirect=oldaudit,reconstructed=replay),indent=2,allow_nan=False))
    print('G3_WIRE_COORDINATE_GATE '+json.dumps(dict(archivedDirect=oldaudit,reconstructed=replay)),flush=True)
    if not replay['gate']:raise ValueError('frozen hybrid response replay failed')
    keys=[45,48,60,64];P,wires,labels=setup(q,centers,rows,keys,2,128)
    rear=sorted(set(w.rear for w in wires));F=np.zeros((len(M),len(rear)));F[rear,np.arange(len(rear))]=1.
    train=np.geomspace(30,500,16);valid=np.sqrt(train[:-1]*train[1:])
    full,fa,fr=reference(M,K,D,P,wires,train)
    if not fa['gate']:raise ValueError('full wire reference failed')
    s=1/np.sqrt(np.diag(M));L=cholesky((K+(2*np.pi*100)**2*M)*(s[:,None]*s[None,:]),lower=True)
    T,_=np.linalg.qr(L.T@(lift/s[:,None]),mode='reduced')
    m,k,d,f=normalized(M,K,D,F);S=response_columns(m,k,d,f,train)
    cases=[];models={}
    for extra in (0,8,16,32,48):
        V=enrich_basis(T,S,extra)
        physical=s[:,None]*solve_triangular(L.T,V,lower=False)
        md,A,mass=model(M,K,D,P,physical)
        Y,audit=evaluate(md,A,wires,train);err=comparison(Y,full)
        row=dict(extra=extra,rank=len(md['M']),training=err,massRelative=mass,algebra=audit)
        cases.append(row);models[extra]=(md,A)
        print('G3_WIRE_PORT_CASE '+json.dumps(dict(extra=extra,rank=row['rank'],maximumTraining=err['maximum'])),flush=True)
    eligible=[v for v in cases if v['training']['maximum']<=.05]
    chosen=min(eligible,key=lambda v:(v['rank'],v['extra'])) if eligible else min(cases,key=lambda v:v['training']['maximum'])
    md,A=models[chosen['extra']];a.out.mkdir(parents=True,exist_ok=True)
    # Export the new coordinate map; it is NOT interchangeable with the
    # archived 72-field acoustic data even if the rank happens to match.
    archive=save_matrices(a.out,'wire_port_model',frequencies=train,stiffness=np.diag(md['K']),damping=md['D'],ports=md['P'],
        physicalLift=A,wirePorts=np.stack([A[w.rear] for w in wires]))
    frozen=dict(selectedExtra=chosen['extra'],selectedRank=chosen['rank'],archive=archive,sourceFrozenSha256=sha,
        scaleSha256=hashlib.sha256(raw).hexdigest(),keys=keys,wireIds=[w.id for w in wires],trainingHz=train.tolist(),plannedValidationHz=valid.tolist())
    data=json.dumps(frozen,indent=2,allow_nan=False).encode();(a.out/'frozen_wire_ports.json').write_bytes(data)
    fullv,va,vr=reference(M,K,D,P,wires,valid)
    if not va['gate']:raise ValueError('full validation reference failed')
    Y,ya=evaluate(md,A,wires,valid);err=comparison(Y,fullv)
    base,baseLift=models[0];Y0,_=evaluate(base,baseLift,wires,valid);baseerr=comparison(Y0,fullv)
    summary=dict(gate=True,diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,keys=keys,wires=len(wires),
        selectedRank=chosen['rank'],selectedExtra=chosen['extra'],fullStructuralCoordinates=len(M),trainingMaximum=chosen['training']['maximum'],
        validationMaximum=err['maximum'],frozen72ValidationMaximum=baseerr['maximum'],
        reductionGate=bool(max(chosen['training']['maximum'],err['maximum'])<=.05),selectionUsedValidation=False,
        localCoordinateReconstruction=True,baseMobilityReplayMaximum=replay['mobilityReplayMaximum'],oldAcousticOperatorsCompatible=False,fixedFront=True,verticalPolarizationOnly=True,acousticLoadIncluded=False,
        timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    (a.out/'wire_port_enrichment.json').write_text(json.dumps(dict(summary=summary,cases=cases,validation=err,baseValidation=baseerr,
        validationAlgebra=ya,referenceTraining=fa,referenceValidation=va,frozenSha256=hashlib.sha256(data).hexdigest()),indent=2,allow_nan=False))
    print('G3_WIRE_PORT_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
