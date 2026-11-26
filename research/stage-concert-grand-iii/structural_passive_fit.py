"""G3.13a: passive impedance fitting in structural coordinates.
Retrospective 7-point screening only; not a certified fit or acoustic engine.
Select using training data, then check two already-known C4-neighbour samples."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import eigh
from acoustic_matrix_archive import read_npz
from wire_physical_midpoint import load
from wire_baffle_reference import FREQ,CONFIGS
from physical_unison_decay import detune
from modal_string_radiation import response
from baffle_passive_fit import fit,evaluate,audit,CONFIGS as OLD
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

TRAIN=[30.,150.,250.,261.63,300.]
CHECK=[261.4,261.86]
DICTIONARIES=[
    OLD[1],OLD[3],
    dict(relax=[15.,50.,150.,450.,1500.,5000.],osc=[30.,80.,130.,180.,230.,280.,350.,500.],gamma=35.,ridge=1e-6),
    dict(relax=[20.,80.,240.,800.,2400.],osc=[60.,120.,180.,220.,245.,280.,320.,400.],gamma=75.,ridge=1e-6)]

def structural_impedance(Z,B):
    return np.einsum('ai,fab,bj->fij',B,Z,B)

def subspace(Z):
    # Orthogonal congruence from training impedance only. Independently
    # normalize R and X so small resistance is not hidden by reactance.
    blocks=[]
    for z in Z:
        for a in (z.real,z.imag):
            norm=np.linalg.norm(a)
            if norm<=0:raise ValueError('empty impedance component')
            blocks.append(a/norm)
    H=sum(x@x.T for x in blocks)
    ev,U=eigh((H+H.T)/2)
    return U[:,::-1]

def project(Z,U):
    return np.einsum('ai,fab,bj->fij',U,Z,U)
def lift(C,U):
    return np.einsum('ia,lab,jb->lij',U,C,U)
def matrix_errors(Z,R):
    return [dict(impedance=relative(x,y),resistance=relative(x.real,y.real),reactance=relative(x.imag,y.imag)) for x,y in zip(Z,R)]
def worst(rows):
    return max(max(x[k] for k in ('impedance','resistance','reactance')) for x in rows)

def select_rank(Z,U):
    rows=[]
    for n in (8,16,24,32,48,64,80):
        n=min(n,U.shape[1])
        if any(x['rank']==n for x in rows):continue
        V=U[:,:n];r=matrix_errors(lift(project(Z,V),V),Z)
        rows.append(dict(rank=n,maximum=worst(r)))
    eligible=[x for x in rows if x['maximum']<=.01]
    return min(eligible,key=lambda x:x['rank']) if eligible else rows[-1],rows

def read_reference(root,sha):
    raw=(root/'wire_baffle_reference.json').read_bytes();d=json.loads(raw);s=d['summary']
    expected=dict(gate=True,reduced32Gate=True,fields=80,structureRank=80,wires=10,cases=35,
        coCoordinateSurface=True,oneSidedIdealBaffle=True,physicalAcousticFitAccepted=False)
    if d['sourceFrozenSha256']!=sha or any(s.get(k)!=v for k,v in expected.items()) or d['frequenciesHz']!=FREQ or d['configurations']!=[list(x) for x in CONFIGS]:
        raise ValueError('unapproved acoustic source')
    z=read_npz(root,d['archive'],dict(stiffness=(80,),damping=(80,80),ports=(80,7),wirePorts=(10,80),
        physicalLift=(1386,80),regionalDamping=(3,80,80),fieldMap=(80,80),fieldEigenvalues=(80,),fieldVectors=(80,80),
        impedance=(7,80,80),pressure=(7,2,80),mobility=(5,7,7,7),observation=(5,7,2,7)),FREQ)
    return z,hashlib.sha256(raw).hexdigest()

def contexts(z,wires,rows):
    out=[]
    for spread,factor in CONFIGS:
        ww,_=detune(wires,rows,spread)
        md=dict(M=np.eye(80),K=np.diag(z['stiffness']),D=z['damping']*factor,P=z['ports'])
        out.append((md,ww))
    return out

def score(z,Z,indices,ctx):
    B=z['fieldMap'];out=[]
    for i,j in enumerate(indices):
        f=FREQ[j];target=structural_impedance(z['impedance'][j:j+1],B)[0]
        e=matrix_errors(Z[i:i+1],target[None])[0];H=z['pressure'][j]@B
        cases=[]
        for c,(md,wires) in enumerate(ctx):
            Y,O,a=response(md,z['wirePorts'],wires,Z[i],H,f)
            case=dict(spreadCents=CONFIGS[c][0],structureFactor=CONFIGS[c][1],
                mobility=relative(Y,z['mobility'][c,j]),pressure=relative(O,z['observation'][c,j]),
                c4Pressure=relative(O[:,2],z['observation'][c,j,:,2]),powerGate=bool(a['gate']))
            cases.append(case)
        row=dict(frequencyHz=f,**e,cases=cases,maximumResponse=max(max(c[k] for k in ('mobility','pressure','c4Pressure')) for c in cases),
            powerGate=all(c['powerGate'] for c in cases))
        out.append(row)
    return out

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','reference','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();_,wires,sha=load(a.source,a.scale);z,rh=read_reference(a.reference,sha)
    rows={v['key']:v for v in json.loads(a.scale.read_text())['rows']};ctx=contexts(z,wires,rows)
    it=[FREQ.index(f) for f in TRAIN];ic=[FREQ.index(f) for f in CHECK]
    target=structural_impedance(z['impedance'][it],z['fieldMap']);U=subspace(target)
    chosen,ranks=select_rank(target,U);V=U[:,:chosen['rank']]
    # Verify source replay before fitting. Archived matrices and observers
    # are in the same structural coordinates; no cross-run column mixing.
    replay=score(z,target,it,ctx)
    if max(v['maximumResponse'] for v in replay)>1e-8 or not all(v['powerGate'] for v in replay):raise ValueError('reference replay')
    candidates=[];coeffs=[]
    for i,cfg in enumerate(DICTIONARIES):
        C,opt=fit(TRAIN,project(target,V),cfg,maxiter=2500)
        full=lift(C,V);rep=audit(full,cfg);Z=evaluate(2j*np.pi*np.asarray(TRAIN),full,cfg)
        tr=score(z,Z,it,ctx);matrix=worst(tr);resp=max(t['maximumResponse'] for t in tr)
        row=dict(index=i,config=cfg,optimizer=opt,passivity=rep,training=tr,
            trainingMatrixMaximum=matrix,trainingResponseMaximum=resp,
            eligible=bool(opt['converged'] and rep['gate'] and all(t['powerGate'] for t in tr)))
        candidates.append(row);coeffs.append(full)
        print('G3_STRUCTURAL_PASSIVE_CANDIDATE '+json.dumps({k:v for k,v in row.items() if k!='training'},allow_nan=False),flush=True)
    eligible=[x for x in candidates if x['eligible']]
    selected=min(eligible or candidates,key=lambda x:(max(x['trainingMatrixMaximum'],x['trainingResponseMaximum']),x['index']))
    C=coeffs[selected['index']];cfg=selected['config']
    a.out.mkdir(parents=True,exist_ok=True)
    entry=save_matrices(a.out,'structural_passive_coefficients',frequencies=TRAIN,coefficients=C,projection=V)
    frozen=dict(selected=selected,rankSelection=chosen,rankCandidates=ranks,archive=entry,sourceFrozenSha256=sha,
        referenceManifestSha256=rh,trainingHz=TRAIN,plannedCheckHz=CHECK,retrospectiveCheck=True)
    b=json.dumps(frozen,indent=2,allow_nan=False).encode();(a.out/'frozen_structural_passive.json').write_bytes(b)
    # Held-out for optimization only, not novel external validation.
    check=score(z,evaluate(2j*np.pi*np.asarray(CHECK),C,cfg),ic,ctx)
    cm=worst(check);cr=max(x['maximumResponse'] for x in check)
    gate=bool(selected['eligible'] and all(x['powerGate'] for x in check) and
        max(selected['trainingMatrixMaximum'],selected['trainingResponseMaximum'],cm,cr)<=.05)
    summary=dict(gate=True,screeningFitGate=gate,diagnosticOnly=True,physicalHypothesis=True,
        calibratedParameters=False,structureRank=80,fitRank=chosen['rank'],trainingPoints=len(TRAIN),checkPoints=len(CHECK),
        selectionUsedCheck=False,checkPreviouslyObserved=True,selectedIndex=selected['index'],
        optimizationGate=selected['optimizer']['converged'],passivityGate=selected['passivity']['gate'],
        trainingMatrixMaximum=selected['trainingMatrixMaximum'],trainingResponseMaximum=selected['trainingResponseMaximum'],
        checkMatrixMaximum=cm,checkResponseMaximum=cr,maximumReferenceReplay=max(v['maximumResponse'] for v in replay),
        physicalAcousticFitAccepted=False,continuousFrequencyValidated=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    (a.out/'structural_passive_fit.json').write_text(json.dumps(dict(summary=summary,candidates=candidates,check=check,
        frozenSha256=hashlib.sha256(b).hexdigest(),sourceFrozenSha256=sha,referenceManifestSha256=rh),indent=2,allow_nan=False))
    print('G3_STRUCTURAL_PASSIVE_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
