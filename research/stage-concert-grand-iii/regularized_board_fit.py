"""G3.11h: regularized positive-real candidate selection.
Validation is never used to select complexity, damping or regularization."""
import argparse,hashlib,json,itertools
from pathlib import Path
import numpy as np
from passive_board_fit import dictionary,psd,evaluate,audit
from split_radiation import relative
from acoustic_matrix_archive import read_npz
from fixed_355_validation import require_fine
from high_modal_allocation import read
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from dense_frequency_batch import BATCHES,FREQ
from dual_cavity_spatial_diagnostic import save_matrices

def candidates(n):
    # Each inner fold has n-1 complex frequency rows. Bound dictionary
    # size by its real observation count; this does not guarantee identifiability.
    return [(k,g,r) for k,g,r in itertools.product((5,9,15),(5.,15.),(1e-4,1e-2)) if k+3<=2*(n-1)]

def centers_for(k):
    return np.linspace(20.,400.,k)

def solve_fit(freq,Z,cfg,maxiter=20000):
    k,g,r=cfg;centers=centers_for(k);freq=np.asarray(freq,float);Z=np.asarray(Z,complex)
    if freq.ndim!=1 or len(freq)<2 or len(set(freq))!=len(freq) or not np.isfinite(freq).all() or np.any(freq<=0) or Z.ndim!=3 or Z.shape[0]!=len(freq) or Z.shape[1]!=Z.shape[2] or not np.isfinite(Z).all() or maxiter<1:raise ValueError('invalid training data')
    if any(relative(v,v.T)>1e-8 or np.linalg.eigvalsh((v+v.conj().T)/2).min()<-1e-8*max(np.linalg.norm(v),1e-30) for v in Z):raise ValueError('invalid passive sample')
    w=1/np.maximum(np.linalg.norm(Z,axis=(1,2)),1e-30)
    D=dictionary(2j*np.pi*freq,centers,g)*w[:,None]
    norm=np.linalg.norm(D,axis=0);D/=norm
    A=np.concatenate([D.real,D.imag]);Y=np.concatenate([Z.real*w[:,None,None],Z.imag*w[:,None,None]])
    H=A.T@A+r*np.eye(A.shape[1]);rhs=np.einsum('ij,ikl->jkl',A,Y)
    L=np.linalg.eigvalsh(H)[-1];X=np.zeros_like(rhs);V=X.copy();t=1.
    def project(V):
        return psd(V-(np.einsum('ij,jkl->ikl',H,V)-rhs)/L)
    residual=float('inf')
    for i in range(1,maxiter+1):
        N=project(V);u=(1+np.sqrt(1+4*t*t))/2
        V=N+(t-1)/u*(N-X);X=N;t=u
        if i%100==0 or i==maxiter:
            residual=float(np.linalg.norm(X-project(X))/max(np.linalg.norm(X),1e-30))
            if residual<=1e-7:break
    C=X/norm[:,None,None]
    if not np.isfinite(C).all():raise ValueError('nonfinite solution')
    return C,dict(iterations=i,projectedGradientRelative=residual,optimizerConverged=residual<=1e-7,
        normalizedDesignRank=int(np.linalg.matrix_rank(A)),dictionaryColumns=A.shape[1],
        regularizedCondition=float(np.linalg.cond(H)))

def error_rows(freq,Z,C,cfg):
    k,g,_=cfg;pred=evaluate(2j*np.pi*np.asarray(freq),C,centers_for(k),g)
    return [dict(frequencyHz=float(f),relativeError=relative(x,y),
        resistanceRelative=relative(x.real,y.real),reactanceRelative=relative(x.imag,y.imag)) for f,x,y in zip(freq,pred,Z)]

def select(freq,Z):
    freq=np.asarray(freq,float);Z=np.asarray(Z,complex);rows=[]
    for cfg in candidates(len(freq)):
        folds=[]
        for i,f in enumerate(freq):
            idx=np.arange(len(freq))!=i
            C,opt=solve_fit(freq[idx],Z[idx],cfg);k,g,_=cfg
            rep=audit(C,centers_for(k),g)
            er=error_rows([f],Z[i:i+1],C,cfg)[0]
            folds.append(dict(heldOutHz=float(f),trainingHz=freq[idx].tolist(),**er,optimization=opt,passivity=rep))
        errors=[v['relativeError'] for v in folds]
        row=dict(config=list(cfg),maximumInnerError=max(errors),meanInnerError=float(np.mean(errors)),
            eligible=all(v['optimization']['optimizerConverged'] and v['passivity']['gate'] for v in folds),folds=folds)
        rows.append(row)
        print('G3_REGULARIZED_CANDIDATE '+json.dumps({k:v for k,v in row.items() if k!='folds'},allow_nan=False),flush=True)
    if not rows:raise ValueError('no candidate dictionary')
    eligible=[v for v in rows if v['eligible']]
    selected=min(eligible or rows,key=lambda v:(v['maximumInnerError'],v['meanInnerError'],v['config'][0],v['config']))
    return selected,rows

