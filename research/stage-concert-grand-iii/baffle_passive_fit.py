"""G3.12e: passive impedance pilot for the 72-field ideal-baffle reference.
PSD coefficient ADMM with separate resistance/reactance scaling.
No zero-frequency spring or constant drag; the model satisfies Z(0)=0.
Fit selection is independent of the reserved acoustic samples."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from passive_board_fit import psd
from acoustic_matrix_archive import read_npz
from enriched_baffle import load_source
from baffle_frequency_grid import TRAIN,VALID,PREVIOUS
from surface_reactive_fft import wet_response
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

# Frequencies in Hz. All scalar atoms are positive real for Re(s)>0.
CONFIGS=[
    dict(relax=[40.,150.,600.],osc=[],gamma=30.,ridge=1e-6),
    dict(relax=[20.,80.,240.,800.,2400.],osc=[],gamma=30.,ridge=1e-6),
    dict(relax=[40.,150.,600.],osc=[45.,120.,220.,340.],gamma=35.,ridge=1e-6),
    dict(relax=[40.,150.,600.],osc=[30.,80.,130.,180.,240.,320.],gamma=60.,ridge=1e-6)]

def dictionary(s,cfg):
    s=np.atleast_1d(np.asarray(s,complex));a=2*np.pi*np.asarray(cfg['relax'],float)
    w=2*np.pi*np.asarray(cfg['osc'],float);g=2*np.pi*cfg['gamma']
    if not np.isfinite(s).all() or np.any(s.real<0) or not np.isfinite(np.r_[a,w,g]).all() or np.any(a<=0) or np.any(w<=0) or g<=0:raise ValueError('invalid dictionary')
    return np.column_stack([s,s[:,None]/(s[:,None]+a),s[:,None]/(s[:,None]**2+2*g*s[:,None]+w*w)])

def evaluate(s,C,cfg):
    return np.einsum('fa,aij->fij',dictionary(s,cfg),C)

def fit(freq,Z,cfg,maxiter=2000,tol=1e-6):
    freq=np.asarray(freq,float);Z=np.asarray(Z,complex)
    if freq.ndim!=1 or len(freq)<2 or len(set(freq))!=len(freq) or np.any(freq<=0) or not np.isfinite(freq).all() or Z.ndim!=3 or Z.shape[0]!=len(freq) or Z.shape[1]!=Z.shape[2] or not np.isfinite(Z).all() or maxiter<1 or tol<=0:raise ValueError('invalid fit')
    if any(relative(v,v.T)>1e-8 or np.linalg.eigvalsh((v+v.conj().T)/2).min()<-1e-8*max(np.linalg.norm(v),1e-30) for v in Z):raise ValueError('nonpassive input')
    n=Z.shape[1];D=dictionary(2j*np.pi*freq,cfg)
    # Balance resistance and reactance independently; do not hide a
    # poor resistance fit behind large inertance.
    floor=max(np.linalg.norm(Z,axis=(1,2)).max()*1e-12,1e-30)
    wr=1/np.maximum(np.linalg.norm(Z.real,axis=(1,2)),floor)
    wi=1/np.maximum(np.linalg.norm(Z.imag,axis=(1,2)),floor)
    A=np.vstack([D.real*wr[:,None],D.imag*wi[:,None]])
    B=np.concatenate([Z.real*wr[:,None,None],Z.imag*wi[:,None,None]])
    B=(B+B.transpose(0,2,1))/2
    scale=np.linalg.norm(A,axis=0)
    if np.any(scale<=0):raise ValueError('empty dictionary column')
    A/=scale;H=A.T@A;rhs=A.T@B.reshape(len(B),-1)
    ridge=cfg['ridge']
    if not np.isfinite(ridge) or ridge<0:raise ValueError('invalid ridge')
    rho=1.;m=len(scale);X=np.zeros((m,n,n));U=X.copy();Q=X.copy()
    fac=cho_factor(H+(ridge+rho)*np.eye(m))
    primal=dual=float('inf')
    for it in range(1,maxiter+1):
        X=cho_solve(fac,rhs+rho*(Q-U).reshape(m,-1)).reshape(m,n,n)
        old=Q;Q=psd(X+U);U+=X-Q
        den=max(np.linalg.norm(X),np.linalg.norm(Q),1e-30)
        primal=float(np.linalg.norm(X-Q)/den)
        dual=float(rho*np.linalg.norm(Q-old)/max(np.linalg.norm(rho*U),np.linalg.norm(rhs),1e-30))
        if max(primal,dual)<=tol:break
        if it%50==0:
            new=rho*2 if primal>10*dual else rho/2 if dual>10*primal else rho
            new=float(np.clip(new,1e-4,1e4))
            if new!=rho:
                U*=rho/new;rho=new;fac=cho_factor(H+(ridge+rho)*np.eye(m))
    C=Q/scale[:,None,None]
    if not np.isfinite(C).all():raise ValueError('nonfinite fit')
    return C,dict(iterations=it,primalRelative=primal,dualRelative=dual,converged=bool(max(primal,dual)<=tol),rho=rho)

def audit(C,cfg):
    eig=min(float(np.linalg.eigvalsh((v+v.T)/2).min()/max(np.linalg.norm(v),1e-30)) for v in C)
    sym=max(relative(v,v.T) for v in C)
    f=np.geomspace(1,20000,121)
    s=np.r_[2j*np.pi*f,2*np.pi*10+2j*np.pi*f]
    Z=evaluate(s,C,cfg)
    pr=min(float(np.linalg.eigvalsh((v+v.conj().T)/2).min()/max(np.linalg.norm(v),1e-30)) for v in Z)
    zero=bool(np.count_nonzero(evaluate([0j],C,cfg))==0)
    return dict(coefficientMinRelative=eig,symmetry=sym,positiveRealSampleMin=pr,zeroAtDC=zero,
        gate=bool(eig>=-1e-10 and sym<=1e-10 and pr>=-1e-10 and zero))

def score(freq,data,C,cfg,z):
    rows=[]
    for i,(f,Z) in enumerate(zip(freq,evaluate(2j*np.pi*np.asarray(freq),C,cfg))):
        target=data['impedance'][i];H=data['pressure'][i]
        Y,O,a=wet_response(z['stiffness'],z['damping'],z['ports'],z['fieldMap'],Z,H,f)
        row=dict(frequencyHz=float(f),impedance=relative(Z,target),resistance=relative(Z.real,target.real),
            reactance=relative(Z.imag,target.imag),mobility=relative(Y,data['mobility'][i]),
            pressureWithReferenceObserver=relative(O,data['observation'][i]),power=a)
        row['maximum']=max(row[k] for k in ('impedance','resistance','reactance','mobility','pressureWithReferenceObserver'))
        row['powerGate']=bool(max(a['powerRelative'],a['reciprocity'])<=1e-8 and a['passivityMinRelative']>=-1e-8)
        rows.append(row)
    return rows

def maximum(rows):return max(v['maximum'] for v in rows)
def subset(data,ix):return {k:v[ix] for k,v in data.items()}

def select(freq,data,z):
    f=np.asarray(freq);rows=[]
    for i,cfg in enumerate(CONFIGS):
        folds=[]
        for j in range(3):
            ix=np.arange(len(f))%3==j
            C,opt=fit(f[~ix],data['impedance'][~ix],cfg)
            rep=audit(C,cfg);sc=score(f[ix],subset(data,ix),C,cfg,z)
            folds.append(dict(heldOutHz=f[ix].tolist(),maximum=maximum(sc),optimization=opt,passivity=rep,
                score=sc,eligible=bool(opt['converged'] and rep['gate'] and all(v['powerGate'] for v in sc))))
        row=dict(index=i,config=cfg,maximumInner=max(v['maximum'] for v in folds),
            eligible=all(v['eligible'] for v in folds),folds=folds)
        rows.append(row)
        print('G3_BAFFLE_PASSIVE_CANDIDATE '+json.dumps({k:v for k,v in row.items() if k!='folds'},allow_nan=False),flush=True)
    eligible=[v for v in rows if v['eligible']]
    return min(eligible or rows,key=lambda v:(v['maximumInner'],v['index'])),rows

def read_grid(root,role,sha):
    raw=(root/'baffle_grid.json').read_bytes();d=json.loads(raw);s=d['summary'];freq=TRAIN if role=='training' else VALID
    expected=dict(gate=True,diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,fields=72,
        oneSidedIdealBaffle=True,role=role,pointCount=len(freq),fitNotPerformed=True,
        acousticFitAccepted=False,timeDomainReady=False,radiationReady=False)
    if any(s.get(k)!=v for k,v in expected.items()) or d['sourceFrozenSha256']!=sha or d['frequenciesHz']!=freq or d['trainingHz']!=TRAIN or d['validationHz']!=VALID:raise ValueError('invalid grid provenance')
    if [v['frequencyHz'] for v in d['cases']]!=freq or not all(v['gate'] is True and v['role']==role for v in d['cases']):
        raise ValueError('incomplete grid')
    if max(s['maximumKernelError'],s['maximumPressureError'])>1e-6 or s['maximumReactiveError']>.005:
        raise ValueError('grid convergence failed')
    if role=='training' and ([v['frequencyHz'] for v in d['replay']]!=PREVIOUS or not all(v['gate'] is True for v in d['replay'])):
        raise ValueError('missing replay')
    n=len(freq);data=read_npz(root,d['archive'],dict(impedance=(n,72,72),pressure=(n,2,72),mobility=(n,4,4),observation=(n,2,4)),freq)
    return data,d,hashlib.sha256(raw).hexdigest()

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','training','validation','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();z,sha=load_source(a.source,a.scale)
    train,td,th=read_grid(a.training,'training',sha)
    selected,candidates=select(TRAIN,train,z);cfg=selected['config']
    C,opt=fit(TRAIN,train['impedance'],cfg);rep=audit(C,cfg);tr=score(TRAIN,train,C,cfg,z)
    a.out.mkdir(parents=True,exist_ok=True)
    archive=save_matrices(a.out,'baffle_passive_coefficients',frequencies=TRAIN,coefficients=C)
    frozen=dict(selected=selected,archive=archive,optimization=opt,passivity=rep,training=tr,
        sourceFrozenSha256=sha,trainingManifestSha256=th,trainingHz=TRAIN,plannedValidationHz=VALID)
    raw=json.dumps(frozen,indent=2,allow_nan=False).encode();(a.out/'frozen_passive.json').write_bytes(raw)
    # The validation data are first opened after coefficients are frozen.
    valid,vd,vh=read_grid(a.validation,'validation',sha)
    if any(td[k]!=vd[k] for k in ('previousManifestSha256','microphonesXYZ_m')):raise ValueError('grid mismatch')
    va=score(VALID,valid,C,cfg,z)
    fitgate=bool(selected['eligible'] and opt['converged'] and rep['gate'] and all(v['powerGate'] for v in tr+va)
        and max(selected['maximumInner'],maximum(tr),maximum(va))<=.05)
    summary=dict(gate=True,diagnosticOnly=True,fields=72,oneSidedIdealBaffle=True,selectedConfig=cfg,
        trainingPoints=12,validationPoints=6,selectionUsedValidation=False,maximumInnerError=selected['maximumInner'],
        trainingError=maximum(tr),validationError=maximum(va),optimizerGate=bool(selected['eligible'] and opt['converged']),
        passiveStructureGate=rep['gate'],fitGate=fitgate,physicalFitAccepted=False,causalObserverFitPerformed=False,
        continuousFrequencyValidated=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    (a.out/'baffle_passive_fit.json').write_text(json.dumps(dict(summary=summary,candidates=candidates,validation=va,
        frozenSha256=hashlib.sha256(raw).hexdigest(),validationManifestSha256=vh),indent=2,allow_nan=False))
    print('G3_BAFFLE_PASSIVE_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
