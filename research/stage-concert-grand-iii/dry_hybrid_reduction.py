"""G3.11z: hybrid low eigenmodes + residual response snapshots.
Training and rank selection use development grids only; outer grid frozen.
Dry physical hypothesis, no acoustic or string certification."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.linalg import eigh,svd,solve
from dry_snapshot_reduction import normalized,reduced,errors,read
from dry_structural_modal import mobility
from structural_response import response as direct
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from bridge_strings import centerline
from spline_plate import assemble
from structural_assembly import assemble as structure
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

def grids():
    x=np.geomspace(30,500,32);a=x[:-1];b=x[1:]
    train=np.sort(np.r_[x,np.sqrt(a*b)])
    inner=a**.75*b**.25
    outer=a**.25*b**.75
    return train,inner,outer

def response_columns(m,k,d,p,freq):
    cols=[]
    for f in freq:
        w=2*np.pi*f;A=k-w*w*m+1j*w*d;X=solve(A,p)
        if relative(A@X,p)>1e-7:raise ValueError('snapshot residual')
        norm=np.maximum(np.linalg.norm(X,axis=0),1e-30)
        cols.extend((X.real/norm,X.imag/norm))
    return np.column_stack(cols)

def hybrid_basis(m,k,S,low):
    # normalized() gives K+shift*M=I; largest mass eigenvalues are
    # lowest undamped modes. Verify this property rather than assume it.
    if relative(k+(2*np.pi*100)**2*m,np.eye(len(m)))>1e-7:raise ValueError('unexpected energy metric')
    ev,V=eigh(m,subset_by_index=[len(m)-low,len(m)-1])
    V=V[:,::-1]
    if ev.min()<=0:raise ValueError('nonpositive low mode mass')
    R=S-V@(V.T@S);R-=V@(V.T@R)
    W,s,_=svd(R,full_matrices=False)
    keep=int(np.count_nonzero(s>max(s[0]*1e-12,np.linalg.norm(S)*1e-13)))
    W=W[:,:keep]
    if keep:
        W-=V@(V.T@W);W,_=np.linalg.qr(W,mode='reduced')
    T=np.column_stack((V,W))
    if relative(T.T@T,np.eye(T.shape[1]))>1e-9:raise ValueError('hybrid orthogonality')
    return T,s,keep

def select_hybrid(m,k,d,p,train,inner,Y,Z,lows=(32,64,96),extras=(0,8,16,32,48,64,96)):
    S=response_columns(m,k,d,p,train);rows=[];models={}
    for low in sorted(set(min(v,len(m)) for v in lows)):
        T,s,keep=hybrid_basis(m,k,S,low)
        for extra in sorted(set(min(v,keep) for v in extras)):
            w,D,P,audit=reduced(m,k,d,p,T[:,:low+extra])
            tr=errors(mobility(w,D,P,train),Y);inn=errors(mobility(w,D,P,inner),Z)
            row=dict(lowModes=low,extraModes=extra,rank=low+extra,trainingMaximum=tr['maximum'],
                innerMaximum=inn['maximum'],congruence=audit)
            rows.append(row);models[(low,extra)]=(w,D,P)
    eligible=[x for x in rows if max(x['trainingMaximum'],x['innerMaximum'])<=.05]
    err=lambda x:max(x['trainingMaximum'],x['innerMaximum'])
    selected=min(eligible,key=lambda x:(x['rank'],err(x),x['lowModes'])) if eligible else min(rows,key=lambda x:(err(x),x['rank']))
    return selected,rows,models[(selected['lowModes'],selected['extraModes'])]

def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw)
    if sc['version']!='G3-scale-hypothesis-02' or sc['summary']['gate'] is not True:raise ValueError('unapproved scale')
    l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json')
    c=contour_build(l,read('board_contour_hypothesis.json'),mat);rib=read('ribbed_plate_hypothesis.json')['rib']
    poly=np.array(c['contourXY_m']);centers={s:centerline(l['bridgeAttachmentNodes'][s]) for s in ('bass','treble')}
    plate=assemble(poly,c['ribs'],mat['plate'],rib,30,14,False)
    z=structure(plate,centers,read('bridge_hypothesis.json'),mat,read('rim_structure_hypothesis.json'),2,8,14,True)
    M=z['M'];K=z['K']+z['Jrim']+z['Jbridge'];D=z['D'];P=z['P'][:,[0,2,4,5]]
    train,inner,outer=grids()
    Y,ta,_=direct(M,K,D,P,train,np.ones(4));Z,ia,_=direct(M,K,D,P,inner,np.ones(4))
    if not ta['gate'] or not ia['gate']:raise ValueError('development reference failed')
    m,k,d,p=normalized(M,K,D,P)
    selected,rows,model=select_hybrid(m,k,d,p,train,inner,Y,Z)
    w,Dr,Pr=model;a.out.mkdir(parents=True,exist_ok=True)
    archive=save_matrices(a.out,'dry_hybrid_model',frequencies=train,stiffness=w,damping=Dr,ports=Pr)
    frozen=dict(selected=selected,archive=archive,trainingHz=train.tolist(),innerHz=inner.tolist(),
        plannedOuterHz=outer.tolist(),scaleSha256=hashlib.sha256(raw).hexdigest())
    frozenraw=json.dumps(frozen,indent=2,allow_nan=False).encode();(a.out/'frozen_hybrid.json').write_bytes(frozenraw)
    ref,oa,_=direct(M,K,D,P,outer,np.ones(4))
    if not oa['gate']:raise ValueError('outer reference failed')
    e=errors(mobility(w,Dr,Pr,outer),ref)
    summary=dict(gate=True,diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,
        fullCoordinates=len(M),selectedRank=selected['rank'],lowModes=selected['lowModes'],extraModes=selected['extraModes'],
        trainingMaximum=selected['trainingMaximum'],innerMaximum=selected['innerMaximum'],outerMaximum=e['maximum'],
        reductionGate=bool(max(selected['trainingMaximum'],selected['innerMaximum'],e['maximum'])<=.05),
        selectionUsedOuter=False,priorValidationReusedAsTraining=True,fullDampingPreserved=True,
        acousticFitAccepted=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    (a.out/'dry_hybrid_reduction.json').write_text(json.dumps(dict(summary=summary,candidates=rows,outer=e,
        frozenSha256=hashlib.sha256(frozenraw).hexdigest(),trainingReferenceAudit=ta,innerReferenceAudit=ia,outerReferenceAudit=oa),indent=2,allow_nan=False))
    print('G3_DRY_HYBRID_GATE '+json.dumps(summary),flush=True)
    for row in rows:print('G3_DRY_HYBRID_CASE '+json.dumps(row),flush=True)
if __name__=='__main__':main()
