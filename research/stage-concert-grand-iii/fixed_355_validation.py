"""G3.10j: hold the retrospectively selected 355 modes fixed on a new mesh.
Replay archived operators; no new FEM or physical tuning."""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from acoustic_matrix_archive import read_npz,replay_full,modal_replay
from graded_reference_audit import require_graded
from high_modal_allocation import require_archive
from dual_cavity_spatial_diagnostic import FREQ,compare_spatial

COUNTS=(55,55,55,45,45,55,45)
METRICS={'impedance','upperPressure','lowerPressure','exteriorPressure','flow','physicalVelocityRelative'}

def valid_metrics(m):
    return set(m)==METRICS and all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and 0<=v<=.05 for v in m.values())

def require_common(d,sha):
    s=d.get('summary',{});c=s.get('commonSelection',{})
    expected=dict(gate=True,diagnosticOnly=True,angles=[30,55],retrospectiveSelection=True,modalConvergenceCertified=False,radiationReady=False)
    if d.get('scaleSha256')!=sha or d.get('frequenciesHz')!=FREQ or any(s.get(k)!=v for k,v in expected.items()) or tuple(c.get('counts',()))!=COUNTS or c.get('totalModes')!=355 or c.get('gate') is not True or not valid_metrics(c.get('maximum',{})):
        raise ValueError('invalid fixed selection evidence')

def require_fine(d,angle,sha):
    s=d.get('summary',{})
    expected=dict(gate=True,angleDeg=angle,diagnosticOnly=True,upperConfig=[50,200,32],baselineConfig=[40,160,24],modes=385,lowerFixed=True,exteriorFixed=True,modalConvergenceCertified=False,fullCabinetReady=False,radiationReady=False)
    rows=d.get('cases',[])
    if d.get('scaleSha256')!=sha or d.get('frequenciesHz')!=FREQ or any(s.get(k)!=v for k,v in expected.items()) or [r.get('frequencyHz') for r in rows]!=FREQ or any(r.get('upper',{}).get('gate') is not True or r.get('coupled',{}).get('gate') is not True for r in rows) or d.get('geometry',{}).get('gate') is not True or not .95<=s.get('minimumCapture',0)<=1.0000001:
        raise ValueError('invalid combined archive')
    if s.get('combinedUpperRefinementGate') is not True or not valid_metrics(s.get('comparison',{})):
        raise ValueError('combined spatial criterion failed')

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','archive','consolidated','graded','fine','common','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    sha=hashlib.sha256(a.scale.read_bytes()).hexdigest()
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    gd=json.loads((a.graded/'graded_cavity_replay.json').read_text());require_graded(gd,a.angle,sha)
    fine=json.loads((a.fine/'graded_combined_refinement.json').read_text());require_fine(fine,a.angle,sha)
    require_common(json.loads(a.common.read_text()),sha)
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
    T=[np.eye(55)[:,:n] for n in COUNTS];Tu=block_diag(*T[:6]);Tl=T[-1]
    outputs=[];diagnostics=[]
    for d in (coarse,ref):
        full=[];reduced=[];rows=[]
        for i,f in enumerate(FREQ):
            x=tuple(v[i] for v in (d['Zu'],d['Pu'],sh['Zl'],sh['Pl'],ex['Ze'],sh['Pe']))
            y,_=replay_full(*x,d['Y'][i],d['flow'][i],4)
            v,r=modal_replay(x,Tu,Tl,4,[55]*7,sh['areas'],y)
            full.append(y);reduced.append(v);rows.append(dict(frequencyHz=f,omitted=r['flow']['omittedRelative'],resolved=r['flow']['resolvedRelative']))
        outputs.append((full,reduced));diagnostics.append(rows)
    (c385,c355),(f385,f355)=outputs
    pairs=dict(coarseModal=(c355,c385),fineModal=(f355,f385),fullSpatial=(c385,f385),reducedSpatial=(c355,f355),combined=(c355,f385))
    comparisons={k:compare_spatial(FREQ,*v,[55]*7,sh['areas']) for k,v in pairs.items()}
    gate=all(v['gate'] for v in comparisons.values())
    summary=dict(gate=gate,angleDeg=a.angle,diagnosticOnly=True,counts=list(COUNTS),modes=355,referenceModes=385,
        fixedSelection=True,independentSpatialValidation=True,modalConvergenceCertified=False,fullCabinetReady=False,radiationReady=False,
        maximum={k:v['maximum'] for k,v in comparisons.items()})
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'fixed_355_validation.json').write_text(json.dumps(dict(summary=summary,comparisons=comparisons,diagnostics=diagnostics,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_FIXED_355_GATE '+json.dumps(summary),flush=True)
    if not gate:raise ValueError('fixed selection did not transfer to refined mesh')
if __name__=='__main__':main()
