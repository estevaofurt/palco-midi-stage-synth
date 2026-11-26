"""G3.11y: dry structural response snapshots in energy coordinates.
Real congruence preserves mass, stiffness and non-diagonal damping.
Frozen rank selection, independently sampled validation; no acoustic or string claim."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.linalg import cholesky,solve_triangular,solve,eigh,svd
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from bridge_strings import centerline
from spline_plate import assemble
from structural_assembly import assemble as structure
from structural_response import congruence,response as direct
from dry_structural_modal import mobility,read
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

def normalized(M,K,D,P):
    s=1/np.sqrt(np.diag(M));W=s[:,None]*s[None,:]
    m=M*W;k=K*W;d=D*W;p=P*s[:,None]
    L=cholesky(k+(2*np.pi*100)**2*m,lower=True)
    return congruence(L,m),congruence(L,k),congruence(L,d),solve_triangular(L,p,lower=True)

def snapshots(m,k,d,p,freq):
    columns=[]
    for f in freq:
        w=2*np.pi*f;X=solve(k-w*w*m+1j*w*d,p)
        if relative((k-w*w*m+1j*w*d)@X,p)>1e-7:raise ValueError('snapshot residual')
        norm=np.maximum(np.linalg.norm(X,axis=0),1e-30)
        columns.extend((X.real/norm,X.imag/norm))
    V,s,_=svd(np.column_stack(columns),full_matrices=False)
    rank=int(np.count_nonzero(s>s[0]*1e-12))
    return V[:,:rank],s

def reduced(m,k,d,p,V):
    M=V.T@m@V;K=V.T@k@V;D=V.T@d@V;P=V.T@p
    w,U=eigh((K+K.T)/2,(M+M.T)/2)
    D=U.T@D@U;D=(D+D.T)/2;P=U.T@P
    mass=relative(U.T@M@U,np.eye(len(w)));stiffness=relative(U.T@K@U,np.diag(w))
    minimum=float(np.linalg.eigvalsh(D).min())
    if np.any(w<=0) or minimum<-1e-10*max(np.linalg.norm(D),1e-30) or max(mass,stiffness)>1e-8:raise ValueError('invalid reduced congruence')
    return w,D,P,dict(massRelative=mass,stiffnessRelative=stiffness,minimumDampingEigenvalue=minimum)

def errors(Y,ref):
    vals=[relative(x,y) for x,y in zip(Y,ref)]
    return dict(maximum=max(vals),aggregate=relative(Y,ref),perFrequency=vals)

def select(m,k,d,p,train,reference,ranks):
    V,s=snapshots(m,k,d,p,train);rows=[];models={}
    for n in sorted(set(min(int(v),V.shape[1]) for v in ranks)):
        w,D,P,audit=reduced(m,k,d,p,V[:,:n]);models[n]=(w,D,P)
        e=errors(mobility(w,D,P,train),reference)
        rows.append(dict(rank=n,training=e,congruence=audit))
    eligible=[v for v in rows if v['training']['maximum']<=.05]
    selected=min(eligible,key=lambda v:v['rank']) if eligible else min(rows,key=lambda v:v['training']['maximum'])
    return selected,rows,models[selected['rank']],s

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
    train=np.geomspace(30,500,32);valid=np.sqrt(train[:-1]*train[1:])
    reference,refaudit,_=direct(M,K,D,P,train,np.ones(4))
    if not refaudit['gate']:raise ValueError('training reference failed')
    m,k,d,p=normalized(M,K,D,P)
    selected,rows,model,s=select(m,k,d,p,train,reference,(16,32,48,64,96,128,192,256))
    w,Dr,Pr=model;a.out.mkdir(parents=True,exist_ok=True)
    archive=save_matrices(a.out,'dry_snapshot_model',frequencies=train,stiffness=w,damping=Dr,ports=Pr)
    frozen=dict(selected=selected,archive=archive,trainingHz=train.tolist(),scaleSha256=hashlib.sha256(raw).hexdigest())
    frozenraw=json.dumps(frozen,indent=2,allow_nan=False).encode();(a.out/'frozen_snapshot.json').write_bytes(frozenraw)
    validation,vaudit,_=direct(M,K,D,P,valid,np.ones(4))
    if not vaudit['gate']:raise ValueError('validation reference failed')
    error=errors(mobility(w,Dr,Pr,valid),validation)
    summary=dict(gate=True,diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,fullDampingPreserved=True,
        fullCoordinates=len(M),selectedRank=selected['rank'],trainingMaximum=selected['training']['maximum'],validationMaximum=error['maximum'],
        reductionGate=bool(max(error['maximum'],selected['training']['maximum'])<=.05),selectionUsedValidation=False,
        acousticFitAccepted=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    (a.out/'dry_snapshot_reduction.json').write_text(json.dumps(dict(summary=summary,candidates=rows,validation=error,validationHz=valid.tolist(),
        singularValues=s.tolist(),trainingReferenceAudit=refaudit,validationReferenceAudit=vaudit,frozenSha256=hashlib.sha256(frozenraw).hexdigest()),indent=2,allow_nan=False))
    print('G3_DRY_SNAPSHOT_GATE '+json.dumps(summary),flush=True)
    for row in rows:print('G3_DRY_SNAPSHOT_CASE '+json.dumps(dict(rank=row['rank'],trainingMaximum=row['training']['maximum'])),flush=True)
if __name__=='__main__':main()
