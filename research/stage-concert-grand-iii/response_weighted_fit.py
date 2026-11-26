"""G3.13c: response-aware passive impedance screening.
Train only on existing seven-point reference and new development grid.
Congruence emphasizes structural directions excited by wire force ports.
Never use reserved grid to select a model; no physical approval."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import eigh,solve
from structural_passive_fit import read_reference,contexts,structural_impedance,subspace,project,lift,select_rank,matrix_errors,worst,DICTIONARIES
from wire_baffle_reference import FREQ
from new_baffle_grid import DEVELOPMENT,RESERVED,EXTENSION
from wire_physical_midpoint import load
from modal_string_radiation import response
from baffle_passive_fit import fit,evaluate,audit
from acoustic_matrix_archive import read_npz
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

def read_group(root,role,freq,sha,rh):
    raw=(root/('new_baffle_'+role+'.json')).read_bytes();d=json.loads(raw);s=d['summary']
    if d['sourceFrozenSha256']!=sha or d['referenceManifestSha256']!=rh or d['frequenciesHz']!=freq or s['gate'] is not True or s['role']!=role or not all(v['kernel']['gate'] for v in d['cases']):
        raise ValueError('unapproved '+role+' reference')
    n=len(freq)
    z=read_npz(root,d['archive'],dict(impedance=(n,80,80),pressure=(n,2,80),mobility=(5,n,7,7),observation=(5,n,2,7)),freq)
    return z,hashlib.sha256(raw).hexdigest()

def merge(z,d):
    f=np.asarray(FREQ+DEVELOPMENT);ix=np.argsort(f)
    out={k:np.concatenate([z[k],d[k]],axis=0)[ix] for k in ('impedance','pressure')}
    out.update({k:np.concatenate([z[k],d[k]],axis=1)[:,ix] for k in ('mobility','observation')})
    return f[ix],out

def states(md,A,wires,Z,f):
    w=2*np.pi*f
    H=md['K']-w*w*md['M']+1j*w*(md['D']+Z);R=md['P'].astype(complex)
    for a,b in zip(A,wires):
        z,g,_,_,_=b.condense(w)
        H+=z*np.outer(a,a);R[:,b.port]+=g*a
    return 1j*w*solve(H,R)

def response_gram(freq,Z,ctx,A,V):
    G=np.zeros((V.shape[1],V.shape[1]));count=0
    for f,z in zip(freq,Z):
        for md,wires in ctx:
            q=V.T@states(md,A,wires,z,f)
            for col in q.T:
                norm=float(np.vdot(col,col).real)
                if norm>1e-30:
                    G+=np.outer(col,col.conj()).real/norm;count+=1
    if count==0:raise ValueError('empty response directions')
    return G/count

def weight(G,strength):
    if strength<0 or not np.isfinite(strength):raise ValueError('strength')
    e,U=eigh((G+G.T)/2)
    if e[-1]<=0 or e[0]<-1e-10*e[-1]:raise ValueError('gram')
    d=np.sqrt(1+strength*np.maximum(e,0)/e[-1])
    T=(U*d)@U.T;I=(U/d)@U.T
    if relative(T@I,np.eye(len(T)))>1e-12:raise ValueError('weight inverse')
    return T,I

def score(freq,data,z,Z,ctx):
    B=z['fieldMap'];target=structural_impedance(data['impedance'],B);out=[]
    for i,(f,x,y) in enumerate(zip(freq,Z,target)):
        e=matrix_errors(x[None],y[None])[0];H=data['pressure'][i]@B;cases=[]
        for j,(md,wires) in enumerate(ctx):
            Y,O,a=response(md,z['wirePorts'],wires,x,H,float(f))
            cases.append(dict(config=j,mobility=relative(Y,data['mobility'][j,i]),pressure=relative(O,data['observation'][j,i]),
                c4Pressure=relative(O[:,2],data['observation'][j,i,:,2]),powerGate=bool(a['gate'])))
        out.append(dict(frequencyHz=float(f),**e,cases=cases,
            maximumResponse=max(max(v[k] for k in ('mobility','pressure','c4Pressure')) for v in cases),
            powerGate=all(v['powerGate'] for v in cases)))
    return out

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','reference','grid','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();_,wires,sha=load(a.source,a.scale);z,rh=read_reference(a.reference,sha)
    dev,dh=read_group(a.grid,'development',DEVELOPMENT,sha,rh);freq,data=merge(z,dev)
    target=structural_impedance(data['impedance'],z['fieldMap'])
    ctx=contexts(z,wires,{x['key']:x for x in json.loads(a.scale.read_text())['rows']})
    replay=score(freq,data,z,target,ctx)
    if max(x['maximumResponse'] for x in replay)>1e-8 or not all(x['powerGate'] for x in replay):raise ValueError('reference replay')
    # All prior points now development, including former retrospective check.
    U=subspace(target);rank,rankRows=select_rank(target,U);V=U[:,:rank['rank']]
    Q=project(target,V);G=response_gram(freq,target,ctx,z['wirePorts'],V)
    candidates=[];coeffs=[]
    # Fixed candidates: no tuning on reserved samples.
    dictionaries=[DICTIONARIES[2],dict(relax=[10.,30.,90.,270.,810.,2430.,7290.],
        osc=[25.,50.,75.,100.,125.,150.,175.,200.,225.,250.,275.,300.,350.,450.,600.],gamma=30.,ridge=1e-6)]
    for j,cfg in enumerate(dictionaries):
        for strength in (0.,3.,15.):
            T,I=weight(G,strength)
            C,opt=fit(freq,project(Q,T),cfg,maxiter=4000)
            full=lift(lift(C,I),V);rep=audit(full,cfg)
            tr=score(freq,data,z,evaluate(2j*np.pi*freq,full,cfg),ctx)
            row=dict(index=len(candidates),dictionary=j,strength=strength,config=cfg,rank=rank['rank'],
                matrixMaximum=worst(tr),responseMaximum=max(v['maximumResponse'] for v in tr),
                optimization=opt,passivity=rep,training=tr,
                eligible=bool(opt['converged'] and rep['gate'] and all(v['powerGate'] for v in tr)))
            candidates.append(row);coeffs.append(full)
            print('G3_RESPONSE_WEIGHTED_CANDIDATE '+json.dumps({k:v for k,v in row.items() if k!='training'},allow_nan=False),flush=True)
    eligible=[v for v in candidates if v['eligible']]
    sel=min(eligible or candidates,key=lambda v:(max(v['matrixMaximum'],v['responseMaximum']),v['index']))
    C=coeffs[sel['index']];cfg=sel['config'];a.out.mkdir(parents=True,exist_ok=True)
    desc=save_matrices(a.out,'response_weighted_coefficients',frequencies=freq,coefficients=C,projection=V,responseGram=G)
    frozen=dict(selected=sel,archive=desc,rankCandidates=rankRows,trainingHz=freq.tolist(),reservedHz=RESERVED,
        sourceFrozenSha256=sha,referenceManifestSha256=rh,developmentManifestSha256=dh)
    raw=json.dumps(frozen,indent=2,allow_nan=False).encode();(a.out/'frozen_response_weighted.json').write_bytes(raw)
    reserved,vh=read_group(a.grid,'reserved',RESERVED,sha,rh)
    check=score(RESERVED,reserved,z,evaluate(2j*np.pi*np.asarray(RESERVED),C,cfg),ctx)
    cm=worst(check);cr=max(v['maximumResponse'] for v in check)
    summary=dict(gate=True,screeningFitGate=bool(sel['eligible'] and all(v['powerGate'] for v in check) and
        max(sel['matrixMaximum'],sel['responseMaximum'],cm,cr)<=.05),diagnosticOnly=True,calibratedParameters=False,
        selectedIndex=sel['index'],selectedStrength=sel['strength'],fitRank=rank['rank'],trainingPoints=len(freq),reservedPoints=len(RESERVED),
        trainingMatrixMaximum=sel['matrixMaximum'],trainingResponseMaximum=sel['responseMaximum'],reservedMatrixMaximum=cm,reservedResponseMaximum=cr,
        selectionUsedReserved=False,reservedPreviouslyObservedForOlderFit=True,passivityGate=sel['passivity']['gate'],
        optimizerGate=sel['optimization']['converged'],physicalAcousticFitAccepted=False,
        continuousFrequencyValidated=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    (a.out/'response_weighted_fit.json').write_text(json.dumps(dict(summary=summary,candidates=candidates,reserved=check,
        frozenSha256=hashlib.sha256(raw).hexdigest(),reservedManifestSha256=vh),indent=2,allow_nan=False))
    print('G3_RESPONSE_WEIGHTED_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
