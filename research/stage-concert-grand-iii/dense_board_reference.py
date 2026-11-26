"""Assemble a fixed split from approved full-reference evidence only."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from acoustic_matrix_archive import read_npz
from fixed_355_validation import require_fine,valid_metrics
from frozen_basis_replay import require_120
from dense_frequency_batch import BATCHES,grid_check,FREQ
from dual_cavity_spatial_diagnostic import save_matrices
from high_modal_allocation import read
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry

def require_batch(d,angle,sha,batch,basis_sha):
    s=d.get('summary',{});f=list(BATCHES[batch])
    expected=dict(gate=True,angleDeg=angle,diagnosticOnly=True,batch=batch,referenceModes=385,reducedModes=120,frozenBasis=True,
        fitRole=('training' if batch==0 else 'validation'),basisTrainingFrequencies=FREQ,approvedReactiveBlocks=28,
        continuousFrequencyValidated=False,modalConvergenceCertified=False,timeDomainReady=False,radiationReady=False)
    if d.get('scaleSha256')!=sha or d.get('frequenciesHz')!=f or d.get('basisManifestSha256')!=basis_sha or any(s.get(k)!=v for k,v in expected.items()):
        raise ValueError('invalid batch provenance')
    if s.get('reductionGate') is not valid_metrics(s.get('maximum',{})):raise ValueError('inconsistent reduction evidence')
    rows=d.get('reactive',[])
    if [(v.get('panel'),v.get('otherPanel')) for v in rows]!=[(i,j) for i in range(7) for j in range(i,7)] or not all(v.get('gate') is True for v in rows):
        raise ValueError('invalid reactive evidence')
    for key in ('smooth','reports'):
        rows=d.get(key,[])
        if [v.get('frequencyHz') for v in rows]!=f:raise ValueError('missing frequency evidence')
        if key=='smooth' and not all(v.get('gate') is True for v in rows):raise ValueError('unapproved smooth operator')
        if key=='reports' and not all(all(v.get(k,{}).get('gate') is True for k in ('upper','lower','coupled')) for v in rows):raise ValueError('unapproved solve')

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','fine','basis','batch0','batch1','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    grid_check();raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw)
    d=json.loads((a.fine/'graded_combined_refinement.json').read_text());require_fine(d,a.angle,sha)
    basisraw=(a.basis/'common_snapshot_transfer.json').read_bytes();require_120(json.loads(basisraw),a.angle,sha)
    bsha=hashlib.sha256(basisraw).hexdigest()
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    nm=len(geometry(np.asarray(q['contourXY_m']),l,read('cabinet_geometry_hypothesis.json'))['microphonesXYZ_m'])
    nf=len(FREQ);z=read_npz(a.fine,d['archive'],dict(Zu=(nf,334,334),Pu=(nf,nm,334),Y=(nf,4,4),flow=(nf,385,4)),FREQ)['Y']
    samples={f:v for f,v in zip(FREQ,z)};hashes=[];gates=[]
    for i,root in enumerate((a.batch0,a.batch1)):
        raw=(root/'dense_frequency_batch.json').read_bytes();d=json.loads(raw)
        require_batch(d,a.angle,sha,i,bsha);f=list(BATCHES[i]);n=len(f)
        z=read_npz(root,d['archive'],dict(Zu=(n,334,334),Pu=(n,nm,334),Zl=(n,59,59),Pl=(n,2,59),Ze=(n,385,385),Pe=(n,2,385),Y=(n,4,4),flow=(n,385,4)),f)['Y']
        samples.update(zip(f,z));hashes.append(hashlib.sha256(raw).hexdigest());gates.append(d['summary']['reductionGate'])
    train=sorted([*FREQ,*BATCHES[0]]);valid=list(BATCHES[1]);freq=sorted(samples)
    if set(train)&set(valid) or set(train+valid)!=set(freq):raise ValueError('invalid split')
    a.out.mkdir(parents=True,exist_ok=True)
    archive=save_matrices(a.out,'dense_board_reference',frequencies=freq,Y=np.stack([samples[f] for f in freq]))
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,referenceModes=385,trainingHz=train,validationHz=valid,
        newPointCount=12,referencePointCount=len(freq),reductionBatchGates=gates,fitNotPerformed=True,
        continuousFrequencyValidated=False,timeDomainReady=False,radiationReady=False)
    (a.out/'dense_board_reference.json').write_text(json.dumps(dict(summary=summary,archive=archive,scaleSha256=sha,
        frequenciesHz=freq,batchManifestSha256=hashes),indent=2,allow_nan=False))
    print('G3_DENSE_REFERENCE_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
