"""G3.14d.11: conservative, fixed rank64 impedance projection.
Rebuild locally and freeze coordinates with the candidate. No CQ or feedback.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from wire_physical_midpoint import load
from structural_region_decay import rebuild
from retarded_local_reference import geometry
from projected_board_cq import bridge_ports
from acoustic_port_rank import TRAIN,CHECK,reference,assess,summarize
from structural_passive_fit import subspace
from unison_profiles import KEYS,profiles_for_key,detune_profile
from mode_selective_loss import mode_loss
from dual_cavity_spatial_diagnostic import save_matrices
from split_radiation import relative

# Fixed after rank32 failure; never search ranks using these checks.
RANK=64
NOVEL=(105.,109.7,110.3,130.5,131.1,260.9,262.3,329.3,330.,475.)
MATRIX_LIMIT=.01
RESPONSE_LIMIT=.05

def eligible(s):
    return bool(s['powerGate'] and s['maximumMatrix']<=MATRIX_LIMIT and s['maximumResponse']<=RESPONSE_LIMIT)

def freeze_projection(Z,rank=RANK):
    U=subspace(Z)[:,:rank]
    if U.shape[1]!=rank or relative(U.T@U,np.eye(rank))>1e-10:raise ValueError('invalid frozen projection')
    return U

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','source','surface','out'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();archive,wires,sha=load(a.source,a.scale);local={}
    def sink(plate,poly,lift):local.update(plate=plate,poly=poly,lift=lift)
    k,D,P,A,wires,G,lift,replay=rebuild(a.scale,a.surface,archive,wires,surface_sink=sink)
    geom=geometry(local['plate'],local['poly'],local['lift'])
    B=bridge_ports(A,wires);rows={v['key']:v for v in json.loads(a.scale.read_text())['rows']}
    ctx=[]
    for key in KEYS:
        ww,_=detune_profile(wires,rows,profiles_for_key(key)[0][1]);ctx.append(mode_loss(ww,4.,2. if key==64 else 4.))
    train=[reference(f,k,D,P,A,B,ctx,geom) for f in TRAIN]
    U=freeze_projection(np.stack([v['Z'] for v in train]))
    trainrows=[assess(v,U,k,D,P,A,B,ctx) for v in train]
    tr=summarize(trainrows)
    a.out.mkdir(parents=True,exist_ok=True)
    # The lift and all operators are saved together; future calculations
    # must rebuild and verify the coordinate identity or repeat this step.
    entry=save_matrices(a.out,'fixed_acoustic_projection',frequencies=list(TRAIN),projection=U,
        stiffness=k,damping=D,ports=P,wirePorts=A,physicalLift=lift,regionalDamping=G,
        fieldMap=geom[0],trainingImpedance=np.stack([v['Z'] for v in train]),
        trainingPressure=np.stack([v['H'] for v in train]))
    frozen=dict(rank=RANK,method='impedance',trainingHz=TRAIN,priorCheckHz=CHECK,additionalCheckHz=NOVEL,
        training=tr,trainingGate=eligible(tr),sourceFrozenSha256=sha,archive=entry,
        wireIds=[w.id for w in wires],geometryAudit=geom[-1],limits=dict(matrix=MATRIX_LIMIT,response=RESPONSE_LIMIT))
    raw=json.dumps(frozen,indent=2,allow_nan=False).encode()
    (a.out/'frozen_acoustic_projection.json').write_bytes(raw)
    checks={}
    for name,fs in [('priorCheck',CHECK),('additionalCheck',NOVEL)]:
        rec=[]
        for f in fs:
            ref=reference(f,k,D,P,A,B,ctx,geom)
            row=assess(ref,U,k,D,P,A,B,ctx);rec.append(row)
            print('G3_FIXED_ACOUSTIC_CHECK '+json.dumps(dict(group=name,**row),allow_nan=False),flush=True)
        checks[name]=dict(summary=summarize(rec),rows=rec)
    summary=dict(gate=True,screeningGate=bool(eligible(tr) and all(eligible(v['summary']) for v in checks.values())),
        rank=RANK,method='impedance',training=tr,priorCheck=checks['priorCheck']['summary'],
        additionalCheck=checks['additionalCheck']['summary'],selectionUsedCheck=False,
        rankChosenAfterPriorRank32Failure=True,independentPhysicalMeasurement=False,
        diagnosticOnly=True,temporalKernelGenerated=False,feedbackIntegrated=False,
        audibleSustainMeasured=False,sourceFrozenSha256=sha,frozenSha256=hashlib.sha256(raw).hexdigest())
    (a.out/'fixed_acoustic_projection.json').write_text(json.dumps(dict(summary=summary,training=trainrows,checks=checks),indent=2,allow_nan=False))
    print('G3_FIXED_ACOUSTIC_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
