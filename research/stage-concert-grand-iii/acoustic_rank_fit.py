"""G3.14b: separate spatial rank error from passive rational fit error.
Retrospective screening only. No integration into the sound engine."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from wire_physical_midpoint import load
from structural_passive_fit import read_reference,contexts,structural_impedance,subspace,project,lift,worst,DICTIONARIES
from response_weighted_fit import read_group,merge,score,response_gram,weight
from new_baffle_grid import DEVELOPMENT,RESERVED,EXTENSION
from baffle_passive_fit import fit,evaluate,audit
from dual_cavity_spatial_diagnostic import save_matrices

def projected_target(target,U,rank):
    if not 1<=rank<=U.shape[1]:raise ValueError('rank')
    V=U[:,:rank]
    return lift(project(target,V),V)

def metrics(rows):
    return dict(matrixMaximum=worst(rows),responseMaximum=max(r['maximumResponse'] for r in rows),
                powerGate=all(r['powerGate'] for r in rows))

def objective(row):
    return max(row['matrixMaximum'],row['responseMaximum'])

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','reference','grid','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();_,wires,sha=load(a.source,a.scale);z,rh=read_reference(a.reference,sha)
    dev,dh=read_group(a.grid,'development',DEVELOPMENT,sha,rh);freq,data=merge(z,dev)
    target=structural_impedance(data['impedance'],z['fieldMap'])
    ctx=contexts(z,wires,{v['key']:v for v in json.loads(a.scale.read_text())['rows']})
    U=subspace(target);replay=metrics(score(freq,data,z,target,ctx))
    if objective(replay)>1e-8 or not replay['powerGate']:raise ValueError('reference replay')
    spatial=[]
    for rank in (32,48,64,72,80):
        row=dict(rank=rank,**metrics(score(freq,data,z,projected_target(target,U,rank),ctx)))
        spatial.append(row);print('G3_ACOUSTIC_SPATIAL '+json.dumps(row,allow_nan=False),flush=True)
    if objective(spatial[-1])>1e-8:raise ValueError('full rank replay')
    # Repeat the previously tested dictionary at both ranks. One additional
    # candidate increases the range of relaxation/oscillator time constants.
    cfgs=[DICTIONARIES[2],dict(relax=[5.,15.,45.,135.,405.,1215.,3645.,10935.],
        osc=[25.,40.,60.,85.,110.,140.,175.,210.,240.,260.,280.,310.,360.,430.,520.,700.],gamma=20.,ridge=1e-6)]
    candidates=[];coeffs=[]
    for rank,dictionary,strength in [(64,0,15.),(80,0,15.),(80,0,0.),(80,1,15.)]:
        V=U[:,:rank];Q=project(target,V);G=response_gram(freq,target,ctx,z['wirePorts'],V)
        T,I=weight(G,strength);cfg=cfgs[dictionary]
        C,opt=fit(freq,project(Q,T),cfg,maxiter=4000)
        full=lift(lift(C,I),V);rep=audit(full,cfg)
        tr=score(freq,data,z,evaluate(2j*np.pi*freq,full,cfg),ctx)
        row=dict(index=len(candidates),rank=rank,dictionary=dictionary,strength=strength,config=cfg,
            optimization=opt,passivity=rep,**metrics(tr),training=tr)
        row['eligible']=bool(opt['converged'] and rep['gate'] and row['powerGate'])
        candidates.append(row);coeffs.append(full)
        print('G3_ACOUSTIC_RANK_FIT '+json.dumps({k:v for k,v in row.items() if k!='training'},allow_nan=False),flush=True)
    eligible=[v for v in candidates if v['eligible']]
    chosen=min(eligible or candidates,key=lambda v:(objective(v),v['index']))
    C=coeffs[chosen['index']];cfg=chosen['config'];a.out.mkdir(parents=True,exist_ok=True)
    entry=save_matrices(a.out,'rank_fit_coefficients',frequencies=freq,coefficients=C)
    frozen=dict(selected=chosen,archive=entry,trainingHz=freq.tolist(),sourceFrozenSha256=sha,
        referenceManifestSha256=rh,developmentManifestSha256=dh)
    raw=json.dumps(frozen,indent=2,allow_nan=False).encode()
    (a.out/'frozen_acoustic_rank_fit.json').write_bytes(raw)
    checks={};hashes={}
    for role,fs in [('reserved',RESERVED),('extension',EXTENSION)]:
        d,h=read_group(a.grid,role,fs,sha,rh);hashes[role]=h
        checks[role]=score(fs,d,z,evaluate(2j*np.pi*np.asarray(fs),C,cfg),ctx)
    reserve=metrics(checks['reserved']);ext=metrics(checks['extension'])
    summary=dict(gate=True,screeningFitGate=bool(chosen['eligible'] and reserve['powerGate'] and max(objective(chosen),objective(reserve))<=.05),
        extensionGate=bool(ext['powerGate'] and objective(ext)<=.05),diagnosticOnly=True,
        selectedIndex=chosen['index'],selectedRank=chosen['rank'],trainingMaximum=objective(chosen),
        reservedMaximum=objective(reserve),extensionMaximum=objective(ext),spatial=spatial,
        selectedUsingChecks=False,checksPreviouslyObserved=True,physicalAcousticFitAccepted=False,
        continuousFrequencyValidated=False,timeDomainReady=False,polyphonyValidated=False,
        frozenSha256=hashlib.sha256(raw).hexdigest(),checkManifestSha256=hashes)
    (a.out/'acoustic_rank_fit.json').write_text(json.dumps(dict(summary=summary,candidates=candidates,checks=checks),indent=2,allow_nan=False))
    print('G3_ACOUSTIC_RANK_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
