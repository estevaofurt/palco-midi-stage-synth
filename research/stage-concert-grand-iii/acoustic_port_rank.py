"""G3.14d.8: select acoustic port rank from local harmonic responses.
No temporal kernel generation, feedback or calibration. All bases are local.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from wire_physical_midpoint import load
from structural_region_decay import rebuild
from retarded_local_reference import geometry
from new_baffle_grid import kernel
from projected_board_cq import bridge_ports,harmonic
from modal_string_radiation import response
from mode_selective_loss import mode_loss
from unison_profiles import KEYS,profiles_for_key,detune_profile
from structural_passive_fit import matrix_errors,subspace
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

TRAIN=(30.,110.,150.,261.63,400.)
CHECK=(72.,130.81,194.,258.,329.63,500.)
RANKS=(4,8,12,16,24,32,48,64,80)

def basis(B,blocks):
    Q,sv,_=np.linalg.svd(B,full_matrices=True)
    p=B.shape[1]
    if sv[-1]<=1e-8*sv[0]:raise ValueError('bridge rank')
    fixed=Q[:,:p];rest=Q[:,p:]
    if rest.shape[1]==0:return fixed
    data=[]
    for a in blocks:
        a=np.asarray(a)
        for x in (a.real,a.imag) if np.iscomplexobj(a) else (a,):
            if np.linalg.norm(x)>1e-30:data.append(rest.T@x/np.linalg.norm(x))
    if not data:raise ValueError('empty training blocks')
    W,_,_=np.linalg.svd(np.concatenate(data,axis=1),full_matrices=True)
    U=np.column_stack([fixed,rest@W])
    if relative(U.T@U,np.eye(len(U)))>1e-10:raise ValueError('orthogonality')
    return U

def projected(Z,U):
    return U@(U.T@Z@U)@U.T

def wire_velocity(md,A,wires,Z,f):
    s=2j*np.pi*f;w=2*np.pi*f
    L=md['K']+s*s*md['M']+s*(md['D']+Z);rhs=md['P'].astype(complex)
    for a,wire in zip(A,wires):
        z,g,_,_,_=wire.condense(w)
        L+=z*np.outer(a,a);rhs[:,wire.port]+=g*a
    return s*np.linalg.solve(L,rhs)

def reference(f,k,D,P,A,B,ctx,geom):
    T,_,quad,grids,mic,_=geom
    Z,H,audit=kernel(f,grids,quad,mic)
    if not audit['gate']:raise ValueError('reference grid '+str(audit))
    Z=T.T@Z@T;H=H@T
    Y,V=harmonic(k,D,B,Z,f);_,dry=harmonic(k,D,B,np.zeros_like(Z),f)
    notes=[]
    for j,ww in enumerate(ctx):
        md=dict(M=np.eye(len(k)),K=np.diag(k),D=D,P=P)
        yy,oo,rep=response(md,A,ww,Z,H,f)
        if not rep['gate']:raise ValueError('reference wire algebra')
        vv=wire_velocity(md,A,ww,Z,f)
        if relative(H@vv,oo)>1e-8:raise ValueError('wire state replay')
        notes.append((yy[:,j],oo[:,j],vv[:,j:j+1]))
    return dict(f=f,Z=Z,H=H,Y=Y,V=V,dry=dry,notes=notes,grid=audit)

def assess(ref,U,k,D,P,A,B,ctx):
    f=ref['f'];Z=projected(ref['Z'],U)
    Y,V=harmonic(k,D,B,Z,f)
    md=dict(M=np.eye(len(k)),K=np.diag(k),D=D,P=P)
    cases=[]
    for j,ww in enumerate(ctx):
        y,o,a=response(md,A,ww,Z,ref['H'],f)
        yr,orr,vr=ref['notes'][j]
        v=wire_velocity(md,A,ww,Z,f)[:,j:j+1]
        cases.append(dict(key=KEYS[j],mobility=relative(y[:,j],yr),pressure=relative(o[:,j],orr),
            state=relative(v,vr),powerGate=bool(a['gate'])))
    board=dict(mobility=relative(Y,ref['Y']),state=relative(V,ref['V']))
    matrix=matrix_errors(Z[None],ref['Z'][None])[0]
    maximum=max(*board.values(),*(max(c[t] for t in ('mobility','pressure','state')) for c in cases))
    return dict(frequencyHz=f,board=board,notes=cases,matrix=matrix,maximumResponse=maximum,
        powerGate=all(v['powerGate'] for v in cases))

def summarize(rows):
    return dict(maximumResponse=max(x['maximumResponse'] for x in rows),
        maximumMatrix=max(max(x['matrix'].values()) for x in rows),
        powerGate=all(x['powerGate'] for x in rows))

def main():
    p=argparse.ArgumentParser()
    for name in ('scale','source','surface','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();archive,wires,sha=load(a.source,a.scale);local={}
    def sink(plate,poly,lift):local.update(plate=plate,poly=poly,lift=lift)
    k,D,P,A,wires,G,lift,replay=rebuild(a.scale,a.surface,archive,wires,surface_sink=sink)
    geom=geometry(local['plate'],local['poly'],local['lift'])
    B=bridge_ports(A,wires);rows={v['key']:v for v in json.loads(a.scale.read_text())['rows']}
    ctx=[]
    for key in KEYS:
        ww,_=detune_profile(wires,rows,profiles_for_key(key)[0][1]);ctx.append(mode_loss(ww,4.,2. if key==64 else 4.))
    train=[reference(f,k,D,P,A,B,ctx,geom) for f in TRAIN]
    snapshots=[x for r in train for x in (r['V'],r['dry'],*(v[2] for v in r['notes']))]
    operators=[x for r in train for x in (r['Z'].real,r['Z'].imag)]
    bases=dict(portState=basis(B,snapshots),portStateAndImpedance=basis(B,snapshots+operators),impedance=subspace(np.stack([r['Z'] for r in train])))
    candidates=[]
    for name,U in bases.items():
        for n in RANKS:
            records=[assess(ref,U[:,:n],k,D,P,A,B,ctx) for ref in train]
            row=dict(method=name,rank=n,**summarize(records),training=records)
            candidates.append(row)
            print('G3_ACOUSTIC_PORT_RANK '+json.dumps({x:y for x,y in row.items() if x!='training'},allow_nan=False),flush=True)
    eligible=[v for v in candidates if v['powerGate'] and v['maximumResponse']<=.05]
    if not eligible:raise ValueError('even full rank fails')
    chosen=min(eligible,key=lambda v:(v['rank'],v['maximumResponse'],v['method']))
    U=bases[chosen['method']][:,:chosen['rank']]
    a.out.mkdir(parents=True,exist_ok=True)
    entry=save_matrices(a.out,'acoustic_port_rank',frequencies=list(TRAIN),projection=U)
    frozen=dict(selected=chosen,archive=entry,trainingHz=TRAIN,checkHz=CHECK,sourceFrozenSha256=sha)
    raw=json.dumps(frozen,indent=2,allow_nan=False).encode();(a.out/'frozen_acoustic_port_rank.json').write_bytes(raw)
    checks=[assess(reference(f,k,D,P,A,B,ctx,geom),U,k,D,P,A,B,ctx) for f in CHECK]
    check=summarize(checks)
    summary=dict(gate=True,screeningGate=bool(check['powerGate'] and check['maximumResponse']<=.05),
        diagnosticOnly=True,selectedMethod=chosen['method'],selectedRank=chosen['rank'],
        trainingMaximum=chosen['maximumResponse'],checkMaximum=check['maximumResponse'],
        candidateCount=len(candidates),trainingPoints=len(TRAIN),checkPoints=len(CHECK),
        selectionUsedCheck=False,checkIsIndependentPhysicalMeasurement=False,temporalKernelGenerated=False,
        physicalFeedbackAccepted=False,polyphonyValidated=False,audibleSustainMeasured=False,
        sourceFrozenSha256=sha,frozenSha256=hashlib.sha256(raw).hexdigest())
    (a.out/'acoustic_port_rank.json').write_text(json.dumps(dict(summary=summary,candidates=candidates,checks=checks,geometry=geom[-1]),indent=2,allow_nan=False))
    print('G3_ACOUSTIC_PORT_RANK_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