def require_dense(d,angle,sha):
    s=d.get('summary',{});train=sorted([*FREQ,*BATCHES[0]]);valid=list(BATCHES[1]);f=sorted(train+valid)
    expected=dict(gate=True,angleDeg=angle,diagnosticOnly=True,referenceModes=385,trainingHz=train,validationHz=valid,
        newPointCount=12,referencePointCount=18,fitNotPerformed=True,continuousFrequencyValidated=False,timeDomainReady=False,radiationReady=False)
    if d.get('scaleSha256')!=sha or d.get('frequenciesHz')!=f or any(s.get(k)!=v for k,v in expected.items()):raise ValueError('invalid frozen split')
    return train,valid

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','out'):p.add_argument('--'+k,type=Path,required=True)
    group=p.add_mutually_exclusive_group(required=True);group.add_argument('--fine',type=Path);group.add_argument('--dense',type=Path)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw)
    assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    if a.dense:
        manifest=(a.dense/'dense_board_reference.json').read_bytes();d=json.loads(manifest)
        train,valid=require_dense(d,a.angle,sha);freq=d['frequenciesHz']
        Z=read_npz(a.dense,d['archive'],dict(Y=(len(freq),4,4)),freq)['Y']
    else:
        manifest=(a.fine/'graded_combined_refinement.json').read_bytes();d=json.loads(manifest);require_fine(d,a.angle,sha)
        l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
        nm=len(geometry(np.asarray(q['contourXY_m']),l,read('cabinet_geometry_hypothesis.json'))['microphonesXYZ_m'])
        freq=FREQ;train=FREQ;valid=[];n=len(freq)
        Z=read_npz(a.fine,d['archive'],dict(Zu=(n,334,334),Pu=(n,nm,334),Y=(n,4,4),flow=(n,385,4)),freq)['Y']
    trainZ=Z[[freq.index(f) for f in train]]
    selected,rows=select(train,trainZ);cfg=tuple(selected['config']);k,g,r=cfg
    C,opt=solve_fit(train,trainZ,cfg);rep=audit(C,centers_for(k),g)
    training=error_rows(train,trainZ,C,cfg)
    a.out.mkdir(parents=True,exist_ok=True)
    # Freeze the coefficients and selection before scoring the independent set.
    archive=save_matrices(a.out,'regularized_coefficients',frequencies=train,coefficients=C,centersHz=centers_for(k))
    frozen=dict(selected=selected,optimization=opt,passivity=rep,archive=archive,training=training,trainingHz=train,
        scaleSha256=sha,sourceManifestSha256=hashlib.sha256(manifest).hexdigest(),angleDeg=a.angle)
    frozenraw=json.dumps(frozen,indent=2,allow_nan=False).encode();(a.out/'frozen_selection.json').write_bytes(frozenraw)
    validation=error_rows(valid,Z[[freq.index(f) for f in valid]],C,cfg) if valid else []
    tr=max(v['relativeError'] for v in training);va=max(v['relativeError'] for v in validation) if validation else None
    gate=bool(valid and selected['eligible'] and opt['optimizerConverged'] and rep['gate'] and max(tr,va,selected['maximumInnerError'])<=.05)
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,sparsePilot=not bool(valid),selectedConfig=list(cfg),
        trainingPointCount=len(train),validationPointCount=len(valid),selectionUsedValidation=False,
        maximumInnerError=selected['maximumInnerError'],trainingError=tr,validationError=va,optimizerGate=bool(selected['eligible'] and opt['optimizerConverged']),
        passiveStructureGate=rep['gate'],fitGate=gate,continuousFrequencyValidated=False,timeDomainReady=False,radiationReady=False)
    (a.out/'regularized_fit.json').write_text(json.dumps(dict(summary=summary,candidates=rows,validation=validation,
        frozenSelectionSha256=hashlib.sha256(frozenraw).hexdigest(),scaleSha256=sha,frequenciesHz=freq),indent=2,allow_nan=False))
    print('G3_REGULARIZED_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
