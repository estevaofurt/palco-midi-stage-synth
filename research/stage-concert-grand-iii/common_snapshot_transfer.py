"""Independent fine-mesh transfer of a frozen common snapshot allocation."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from acoustic_matrix_archive import read_npz,replay_full,modal_replay
from graded_reference_audit import require_graded
from high_modal_allocation import require_archive
from dual_cavity_spatial_diagnostic import FREQ,compare_spatial,save_matrices
from fixed_355_validation import require_fine,valid_metrics
from snapshot_reduction import snapshot_bases
from snapshot_allocation import common_report

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','archive','consolidated','graded','fine','angle30','angle55','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    sha=hashlib.sha256(a.scale.read_bytes()).hexdigest()
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    gd=json.loads((a.graded/'graded_cavity_replay.json').read_text());require_graded(gd,a.angle,sha)
    fine=json.loads((a.fine/'graded_combined_refinement.json').read_text());require_fine(fine,a.angle,sha)
    common=common_report(json.loads(a.angle30.read_text()),json.loads(a.angle55.read_text()),sha)
    selected=common['summary']['commonSelection']
    if selected is None:raise ValueError('no common approved allocation')
    cfg=selected['counts']
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
    bases,spectra=snapshot_bases([v[-1] for v in full[0]],[55]*7,sh['areas'],24)
    if any(b.shape[1]<n for b,n in zip(bases,cfg)):raise ValueError('rank deficiency')
    bases=[b[:,:n] for b,n in zip(bases,cfg)]
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
    archive=save_matrices(a.out,'common_snapshot_basis',frequencies=FREQ,Tu=Tu,Tl=Tl,areas=sh['areas'])
    summary=dict(gate=gate,angleDeg=a.angle,diagnosticOnly=True,rankDistribution=cfg,modes=modes,referenceModes=385,
        trainingMesh=[40,160,24],validationMesh=[50,200,32],fixedBasis=True,trainedOnFine=False,
        independentUpperMeshValidated=gate,continuousFrequencyValidated=False,timeDomainReady=False,
        modalConvergenceCertified=False,radiationReady=False,maximum={k:v['maximum'] for k,v in comparisons.items()})
    (a.out/'common_snapshot_transfer.json').write_text(json.dumps(dict(summary=summary,comparisons=comparisons,
        diagnostics=diagnostics,singularValues=spectra,archive=archive,scaleSha256=sha,frequenciesHz=FREQ,
        selection=selected,sourceManifestSha256=[hashlib.sha256(x.read_bytes()).hexdigest() for x in (a.angle30,a.angle55)]),indent=2,allow_nan=False))
    print('G3_COMMON_SNAPSHOT_TRANSFER_GATE '+json.dumps(summary),flush=True)
    if not gate:raise ValueError('fixed snapshot basis failed refined-mesh transfer')
if __name__=='__main__':main()
