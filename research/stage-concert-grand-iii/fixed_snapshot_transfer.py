"""G3.11b: freeze a snapshot basis on the coarse mesh, transfer it
to a separately refined upper mesh. Never tune against fine evidence."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from acoustic_matrix_archive import read_npz,replay_full,modal_replay
from graded_reference_audit import require_graded
from high_modal_allocation import require_archive
from dual_cavity_spatial_diagnostic import FREQ,compare_spatial,save_matrices
from fixed_355_validation import require_fine,valid_metrics
from snapshot_reduction import snapshot_bases,RANKS

def require_snapshot(d,angle,sha):
    s=d.get('summary',{});rows=d.get('cases',[])
    expected=dict(gate=True,angleDeg=angle,diagnosticOnly=True,referenceModes=385,leaveOneFrequencyOut=True,
        reductionGate=True,independentGeometryValidated=False,continuousFrequencyValidated=False,
        timeDomainReady=False,modalConvergenceCertified=False,radiationReady=False)
    if d.get('scaleSha256')!=sha or d.get('frequenciesHz')!=FREQ or any(s.get(k)!=v for k,v in expected.items()) or [r.get('rankLimit') for r in rows]!=list(RANKS):
        raise ValueError('invalid or unapproved snapshot evidence')
    good=[]
    for row in rows:
        folds=row.get('folds',[]);rank=row['rankLimit']
        if [f.get('heldOutHz') for f in folds]!=FREQ:raise ValueError('missing frequency folds')
        for f in folds:
            if f.get('trainingHz')!=[x for x in FREQ if x!=f['heldOutHz']] or len(f.get('counts',[]))!=7 or any(type(n)!=int or not 1<=n<=rank for n in f['counts']):
                raise ValueError('invalid training folds')
        if row.get('maximumModes')!=max(sum(f['counts']) for f in folds):raise ValueError('wrong dimension')
        gate=valid_metrics(row.get('comparison',{}).get('maximum',{}))
        if row.get('gate') is not gate or row['comparison'].get('gate') is not gate:raise ValueError('inconsistent fold gate')
        if gate:good.append(row)
    if not good:raise ValueError('no approved rank')
    best=min(good,key=lambda v:(v['maximumModes'],v['rankLimit']))
    if s.get('provisionalRank')!=best['rankLimit'] or s.get('provisionalModes')!=best['maximumModes']:raise ValueError('selection mismatch')
    return best['rankLimit']

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','archive','consolidated','graded','fine','snapshot','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    sha=hashlib.sha256(a.scale.read_bytes()).hexdigest()
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    gd=json.loads((a.graded/'graded_cavity_replay.json').read_text());require_graded(gd,a.angle,sha)
    fine=json.loads((a.fine/'graded_combined_refinement.json').read_text());require_fine(fine,a.angle,sha)
    rank=require_snapshot(json.loads((a.snapshot/'snapshot_reduction.json').read_text()),a.angle,sha)
    ext=json.loads((a.consolidated/'consolidated_exterior.json').read_text());s=ext['summary']
    if ext['scaleSha256']!=sha or ext['frequenciesHz']!=FREQ or not s['gate'] or s['angleDeg']!=a.angle or s['approvedBlocks']!=28 or s['radiationReady']:
        raise ValueError('invalid exterior')
    nf=len(FREQ)
    sh=read_npz(a.archive,doc['shared'],dict(areas=(7,),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385)),FREQ)
    # Observer count is fixed by archived cabinet geometry; inspect metadata from
    # geometry definition, not a guess or untrusted matrix shape.
    from high_modal_allocation import read
    from spatial_layout import build as layout_build
    from board_contour import build as contour_build
    from cabinet_geometry import geometry
    sc=json.loads(a.scale.read_text());l=layout_build(sc,read('layout_hypothesis.json'))
    q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    nm=len(geometry(np.asarray(q['contourXY_m']),l,read('cabinet_geometry_hypothesis.json'))['microphonesXYZ_m'])
    shapes=dict(Zu=(nf,334,334),Pu=(nf,nm,334),Y=(nf,4,4),flow=(nf,385,4))
    coarse=read_npz(a.graded,gd['archive'],shapes,FREQ);ref=read_npz(a.fine,fine['archive'],shapes,FREQ)
    ex=read_npz(a.consolidated,ext['archive'],dict(Ze=(nf,385,385),Y=(nf,4,4),flow=(nf,385,4)),FREQ)
    if not np.array_equal(ex['Ze'].real,sh['Ze'].real) or np.any(sh['areas']<=0):raise ValueError('changed resistance or areas')
    full=[];mats=[]
    for d in (coarse,ref):
        vals=[];mm=[]
        for i,f in enumerate(FREQ):
            x=tuple(v[i] for v in (d['Zu'],d['Pu'],sh['Zl'],sh['Pl'],ex['Ze'],sh['Pe']))
            y,_=replay_full(*x,d['Y'][i],d['flow'][i],4)
            vals.append(y);mm.append(x)
        full.append(vals);mats.append(mm)
    bases,spectra=snapshot_bases([v[-1] for v in full[0]],[55]*7,sh['areas'],rank)
    Tu=block_diag(*bases[:6]);Tl=bases[-1]
    modes=sum(b.shape[1] for b in bases)
    reduced=[];diagnostics=[]
    for mm,ff in zip(mats,full):
        vals=[];rows=[]
        for f,x,y in zip(FREQ,mm,ff):
            z,r=modal_replay(x,Tu,Tl,4,[55]*7,sh['areas'],y)
            vals.append(z);rows.append(dict(frequencyHz=f,flow=r['flow'],pressureDefect=r['pressureDefect']))
        reduced.append(vals);diagnostics.append(rows)
    c,f=full;cr,fr=reduced
    pairs=dict(coarseModal=(cr,c),fineModal=(fr,f),fullSpatial=(c,f),reducedSpatial=(cr,fr),combined=(cr,f))
    comparisons={k:compare_spatial(FREQ,*v,[55]*7,sh['areas']) for k,v in pairs.items()}
    gate=all(v['gate'] for v in comparisons.values())
    a.out.mkdir(parents=True,exist_ok=True)
    archive=save_matrices(a.out,'fixed_snapshot_basis',frequencies=FREQ,Tu=Tu,Tl=Tl,areas=sh['areas'])
    summary=dict(gate=gate,angleDeg=a.angle,diagnosticOnly=True,rank=rank,modes=modes,referenceModes=385,
        trainingMesh=[40,160,24],validationMesh=[50,200,32],fixedBasis=True,trainedOnFine=False,
        independentUpperMeshValidated=gate,continuousFrequencyValidated=False,timeDomainReady=False,
        modalConvergenceCertified=False,radiationReady=False,maximum={k:v['maximum'] for k,v in comparisons.items()})
    (a.out/'fixed_snapshot_transfer.json').write_text(json.dumps(dict(summary=summary,comparisons=comparisons,
        diagnostics=diagnostics,singularValues=spectra,archive=archive,scaleSha256=sha,frequenciesHz=FREQ,
        selectionManifestSha256=hashlib.sha256((a.snapshot/'snapshot_reduction.json').read_bytes()).hexdigest()),indent=2,allow_nan=False))
    print('G3_FIXED_SNAPSHOT_GATE '+json.dumps(summary),flush=True)
    if not gate:raise ValueError('fixed snapshot basis failed refined-mesh transfer')
if __name__=='__main__':main()
